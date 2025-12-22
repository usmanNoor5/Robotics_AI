#!/usr/bin/env python3
"""
CIFAR-10 GAN (TensorFlow 2.x, DCGAN-style)
-------------------------------------------
Covers Part A – GAN Guidelines:
1) Build generator & discriminator from scratch (see `build_generator`, `build_discriminator`).
2) Training stability & progressive improvement: Hinge loss, Spectral Norm (D), R1 regularization,
   TTUR (lrD > lrG), EMA of G, light augmentation.
3) Logs losses and saves fixed‑seed sample grids every epoch (TensorBoard + PNG).
4) >2 improvements beyond baseline: SpectralNorm(D), Hinge loss, TTUR, R1, EMA, light aug.

Usage
-----
python CIFAR10_GAN_TF.py \
  --epochs 100 --batch_size 128 --z_dim 128 \
  --g_lr 1e-4 --d_lr 2e-4 --log_interval 100 --gpu 0

TensorBoard:  tensorboard --logdir runs
Samples:      ./outputs/samples/epoch_XXX_[g|g_ema].png
Checkpoints:  ./outputs/checkpoints/
"""

import os
import math
import argparse
from pathlib import Path
from datetime import datetime

import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers

# -----------------------------------------------------
# Utilities
# -----------------------------------------------------

def seed_everything(seed: int = 42):
    tf.random.set_seed(seed)
    np.random.seed(seed)


def make_grid(images, nrow=None):
    """Make an (H*nrows, W*ncols, C) grid from a NCHW or NHWC batch in [-1,1]."""
    if images.ndim == 4 and images.shape[-1] in (1, 3):
        # NHWC
        imgs = images
    elif images.ndim == 4 and images.shape[1] in (1, 3):
        # NCHW -> NHWC
        imgs = np.transpose(images, (0, 2, 3, 1))
    else:
        raise ValueError("images must be NCHW or NHWC")

    imgs = (imgs + 1.0) * 0.5  # [-1,1] -> [0,1]
    imgs = np.clip(imgs, 0.0, 1.0)

    N, H, W, C = imgs.shape
    if nrow is None:
        nrow = int(math.sqrt(N))
    ncol = int(math.ceil(N / nrow))

    grid = np.ones((H * ncol, W * nrow, C), dtype=np.float32)
    idx = 0
    for y in range(ncol):
        for x in range(nrow):
            if idx >= N:
                break
            grid[y * H:(y + 1) * H, x * W:(x + 1) * W, :] = imgs[idx]
            idx += 1
    return (grid * 255.0).astype(np.uint8)


def save_image(path, array_uint8):
    from PIL import Image
    Image.fromarray(array_uint8).save(path)


