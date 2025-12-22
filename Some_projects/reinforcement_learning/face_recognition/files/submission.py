import os
import random
import math
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np

# ----------------------------- User settings -----------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # folder where submission.py is
DATA_DIR = os.path.join(BASE_DIR, "dataset")
FACE_DIR = os.path.join(DATA_DIR, "face")
NONFACE_DIR = os.path.join(DATA_DIR, "nonface")

# DATA_DIR = "dataset"
# FACE_DIR = os.path.join(DATA_DIR, "face")
# NONFACE_DIR = os.path.join(DATA_DIR, "nonface")
IMAGE_SIZE =  512     # resize images to IMAGE_SIZE x IMAGE_SIZE (grayscale)
HIDDEN_UNITS = 128    # number of neurons in hidden layer
LEARNING_RATE = 0.01
EPOCHS = 100
BATCH_SIZE = 32
SEED = 42
MODEL_DIR = "model_weights"
VERBOSE = True
# -------------------------------------------------------------------------

np.random.seed(SEED)
random.seed(SEED)


# ----------------------------- Utilities ---------------------------------
def list_image_files(folder):
    exts = (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".gif")
    files = []
    print(folder)
    for root, dirs, filenames in os.walk(folder):
        print("ROOT:", root)
        print("DIRS:", dirs)
        print("FILES:", filenames)   # <--- IMPORTANT
        print("------------------------")

        for f in filenames:
            if f.lower().endswith(exts):
                files.append(os.path.join(root, f))

    return files

def load_and_preprocess_image(path, size=IMAGE_SIZE):
    # Load image, convert to grayscale, resize, convert to numpy float32 normalized [0,1]
    im = Image.open(path).convert("RGB")  
    im = im.resize((size, size), Image.BILINEAR)
    arr = np.asarray(im, dtype=np.float32) / 255.0
    arr = arr.reshape(-1)  # flatten
    return arr


def build_dataset(face_paths, nonface_paths, size=IMAGE_SIZE):
    X = []
    y = []
    print(face_paths)
    print('hello')
    for p in face_paths:
        try:
            X.append(load_and_preprocess_image(p, size))
            y.append(1)
        except Exception as e:
            print(f"Warning: failed to load {p}: {e}")
    for p in nonface_paths:
        try:
            X.append(load_and_preprocess_image(p, size))
            y.append(0)
        except Exception as e:
            print(f"Warning: failed to load {p}: {e}")
    X = np.stack(X, axis=0)
    y = np.array(y, dtype=np.float32).reshape(-1, 1)
    return X, y


def train_val_test_split(X, y, train_frac=0.6, val_frac=0.2, test_frac=0.2, seed=SEED):
    assert abs(train_frac + val_frac + test_frac - 1.0) < 1e-6
    n = X.shape[0]
    idx = np.arange(n)
    rng = np.random.RandomState(seed)
    rng.shuffle(idx)
    X = X[idx]
    y = y[idx]
    t = int(n * train_frac)
    v = int(n * (train_frac + val_frac))
    X_train, y_train = X[:t], y[:t]
    X_val, y_val = X[t:v], y[t:v]
    X_test, y_test = X[v:], y[v:]
    return X_train, y_train, X_val, y_val, X_test, y_test


