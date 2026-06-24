import os
import sys
import requests

ONNX_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx"
VOICES_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"
SFACE_URL = "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx"

WEIGHTS_DIR = os.path.join(os.path.dirname(__file__), "backend", "weights")
ONNX_PATH = os.path.join(WEIGHTS_DIR, "kokoro-v1.0.onnx")
VOICES_PATH = os.path.join(WEIGHTS_DIR, "voices-v1.0.bin")
SFACE_PATH = os.path.join(WEIGHTS_DIR, "sface.onnx")

def download_file(url: str, dest_path: str):
    filename = os.path.basename(dest_path)
    response = requests.get(url, stream=True)
    response.raise_for_status()
    total_size = int(response.headers.get('content-length', 0))
    
    if os.path.exists(dest_path):
        if os.path.getsize(dest_path) == total_size:
            print(f"--- {filename} already exists and is complete. ---")
            return
        else:
            print(f"--- Removing incomplete/partially downloaded {filename} ---")
            os.remove(dest_path)

    print(f"Downloading {filename} ({total_size / (1024*1024):.1f} MB)...")
    downloaded = 0
    last_printed = 0
    with open(dest_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=65536):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                percent = (downloaded / total_size) * 100 if total_size else 0
                if int(percent) // 10 > last_printed:
                    last_printed = int(percent) // 10
                    print(f"  Downloaded: {percent:.0f}% ({downloaded / (1024*1024):.1f} MB)")
    print(f"--- Finished downloading {filename} ---")

if __name__ == "__main__":
    os.makedirs(WEIGHTS_DIR, exist_ok=True)
    download_file(ONNX_URL, ONNX_PATH)
    download_file(VOICES_URL, VOICES_PATH)
    download_file(SFACE_URL, SFACE_PATH)
    print("--- All model files are ready! ---")