# -----------------------------------------------------
# Spectral Normalization wrapper (for Conv/Dense kernels)
# -----------------------------------------------------
class SpectralNorm(layers.Wrapper):
    """Spectral Normalization for Conv2D/Dense (TF2/Keras).
    Normalizes the underlying kernel via power iteration and **assigns** the
    normalized weights before the wrapped layer's forward pass.
    """
    def __init__(self, layer, power_iterations=1, **kwargs):
        if not isinstance(layer, (layers.Conv2D, layers.Dense)):
            raise ValueError("SpectralNorm supports Conv2D/Dense layers only.")
        super().__init__(layer, **kwargs)
        self.power_iterations = power_iterations

    def build(self, input_shape):
        super().build(input_shape)
        self.w = self.layer.kernel  # tf.Variable
        w_shape = self.w.shape
        # u vector for power iteration (1 x out_channels)
        self.u = self.add_weight(
            shape=(1, w_shape[-1]),
            initializer=tf.random_normal_initializer(),
            trainable=False,
            name="sn_u",
            dtype=self.w.dtype,
        )

    def compute_output_shape(self, input_shape):
        return self.layer.compute_output_shape(input_shape)

    def call(self, inputs, training=None):
        # Flatten to 2D: [N, out_features]
        w = tf.reshape(self.w, [-1, self.w.shape[-1]])
        u = self.u
        # Power iteration
        for _ in range(self.power_iterations):
            v = tf.linalg.l2_normalize(tf.matmul(u, tf.transpose(w)))
            u = tf.linalg.l2_normalize(tf.matmul(v, w))
        sigma = tf.matmul(tf.matmul(v, w), tf.transpose(u))  # 1x1
        w_bar = tf.reshape(self.w / sigma, self.w.shape)
        # IMPORTANT: assign, don't rebind the property
        self.w.assign(w_bar)
        self.u.assign(u)
        return self.layer(inputs, training=training)

    def build(self, input_shape):
        super().build(input_shape)
        self.w = self.layer.kernel  # reference to underlying kernel
        self.w_shape = self.w.shape
        # Create u vector for power iteration
        self.u = self.add_weight(
            shape=(1, self.w_shape[-1]),
            initializer=tf.random_normal_initializer(),
            trainable=False,
            name='sn_u')

    def call(self, inputs, training=None):
        w_reshaped = tf.reshape(self.w, [-1, self.w_shape[-1]])
        u = self.u
        for _ in range(self.power_iterations):
            v = tf.nn.l2_normalize(tf.matmul(u, tf.transpose(w_reshaped)))
            u = tf.nn.l2_normalize(tf.matmul(v, w_reshaped))
        sigma = tf.matmul(tf.matmul(v, w_reshaped), tf.transpose(u))
        w_bar = self.w / sigma
        self.layer.kernel = w_bar
        self.u.assign(u)
        return self.layer(inputs, training=training)


# -----------------------------------------------------
# Models (DCGAN-size for 32x32 CIFAR-10)
# -----------------------------------------------------

def build_generator(z_dim=128, base_ch=256):
    z = layers.Input(shape=(z_dim,))
    x = layers.Dense(4 * 4 * base_ch * 4, use_bias=False)(z)
    x = layers.Reshape((4, 4, base_ch * 4))(x)
    x = layers.BatchNormalization()(x)
    x = layers.ReLU()(x)

    # 4x4 -> 8x8
    x = layers.Conv2DTranspose(base_ch * 2, kernel_size=4, strides=2, padding='same', use_bias=False)(x)
    x = layers.BatchNormalization()(x)
    x = layers.ReLU()(x)

    # 8x8 -> 16x16
    x = layers.Conv2DTranspose(base_ch, kernel_size=4, strides=2, padding='same', use_bias=False)(x)
    x = layers.BatchNormalization()(x)
    x = layers.ReLU()(x)

    # 16x16 -> 32x32
    x = layers.Conv2DTranspose(3, kernel_size=4, strides=2, padding='same', use_bias=False)(x)
    x = layers.Activation('tanh')(x)

    return keras.Model(z, x, name='Generator')


def disc_block(x, out_ch, sn=True):
    conv = layers.Conv2D(out_ch, kernel_size=4, strides=2, padding='same', use_bias=False)
    if sn:
        x = SpectralNorm(conv)(x)
    else:
        x = conv(x)
    x = layers.LeakyReLU(0.2)(x)
    return x


def build_discriminator(base_ch=64, sn=True):
    inp = layers.Input(shape=(32, 32, 3))
    x = inp
    x = disc_block(x, base_ch, sn)
    x = disc_block(x, base_ch * 2, sn)
    x = disc_block(x, base_ch * 4, sn)
    # 4x4 -> 1x1 via conv
    conv_last = layers.Conv2D(1, kernel_size=4, strides=1, padding='valid', use_bias=False)
    x = SpectralNorm(conv_last)(x) if sn else conv_last(x)
    x = layers.Flatten()(x)
    return keras.Model(inp, x, name='Discriminator')


# -----------------------------------------------------
# Losses: Hinge + R1 regularization
# -----------------------------------------------------

def d_hinge(d_real, d_fake):
    loss_real = tf.reduce_mean(tf.nn.relu(1.0 - d_real))
    loss_fake = tf.reduce_mean(tf.nn.relu(1.0 + d_fake))
    return loss_real + loss_fake


