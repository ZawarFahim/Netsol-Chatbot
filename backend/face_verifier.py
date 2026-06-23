"""
face_verifier.py
----------------
Lightweight face verification using SFace (OpenCV Zoo) ONNX model and Haar Cascades.
Detects and crops the face from the webcam snapshot to eliminate background matching.
Uses `onnxruntime` and `opencv-python-headless`.
"""

import os
import io
import cv2
import numpy as np
import onnxruntime as ort
from PIL import Image

MODEL_PATH = os.path.join(os.path.dirname(__file__), "sface.onnx")

# We use a stricter threshold of 0.45 to prevent false matches (OpenCV default is 0.363)
SIMILARITY_THRESHOLD = 0.45

session = None


def get_session():
    global session
    if session is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError("SFace ONNX model not found.")
        session = ort.InferenceSession(MODEL_PATH, providers=["CPUExecutionProvider"])
    return session


def crop_face(image_bytes: bytes) -> Image.Image:
    """Detect and crop the face region from raw image bytes. Raises ValueError if no face is found."""
    # Convert bytes to numpy array for OpenCV
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image.")

    # Convert to grayscale for Haar classifier
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Load default OpenCV face detector
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    if len(faces) == 0:
        raise ValueError("No face detected. Please look directly at the camera and try again.")

    # Get the largest face
    faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
    x, y, w, h = faces[0]

    # Crop to face bounding box
    cropped_bgr = img[y:y+h, x:x+w]

    # Convert BGR back to RGB Pillow image
    cropped_rgb = cv2.cvtColor(cropped_bgr, cv2.COLOR_BGR2RGB)
    return Image.fromarray(cropped_rgb)


def get_face_embedding(image_bytes: bytes) -> np.ndarray:
    """Crop face, resize, preprocess, and run SFace model to get a normalized 128D embedding."""
    sess = get_session()

    # 1. Crop face first (raises ValueError if no face is found)
    img = crop_face(image_bytes)

    # 2. Resize to SFace input shape (112, 112)
    img = img.resize((112, 112))

    # 3. Convert to float32 numpy array
    img_data = np.array(img).astype(np.float32)

    # SFace model expects BGR input (OpenCV style)
    img_data = img_data[:, :, ::-1]

    # Convert shape from (112, 112, 3) to (3, 112, 112)
    img_data = np.transpose(img_data, (2, 0, 1))

    # Add batch dimension -> (1, 3, 112, 112)
    img_data = np.expand_dims(img_data, axis=0)

    # 4. Run SFace model
    inputs = {sess.get_inputs()[0].name: img_data}
    outputs = sess.run(None, inputs)
    embedding = outputs[0][0]

    # L2 normalize the embedding vector
    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding = embedding / norm

    return embedding


def verify_faces(registered_bytes: bytes, login_bytes: bytes) -> bool:
    """Compare two face images. Returns True if similarity is above threshold."""
    try:
        emb1 = get_face_embedding(registered_bytes)
        emb2 = get_face_embedding(login_bytes)

        similarity = float(np.dot(emb1, emb2))
        print(f"Face comparison similarity: {similarity:.4f} (Threshold: {SIMILARITY_THRESHOLD})")
        return similarity >= SIMILARITY_THRESHOLD
    except Exception as e:
        print(f"Face verification exception: {e}")
        return False
