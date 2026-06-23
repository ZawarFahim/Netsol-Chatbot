import os
import sys
import requests

ONNX_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/kokoro-v1.0.onnx"
VOICES_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files/voices-v1.0.bin"
SFACE_URL = "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx"

BACKEND_DIR = os.path.join(os.path.dirname(__file__), "backend")
ONNX_PATH = os.path.join(BACKEND_DIR, "kokoro-v1.0.onnx")
VOICES_PATH = os.path.join(BACKEND_DIR, "voices-v1.0.bin")
SFACE_PATH = os.path.join(BACKEND_DIR, "sface.onnx")

def download_file(url: str, dest_path: str):
    if os.path.exists(dest_path):
        return
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(dest_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

if __name__ == "__main__":
    os.makedirs(BACKEND_DIR, exist_ok=True)
    download_file(ONNX_URL, ONNX_PATH)
    download_file(VOICES_URL, VOICES_PATH)
    download_file(SFACE_URL, SFACE_PATH)
    print("--- All model files are ready! ---")