def g_hinge(d_fake):
    return -tf.reduce_mean(d_fake)


def r1_penalty(d_out_real, real_images, gamma=10.0):
    grads = tf.gradients(tf.reduce_sum(d_out_real), real_images)[0]
    grads = tf.reshape(grads, [tf.shape(grads)[0], -1])
    penalty = 0.5 * gamma * tf.reduce_mean(tf.reduce_sum(tf.square(grads), axis=1))
    return penalty


# -----------------------------------------------------
# Dataset: CIFAR-10 with light augmentation
# -----------------------------------------------------

def preprocess_train(example):
    image = tf.cast(example['image'], tf.float32)
    # Random crop with padding=4 (reflect)
    image = tf.pad(image, [[4, 4], [4, 4], [0, 0]], mode='REFLECT')
    image = tf.image.random_crop(image, size=[32, 32, 3])
    image = tf.image.random_flip_left_right(image)
    # Light color jitter
    image = tf.image.random_brightness(image, max_delta=0.05)
    image = tf.image.random_contrast(image, lower=0.95, upper=1.05)
    image = tf.image.random_saturation(image, lower=0.95, upper=1.05)
    image = (image / 127.5) - 1.0  # [-1,1]
    return image


def load_cifar10(batch_size, shuffle=True, num_parallel_calls=tf.data.AUTOTUNE):
    (x_train, _), _ = keras.datasets.cifar10.load_data()
    ds = tf.data.Dataset.from_tensor_slices({'image': x_train})
    if shuffle:
        ds = ds.shuffle(50000, reshuffle_each_iteration=True)
    ds = ds.map(preprocess_train, num_parallel_calls=num_parallel_calls)
    ds = ds.batch(batch_size, drop_remainder=True)
    ds = ds.prefetch(tf.data.AUTOTUNE)
    return ds


# -----------------------------------------------------
# EMA helper
# -----------------------------------------------------
class EMA:
    def __init__(self, model, decay=0.999):
        self.decay = decay
        self.shadow = [w.numpy().copy() for w in model.weights]

    def update(self, model):
        for i, w in enumerate(model.weights):
            self.shadow[i] = self.decay * self.shadow[i] + (1.0 - self.decay) * w.numpy()

    def copy_to(self, model):
        for i, w in enumerate(model.weights):
            w.assign(self.shadow[i])


