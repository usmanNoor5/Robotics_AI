import numpy as np
from PIL import Image

IMAGE_SIZE = 512
MODEL_DIR = "model_weights"

# ---------------------------------------------------
# Load the trained model
# ---------------------------------------------------
class ShallowNN:
    def __init__(self):
        self.w1 = np.load(f"{MODEL_DIR}/w1.npy")
        self.b1 = np.load(f"{MODEL_DIR}/b1.npy")
        self.w2 = np.load(f"{MODEL_DIR}/w2.npy")
        self.b2 = np.load(f"{MODEL_DIR}/b2.npy")

    @staticmethod
    def relu(z):
        return np.maximum(0, z)

    @staticmethod
    def sigmoid(z):
        z = np.clip(z, -500, 500)
        return 1 / (1 + np.exp(-z))

    def predict_proba(self, X):
        a1 = self.relu(X @ self.w1 + self.b1)
        out = self.sigmoid(a1 @ self.w2 + self.b2)
        return out

    def predict(self, X):
        return (self.predict_proba(X) >= 0.5).astype(int)

# ---------------------------------------------------
# Preprocess function
# ---------------------------------------------------
def preprocess_image(path, mean):
    img = Image.open(path).convert("L")
    img = img.resize((IMAGE_SIZE, IMAGE_SIZE))
    arr = np.asarray(img, dtype=np.float32) / 255.0
    arr = arr.reshape(1, -1)
    arr = arr - mean      # <-- most important for correct prediction
    return arr

# ---------------------------------------------------
# Test on a single image
# ---------------------------------------------------
model = ShallowNN()

# test_image_path = "usman_img_1.jpg"   # <-- put your image here
test_image_path = "/home/usman/Documents/Robotics_AI/Some_projects/reinforcement_learning/face_recognition/dataset/face/usman_img_1.jpg"
mean = np.load("model_weights/input_mean.npy")

x = preprocess_image(test_image_path, mean)



proba = model.predict_proba(x)[0][0]
label = model.predict(x)[0][0]

print("Prediction probability (face):", proba)
print("Prediction label:", label)

if label == 1:
    print("🚀 This is YOUR FACE (detected).")
else:
    print("❌ Not your face.")
