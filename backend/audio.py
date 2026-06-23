import os
import tempfile
import whisper
import soundfile as sf
from pathlib import Path
from kokoro_onnx import Kokoro

BACKEND_DIR = Path(__file__).resolve().parent

ONNX_PATH = BACKEND_DIR / "kokoro-v1.0.onnx"
VOICES_PATH = BACKEND_DIR / "voices-v1.0.bin"

kokoro_engine = None
whisper_model = None

def get_whisper_model():
    global whisper_model
    if whisper_model is None:
        print("--- Initializing Whisper Local Model (tiny) ---")
        whisper_model = whisper.load_model("tiny")
        print("--- Whisper engine running successfully ---")
    return whisper_model

def get_kokoro_engine():
    global kokoro_engine
    if kokoro_engine is None:
        if not ONNX_PATH.exists() or not VOICES_PATH.exists():
            raise FileNotFoundError("Missing Kokoro ONNX model components. Please execute download_models.py first.")
        print("--- Initializing Kokoro ONNX Engine ---")
        kokoro_engine = Kokoro(str(ONNX_PATH), str(VOICES_PATH))
        print("--- Kokoro TTS engine running successfully ---")
    return kokoro_engine

def transcribe_audio_local(audio_bytes: bytes, filename: str) -> str:
    ext = filename.split(".")[-1].lower() if "." in filename else "wav"
    with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        model = get_whisper_model()
        result = model.transcribe(tmp_path)
        return result.get("text", "").strip()
    except Exception as e:
        print(f"Audio transcription error: {e}")
        return ""
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def text_to_speech_kokoro(text: str) -> bytes:
    try:
        engine = get_kokoro_engine()
        samples, sample_rate = engine.create(
            text,
            voice="af_sarah",
            speed=1.0,
            lang="en-us"
        )
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            temp_filename = tmp.name
        
        sf.write(temp_filename, samples, sample_rate)
        with open(temp_filename, "rb") as f:
            audio_bytes = f.read()
            
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
        return audio_bytes
    except Exception as e:
        print(f"TTS synthesis error: {e}")
        return b""