# -----------------------------------------------------
# Training Loop
# -----------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--epochs', type=int, default=100)
    parser.add_argument('--batch_size', type=int, default=128)
    parser.add_argument('--z_dim', type=int, default=128)
    parser.add_argument('--g_lr', type=float, default=1e-4)   # TTUR
    parser.add_argument('--d_lr', type=float, default=2e-4)
    parser.add_argument('--ema_decay', type=float, default=0.999)
    parser.add_argument('--r1_interval', type=int, default=16, help='Apply R1 every N D steps (0=off)')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--gpu', type=int, default=0)
    parser.add_argument('--out_dir', type=str, default='./outputs')
    parser.add_argument('--log_interval', type=int, default=100)
    args = parser.parse_args()

    # GPU select
    gpus = tf.config.list_physical_devices('GPU')
    if gpus:
        try:
            tf.config.set_visible_devices(gpus[args.gpu], 'GPU')
            tf.config.experimental.set_memory_growth(gpus[args.gpu], True)
        except Exception:
            pass

    seed_everything(args.seed)

    out_dir = Path(args.out_dir)
    ckpt_dir = out_dir / 'checkpoints'
    sample_dir = out_dir / 'samples'
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    sample_dir.mkdir(parents=True, exist_ok=True)

    # Data
    train_ds = load_cifar10(args.batch_size)

    # Models
    G = build_generator(z_dim=args.z_dim)
    D = build_discriminator()

    # EMA copy of G
    G_ema = build_generator(z_dim=args.z_dim)
    G_ema.set_weights(G.get_weights())
    ema = EMA(G, decay=args.ema_decay)

    # Optimizers (TTUR)
    g_opt = keras.optimizers.Adam(learning_rate=args.g_lr, beta_1=0.0, beta_2=0.9)
    d_opt = keras.optimizers.Adam(learning_rate=args.d_lr, beta_1=0.0, beta_2=0.9)

    # Fixed noise for progress grids
    rng = tf.random.Generator.from_seed(args.seed)
    fixed_noise = rng.normal(shape=(64, args.z_dim))
    np.save(out_dir / 'fixed_noise.npy', fixed_noise.numpy())

    # Logging
    run_name = f"cifar10_gan_tf_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    logdir = os.path.join('runs', run_name)
    writer = tf.summary.create_file_writer(logdir)

    # Checkpointing
    ckpt = tf.train.Checkpoint(G=G, D=D, g_opt=g_opt, d_opt=d_opt)
    manager = tf.train.CheckpointManager(ckpt, str(ckpt_dir), max_to_keep=5)

    global_step = 0

    @tf.function
    def d_train_step(real_images):
        bsz = tf.shape(real_images)[0]
        noise = tf.random.normal((bsz, args.z_dim))
        with tf.GradientTape(persistent=True) as tape:
            fake_images = G(noise, training=True)
            d_real = D(real_images, training=True)
            d_fake = D(fake_images, training=True)
            d_loss = d_hinge(d_real, d_fake)
            if tf.constant(args.r1_interval > 0) and tf.equal(global_step % args.r1_interval, 0):
                with tf.GradientTape() as r1_tape:
                    r1_tape.watch(real_images)
                    d_real_r1 = D(real_images, training=True)
                grads = r1_tape.gradient(tf.reduce_sum(d_real_r1), real_images)
                grads = tf.reshape(grads, [bsz, -1])
                r1 = 0.5 * 10.0 * tf.reduce_mean(tf.reduce_sum(tf.square(grads), axis=1))
                d_loss = d_loss + r1
            else:
                r1 = tf.constant(0.0)
        d_grads = tape.gradient(d_loss, D.trainable_variables)
        d_opt.apply_gradients(zip(d_grads, D.trainable_variables))
        return d_loss, r1

    @tf.function
    def g_train_step():
        noise = tf.random.normal((args.batch_size, args.z_dim))
        with tf.GradientTape() as tape:
            fake_images = G(noise, training=True)
            d_fake = D(fake_images, training=True)
            g_loss = g_hinge(d_fake)
        g_grads = tape.gradient(g_loss, G.trainable_variables)
        g_opt.apply_gradients(zip(g_grads, G.trainable_variables))
        return g_loss

    for epoch in range(1, args.epochs + 1):
        for real in train_ds:
            d_loss, r1_val = d_train_step(real)
            g_loss = g_train_step()

            # EMA update after G step
            ema.update(G)

            if global_step % args.log_interval == 0:
                with writer.as_default():
                    tf.summary.scalar('losses/d_loss', d_loss, step=global_step)
                    tf.summary.scalar('losses/g_loss', g_loss, step=global_step)
                    tf.summary.scalar('regularization/r1', r1_val, step=global_step)
            global_step += 1

        # End epoch: copy EMA to G_ema and save grids
        ema.copy_to(G_ema)
        # Grids (G & G_ema)
        g_samples = G(fixed_noise, training=False).numpy()
        g_grid = make_grid(g_samples, nrow=int(math.sqrt(fixed_noise.shape[0])))
        save_image(sample_dir / f'epoch_{epoch:03d}_g.png', g_grid)

        g_ema_samples = G_ema(fixed_noise, training=False).numpy()
        g_ema_grid = make_grid(g_ema_samples, nrow=int(math.sqrt(fixed_noise.shape[0])))
        save_image(sample_dir / f'epoch_{epoch:03d}_g_ema.png', g_ema_grid)

        # Checkpoint
        manager.save(checkpoint_number=epoch)
        print(f"[Epoch {epoch}] d_loss={float(d_loss):.4f} g_loss={float(g_loss):.4f} saved.")

    print("Training complete. View samples in ./outputs/samples and logs in TensorBoard.")


if __name__ == '__main__':
    main()