class ShallowNN:
    def __init__(self, input_dim, hidden_units, lr=1e-2, seed=SEED):
        rng = np.random.RandomState(seed)
        # Xavier initialization
        self.w1 = rng.randn(input_dim, hidden_units) * np.sqrt(2.0 / (input_dim + hidden_units))
        self.b1 = np.zeros((1, hidden_units))
        self.w2 = rng.randn(hidden_units, 1) * np.sqrt(2.0 / (hidden_units + 1))
        self.b2 = np.zeros((1, 1))
        self.lr = lr

    @staticmethod
    def sigmoid(z):
        # numerically stable sigmoid
        z = np.clip(z, -500, 500)
        return 1.0 / (1.0 + np.exp(-z))

    @staticmethod
    def sigmoid_grad(a):
        return a * (1 - a)

    @staticmethod
    def relu(z):
        return np.maximum(0, z)

    @staticmethod
    def relu_grad(z):
        return (z > 0).astype(np.float32)

    @staticmethod
    def binary_cross_entropy(y_true, y_pred):
        # y_true and y_pred are column vectors shape (n,1)
        eps = 1e-12
        y_pred = np.clip(y_pred, eps, 1 - eps)
        loss = - (y_true * np.log(y_pred) + (1 - y_true) * np.log(1 - y_pred))
        return np.mean(loss)

    def forward(self, X):
        # X shape (batch, input_dim)
        z1 = X.dot(self.w1) + self.b1      # (batch, hidden)
        a1 = self.relu(z1)
        z2 = a1.dot(self.w2) + self.b2     # (batch, 1)
        a2 = self.sigmoid(z2)
        cache = (X, z1, a1, z2, a2)
        return a2, cache

    def backward(self, cache, y_true):
        X, z1, a1, z2, a2 = cache
        m = X.shape[0]
        # dL/da2 = -(y/a2) + (1-y)/(1-a2) -> simplified for BCE with sigmoid output is (a2 - y)
        dz2 = (a2 - y_true) / m  # (batch,1)
        dw2 = a1.T.dot(dz2)      # (hidden,1)
        db2 = np.sum(dz2, axis=0, keepdims=True)  # (1,1)

        da1 = dz2.dot(self.w2.T)  # (batch, hidden)
        dz1 = da1 * self.relu_grad(z1)
        dw1 = X.T.dot(dz1)        # (input, hidden)
        db1 = np.sum(dz1, axis=0, keepdims=True)  # (1, hidden)

        # Update parameters (SGD)
        self.w2 -= self.lr * dw2
        self.b2 -= self.lr * db2
        self.w1 -= self.lr * dw1
        self.b1 -= self.lr * db1

    def predict_proba(self, X):
        a2, _ = self.forward(X)
        return a2

    def predict(self, X, thresh=0.5):
        return (self.predict_proba(X) >= thresh).astype(np.int32)

    def save(self, folder=MODEL_DIR):
        os.makedirs(folder, exist_ok=True)
        np.save(os.path.join(folder, "w1.npy"), self.w1)
        np.save(os.path.join(folder, "b1.npy"), self.b1)
        np.save(os.path.join(folder, "w2.npy"), self.w2)
        np.save(os.path.join(folder, "b2.npy"), self.b2)
        


    def load(self, folder=MODEL_DIR):
        self.w1 = np.load(os.path.join(folder, "w1.npy"))
        self.b1 = np.load(os.path.join(folder, "b1.npy"))
        self.w2 = np.load(os.path.join(folder, "w2.npy"))
        self.b2 = np.load(os.path.join(folder, "b2.npy"))


# ----------------------------- Training loop -----------------------------
def iterate_minibatches(X, y, batch_size=BATCH_SIZE, shuffle=True):
    n = X.shape[0]
    idx = np.arange(n)
    if shuffle:
        np.random.shuffle(idx)
    for i in range(0, n, batch_size):
        batch_idx = idx[i:i + batch_size]
        yield X[batch_idx], y[batch_idx]


def evaluate(model, X, y):
    preds = model.predict_proba(X)
    loss = ShallowNN.binary_cross_entropy(y, preds)
    pred_labels = (preds >= 0.5).astype(np.int32)
    acc = np.mean(pred_labels == y.astype(np.int32))
    return loss, acc


# def train_model(X_train, y_train, X_val, y_val, input_dim, hidden_units,
#                 epochs=EPOCHS, batch_size=BATCH_SIZE, lr=LEARNING_RATE):
#     model = ShallowNN(input_dim, hidden_units, lr=lr)
#     best_val_loss = float("inf")
#     best_weights = None

#     for epoch in range(1, epochs + 1):
#         # Training
#         train_loss_accum = 0.0
#         n_batches = 0
#         for Xb, yb in iterate_minibatches(X_train, y_train, batch_size, shuffle=True):
#             outputs, cache = model.forward(Xb)
#             loss = ShallowNN.binary_cross_entropy(yb, outputs)
#             model.backward(cache, yb)
#             train_loss_accum += loss
#             n_batches += 1
#         train_loss = train_loss_accum / max(1, n_batches)

#         # Validation
#         val_loss, val_acc = evaluate(model, X_val, y_val)

#         if VERBOSE:
#             print(f"Epoch {epoch:03d}/{epochs} | train_loss: {train_loss:.4f} | val_loss: {val_loss:.4f} | val_acc: {val_acc:.4f}")

#         # Save best model by val loss
#         if val_loss < best_val_loss:
#             best_val_loss = val_loss
#             best_weights = {
#                 "w1": model.w1.copy(), "b1": model.b1.copy(),
#                 "w2": model.w2.copy(), "b2": model.b2.copy()
#             }

#     # restore best weights
#     if best_weights is not None:
#         model.w1 = best_weights["w1"]
#         model.b1 = best_weights["b1"]
#         model.w2 = best_weights["w2"]
#         model.b2 = best_weights["b2"]

#     return model

