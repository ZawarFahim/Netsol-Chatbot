import os
import cv2
import numpy as np
import onnxruntime as ort

MODEL_PATH = os.path.join(os.path.dirname(__file__), "sface.onnx")
SIMILARITY_THRESHOLD = 0.45
session = None

def get_session():
    global session
    if session is None:
        session = ort.InferenceSession(MODEL_PATH, providers=["CPUExecutionProvider"])
    return session

def crop_face(image_bytes: bytes) -> np.ndarray:
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Invalid image")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    if len(faces) == 0:
        raise ValueError("No face detected")

    faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
    x, y, w, h = faces[0]
    return img[y:y+h, x:x+w]

def get_face_embedding(image_bytes: bytes) -> np.ndarray:
    img = crop_face(image_bytes)
    img = cv2.resize(img, (112, 112))
    img_data = img.astype(np.float32)
    img_data = img_data[:, :, ::-1]
    img_data = np.transpose(img_data, (2, 0, 1))
    img_data = np.expand_dims(img_data, axis=0)

    outputs = get_session().run(None, {get_session().get_inputs()[0].name: img_data})
    embedding = outputs[0][0]

    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding = embedding / norm

    return embedding

def verify_faces(registered_bytes: bytes, login_bytes: bytes) -> bool:
    try:
        emb1 = get_face_embedding(registered_bytes)
        emb2 = get_face_embedding(login_bytes)
        return float(np.dot(emb1, emb2)) >= SIMILARITY_THRESHOLD
    except Exception:
        return False
