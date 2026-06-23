from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from backend.routes import router
from backend.auth_routes import auth_router
from backend.upload_routes import upload_router
from backend.db import client
from backend.audio import get_whisper_model, get_kokoro_engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("--- [Startup] Verifying Database Connection ---")
    try:
        client.admin.command('ping')
        print("--- [Startup] MongoDB Atlas connection: SUCCESS ---")
    except Exception as e:
        print(f"--- [Startup] MongoDB Atlas connection: FAILED ({e}) ---")

    print("--- [Startup] Warm loading Speech Models to Memory ---")
    try:
        get_whisper_model()
        get_kokoro_engine()
        print("--- [Startup] Model tracking ready for incoming requests ---")
    except Exception as e:
        print(f"--- [Startup] Model caching run failed: {e} ---")
    yield
    print("--- [Shutdown] Cleaning pipeline context resources ---")

app = FastAPI(
    title="AI Voice Assistant API",
    description="Backend API for the RAG Chatbot with Voice capabilities.",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(auth_router)
app.include_router(upload_router)

@app.get("/")
def home():
    try:
        client.admin.command('ping')
        db_status = "Connected"
    except Exception:
        db_status = "Disconnected"
        
    return {
        "status": "online",
        "database": db_status,
        "message": "Voice AI Assistant API is running."
    }