def train_model(X_train, y_train, X_val, y_val, input_dim, hidden_units,
                epochs=EPOCHS, batch_size=BATCH_SIZE, lr=LEARNING_RATE):

    model = ShallowNN(input_dim, hidden_units, lr=lr)
    best_val_loss = float("inf")
    best_weights = None

    train_losses = []
    val_losses = []
    val_accuracies = []

    # ---- ENABLE INTERACTIVE PLOTTING ----
    plt.ion()
    fig, axs = plt.subplots(3, 1, figsize=(8, 10))

    for epoch in range(1, epochs + 1):

        # -------- TRAINING --------
        train_loss_accum = 0.0
        n_batches = 0

        for Xb, yb in iterate_minibatches(X_train, y_train, batch_size, shuffle=True):
            outputs, cache = model.forward(Xb)
            loss = ShallowNN.binary_cross_entropy(yb, outputs)
            model.backward(cache, yb)
            train_loss_accum += loss
            n_batches += 1

        train_loss = train_loss_accum / max(1, n_batches)
        train_losses.append(train_loss)

        # -------- VALIDATION --------
        val_loss, val_acc = evaluate(model, X_val, y_val)
        val_losses.append(val_loss)
        val_accuracies.append(val_acc)

        if VERBOSE:
            print(f"Epoch {epoch:03d}/{epochs} | train_loss: {train_loss:.4f} | val_loss: {val_loss:.4f} | val_acc: {val_acc:.4f}")

        # -------- SAVE BEST MODEL --------
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_weights = {
                "w1": model.w1.copy(), "b1": model.b1.copy(),
                "w2": model.w2.copy(), "b2": model.b2.copy()
            }

        # --------- REAL-TIME PLOTTING ---------
        axs[0].cla()
        axs[1].cla()
        axs[2].cla()

        axs[0].plot(train_losses)
        axs[0].set_title("Training Loss")
        axs[0].set_xlabel("Epoch")
        axs[0].set_ylabel("Loss")

        axs[1].plot(val_losses)
        axs[1].set_title("Validation Loss")
        axs[1].set_xlabel("Epoch")
        axs[1].set_ylabel("Loss")

        axs[2].plot(val_accuracies)
        axs[2].set_title("Validation Accuracy")
        axs[2].set_xlabel("Epoch")
        axs[2].set_ylabel("Accuracy")

        plt.pause(0.01)

    plt.ioff()
    plt.show()

    # -------- RESTORE BEST MODEL --------
    if best_weights is not None:
        model.w1 = best_weights["w1"]
        model.b1 = best_weights["b1"]
        model.w2 = best_weights["w2"]
        model.b2 = best_weights["b2"]

    return model



# ----------------------------- Main --------------------------------------
def main():
    # 1) Collect image paths
    face_paths = list_image_files(FACE_DIR)
    nonface_paths = list_image_files(NONFACE_DIR)
    print(f"Found {len(face_paths)} face images and {len(nonface_paths)} nonface images.")

    if len(face_paths) + len(nonface_paths) < 20:
        print("Warning: dataset is small. For a useful model, use many more images and diverse examples.")

    # Balance classes (optional): keep as is — but we shuffle later
    # 2) Build dataset arrays
    X, y = build_dataset(face_paths, nonface_paths, size=IMAGE_SIZE)
    print("Dataset shapes:", X.shape, y.shape)

    # 3) Split 60% train, 20% val, 20% test
    X_train, y_train, X_val, y_val, X_test, y_test = train_val_test_split(X, y, 0.6, 0.2, 0.2, seed=SEED)
    print("Split sizes -> train:", X_train.shape[0], "val:", X_val.shape[0], "test:", X_test.shape[0])

    # 4) Normalize inputs: already in [0,1]; optionally mean-center
    
    mean = np.mean(X_train, axis=0, keepdims=True)
    X_train = X_train - mean
    X_val = X_val - mean
    X_test = X_test - mean

    input_dim = X_train.shape[1]
    print("Input dim:", input_dim)

    # 5) Train
    model = train_model(X_train, y_train, X_val, y_val,
                        input_dim=input_dim,
                        hidden_units=HIDDEN_UNITS,
                        epochs=EPOCHS,
                        batch_size=BATCH_SIZE,
                        lr=LEARNING_RATE)

    # 6) Evaluate on test set
    test_loss, test_acc = evaluate(model, X_test, y_test)
    print(f"Test loss: {test_loss:.4f} | Test accuracy: {test_acc:.4f}")
    np.save("model_weights/input_mean.npy", mean)

    # 7) Save model
    model.save(MODEL_DIR)
    print(f"Saved model weights to '{MODEL_DIR}/'")

    # 8) Example: predict on a single image (first test image if exists)
    if X_test.shape[0] > 0:
        proba = model.predict_proba(X_test[:5])
        print("Example test probabilities (first 5):", proba.ravel())
        print("Example test labels (first 5):", y_test[:5].ravel())


if __name__ == "__main__":
    main()
