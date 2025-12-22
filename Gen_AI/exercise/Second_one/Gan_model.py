#!/usr/bin/env python3
"""
CIFAR-10 GAN Trainer (PyTorch)
--------------------------------
Part A – GAN Guidelines covered:
1) Build generator & discriminator from scratch (see classes: Generator, Discriminator).
2) Training stability & progressive visual improvement (hinge loss + spectral norm on D, R1
   regularization, TTUR, EMA of G, light data augmentation).
3) Log losses & save fixed‑seed sample grids throughout training (TensorBoard + PNG grids
   in ./samples; fixed_noise saved for reproducibility).
4) At least two improvements beyond baseline, with rationale:
   • Spectral Normalization on D: controls Lipschitz constant; prevents exploding gradients.
   • Hinge loss: stronger gradients than BCE when D saturates; widely used in SNGAN/BigGAN.
   • TTUR (two time‑scale update rule): larger lr for D than G to balance convergence.
   • R1 gradient penalty (on real): discourages sharp D; reduces overfitting / increases stability.
   • EMA of G: maintains a smoothed copy of generator weights for better sample quality.
   • Light augmentation: random flip/crop/color‑jitter to make D robust without harming G.

Usage:
  python CIFAR10_GAN_Trainer.py \
    --data_root ./data --epochs 100 --batch_size 128 --z_dim 128 \
    --g_lr 1e-4 --d_lr 2e-4 --num_workers 4 --gpu 0

After (re)start, check:
  • ./checkpoints for weights (latest + best FID-ready placeholders) 
  • ./samples for fixed‑seed grids per epoch (both G and G_ema)
  • TensorBoard logs:  tensorboard --logdir runs

Notes:
  • Images are normalized to [-1,1].
  • Model architectures are DCGAN‑style (ResNet‑light would also work) sized for 32×32.
  • By default uses hinge loss + SN + R1 (every r1_interval steps).
"""

import os
import math
import argparse
from pathlib import Path
from datetime import datetime

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.nn.utils import spectral_norm as SN
from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter

import torchvision
from torchvision import datasets, transforms
from torchvision.utils import save_image, make_grid

# ---------------------
# Utils
# ---------------------

def seed_everything(seed: int = 42):
    import random
    import numpy as np
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def weights_init_ortho(m):
    if isinstance(m, (nn.Conv2d, nn.ConvTranspose2d, nn.Linear)):
        nn.init.orthogonal_(m.weight)
        if m.bias is not None:
            nn.init.zeros_(m.bias)


class EMA:
    def __init__(self, model, decay=0.999):
        self.decay = decay
        self.shadow = {}
        for name, param in model.named_parameters():
            if param.requires_grad:
                self.shadow[name] = param.data.clone()

    @torch.no_grad()
    def update(self, model):
        for name, param in model.named_parameters():
            if not param.requires_grad:
                continue
            assert name in self.shadow
            new_average = (1.0 - self.decay) * param.data + self.decay * self.shadow[name]
            self.shadow[name] = new_average.clone()

    @torch.no_grad()
    def copy_to(self, model):
        for name, param in model.named_parameters():
            if name in self.shadow:
                param.data.copy_(self.shadow[name])


# ---------------------
# Architecture (DCGAN-like, tuned for CIFAR-10 32x32x3)
# ---------------------

