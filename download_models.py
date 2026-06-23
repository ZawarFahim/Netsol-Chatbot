import os
import sys
import requests
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent / "backend"
ONNX_PATH = BACKEND_DIR / "kokoro-v1.0.onnx"
VOICES_PATH = BACKEND_DIR / "voices-v1.0.bin"
SFACE_PATH = BACKEND_DIR / "sface.onnx"

ONNX_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx"
VOICES_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"
SFACE_URL = "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx"

def download_file(url: str, dest_path: Path):
    if dest_path.exists():
        print(f"--- {dest_path.name} already exists. Skipping. ---")
        return

    print(f"--- Downloading {dest_path.name} from {url} ---")
    temp_path = dest_path.with_suffix(".tmp")
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        
        downloaded = 0
        with open(temp_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        sys.stdout.write(f"\rProgress: {percent:.1f}% ({downloaded}/{total_size} bytes)")
                        sys.stdout.flush()
        print("\n--- Download complete. Saving file... ---")
        temp_path.rename(dest_path)
        print(f"--- Saved {dest_path.name} successfully. ---")
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink()
        print(f"--- Error downloading {dest_path.name}: {e} ---")
        sys.exit(1)

if __name__ == "__main__":
    BACKEND_DIR.mkdir(parents=True, exist_ok=True)
    download_file(ONNX_URL, ONNX_PATH)
    download_file(VOICES_URL, VOICES_PATH)
    download_file(SFACE_URL, SFACE_PATH)
    print("--- All model files are ready! ---")