class GenBlock(nn.Module):
    def __init__(self, in_ch, out_ch):
        super().__init__()
        self.block = nn.Sequential(
            nn.ConvTranspose2d(in_ch, out_ch, 4, 2, 1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )
    def forward(self, x):
        return self.block(x)


class Generator(nn.Module):
    def __init__(self, z_dim=128, img_channels=3, base_ch=256):
        super().__init__()
        self.net = nn.Sequential(
            # z -> (base_ch*4) x 4x4
            nn.ConvTranspose2d(z_dim, base_ch*4, 4, 1, 0, bias=False),
            nn.BatchNorm2d(base_ch*4),
            nn.ReLU(inplace=True),
            # 4x4 -> 8x8
            GenBlock(base_ch*4, base_ch*2),
            # 8x8 -> 16x16
            GenBlock(base_ch*2, base_ch),
            # 16x16 -> 32x32
            nn.ConvTranspose2d(base_ch, img_channels, 4, 2, 1, bias=False),
            nn.Tanh(),
        )

    def forward(self, z):
        return self.net(z)


class DiscBlock(nn.Module):
    def __init__(self, in_ch, out_ch):
        super().__init__()
        self.block = nn.Sequential(
            SN(nn.Conv2d(in_ch, out_ch, 4, 2, 1, bias=False)),
            nn.LeakyReLU(0.2, inplace=True),
        )
    def forward(self, x):
        return self.block(x)


class Discriminator(nn.Module):
    def __init__(self, img_channels=3, base_ch=64):
        super().__init__()
        self.net = nn.Sequential(
            # 32x32 -> 16x16
            SN(nn.Conv2d(img_channels, base_ch, 4, 2, 1, bias=False)),
            nn.LeakyReLU(0.2, inplace=True),
            # 16x16 -> 8x8
            DiscBlock(base_ch, base_ch*2),
            # 8x8 -> 4x4
            DiscBlock(base_ch*2, base_ch*4),
        )
        self.out = SN(nn.Conv2d(base_ch*4, 1, 4, 1, 0, bias=False))  # 4x4 -> 1x1

    def forward(self, x):
        h = self.net(x)
        return self.out(h).view(-1)


# ---------------------
# Losses: Hinge + optional R1 regularization
# ---------------------

def d_hinge_loss(d_real, d_fake):
    loss_real = F.relu(1.0 - d_real).mean()
    loss_fake = F.relu(1.0 + d_fake).mean()
    return loss_real + loss_fake


def g_hinge_loss(d_fake):
    return (-d_fake).mean()


def r1_gradient_penalty(d_out_real, real_images):
    # R1: 0.5 * gamma * ||∇_x D(x)||^2 ; commonly gamma=10
    gamma = 10.0
    grads = torch.autograd.grad(
        outputs=d_out_real.sum(),
        inputs=real_images,
        create_graph=True,
        retain_graph=True,
        only_inputs=True,
    )[0]
    grads = grads.view(grads.size(0), -1)
    penalty = 0.5 * gamma * (grads.pow(2).sum(dim=1)).mean()
    return penalty


# ---------------------
# Training
# ---------------------

def save_fixed_grid(G, fixed_noise, epoch, out_dir, postfix="g"):
    G.eval()
    with torch.no_grad():
        samples = G(fixed_noise)
    grid = make_grid(samples, nrow=int(math.sqrt(fixed_noise.size(0))), normalize=True, value_range=(-1, 1))
    out_dir.mkdir(parents=True, exist_ok=True)
    save_image(grid, out_dir / f"epoch_{epoch:03d}_{postfix}.png")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data_root', type=str, default='./data')
    parser.add_argument('--epochs', type=int, default=100)
    parser.add_argument('--batch_size', type=int, default=128)
    parser.add_argument('--z_dim', type=int, default=128)
    parser.add_argument('--g_lr', type=float, default=1e-4)  # TTUR: smaller than D
    parser.add_argument('--d_lr', type=float, default=2e-4)
    parser.add_argument('--num_workers', type=int, default=4)
    parser.add_argument('--img_size', type=int, default=32)
    parser.add_argument('--r1_interval', type=int, default=16, help='apply R1 every N D steps (0=off)')
    parser.add_argument('--ema_decay', type=float, default=0.999)
    parser.add_argument('--out_dir', type=str, default='./outputs')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--gpu', type=int, default=0)
    parser.add_argument('--log_interval', type=int, default=100)
    parser.add_argument('--save_every', type=int, default=1)
    args = parser.parse_args()

    seed_everything(args.seed)

    device = torch.device(f'cuda:{args.gpu}' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")

    out_dir = Path(args.out_dir)
    ckpt_dir = out_dir / 'checkpoints'
    sample_dir = out_dir / 'samples'
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    sample_dir.mkdir(parents=True, exist_ok=True)

    # Data: CIFAR‑10 with light augmentation
    transform = transforms.Compose([
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomCrop(args.img_size, padding=4),
        transforms.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.1, hue=0.0),
        transforms.ToTensor(),
        transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),  # -> [-1,1]
    ])

    train_set = datasets.CIFAR10(root=args.data_root, train=True, download=True, transform=transform)
    loader = DataLoader(train_set, batch_size=args.batch_size, shuffle=True, num_workers=args.num_workers, pin_memory=True, drop_last=True)

    # Models
    G = Generator(z_dim=args.z_dim).to(device)
    D = Discriminator().to(device)

    G.apply(weights_init_ortho)
    D.apply(weights_init_ortho)

    # EMA of G
    G_ema = Generator(z_dim=args.z_dim).to(device)
    G_ema.load_state_dict(G.state_dict())
    ema_helper = EMA(G, decay=args.ema_decay)

    # Opts (TTUR) – BigGAN-style betas for hinge
    g_opt = torch.optim.Adam(G.parameters(), lr=args.g_lr, betas=(0.0, 0.9))
    d_opt = torch.optim.Adam(D.parameters(), lr=args.d_lr, betas=(0.0, 0.9))

    # Fixed noise for monitoring progress
    fixed_noise = torch.randn(64, args.z_dim, 1, 1, device=device)
    torch.save(fixed_noise, out_dir / 'fixed_noise.pt')

    # Logging
    run_name = f"cifar10_gan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    writer = SummaryWriter(log_dir=os.path.join('runs', run_name))

    global_step = 0

    for epoch in range(1, args.epochs + 1):
        G.train(); D.train()
        for i, (real, _) in enumerate(loader):
            real = real.to(device)
            bsz = real.size(0)

            # -----------------
            # 1) Update D
            # -----------------
            z = torch.randn(bsz, args.z_dim, 1, 1, device=device)
            with torch.no_grad():
                fake = G(z)

            real.requires_grad_(True)
            d_opt.zero_grad(set_to_none=True)
            d_real = D(real)
            d_fake = D(fake.detach())
            d_loss = d_hinge_loss(d_real, d_fake)

            # R1 penalty every N steps
            if args.r1_interval > 0 and (global_step % args.r1_interval == 0):
                r1 = r1_gradient_penalty(d_real, real)
                d_loss = d_loss + r1
                writer.add_scalar('regularization/r1', r1.item(), global_step)

            d_loss.backward()
            d_opt.step()

            # -----------------
            # 2) Update G
            # -----------------
            z = torch.randn(bsz, args.z_dim, 1, 1, device=device)
            g_opt.zero_grad(set_to_none=True)
            fake = G(z)
            d_fake_for_g = D(fake)
            g_loss = g_hinge_loss(d_fake_for_g)
            g_loss.backward()
            g_opt.step()

            # EMA update
            ema_helper.update(G)

            # Logs
            if global_step % args.log_interval == 0:
                writer.add_scalar('losses/d_loss', d_loss.item(), global_step)
                writer.add_scalar('losses/g_loss', g_loss.item(), global_step)

            global_step += 1

        # End epoch – save samples/checkpoints
        # Copy EMA weights to G_ema for evaluation visuals
        ema_helper.copy_to(G_ema)
        save_fixed_grid(G, fixed_noise, epoch, sample_dir, postfix='g')
        save_fixed_grid(G_ema, fixed_noise, epoch, sample_dir, postfix='g_ema')

        if epoch % args.save_every == 0:
            ckpt = {
                'G': G.state_dict(),
                'D': D.state_dict(),
                'G_ema_shadow': ema_helper.shadow,
                'g_opt': g_opt.state_dict(),
                'd_opt': d_opt.state_dict(),
                'epoch': epoch,
                'global_step': global_step,
                'args': vars(args),
            }
            torch.save(ckpt, ckpt_dir / f'ckpt_epoch_{epoch:03d}.pt')
            torch.save(ckpt, ckpt_dir / 'ckpt_latest.pt')
            print(f"[Epoch {epoch}] Saved checkpoint and samples.")

    writer.close()
    print("Training complete. View samples in ./outputs/samples and logs in TensorBoard.")


if __name__ == '__main__':
    main()
