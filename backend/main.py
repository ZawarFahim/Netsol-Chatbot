from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi.responses import HTMLResponse
from backend.routes import router
from backend.auth_routes import auth_router
from backend.upload_routes import upload_router
from backend.db import client
from backend.audio import get_whisper_model, get_kokoro_engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        client.admin.command('ping')
        get_whisper_model()
        get_kokoro_engine()
    except Exception:
        pass
    yield

app = FastAPI(lifespan=lifespan)

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

@app.get("/app", response_class=HTMLResponse)
def serve_app():
    with open("index.html", "r") as f: return f.read()

@app.get("/loginpage.html", response_class=HTMLResponse)
def serve_login():
    with open("loginpage.html", "r") as f: return f.read()

@app.get("/")
def home():
    try:
        client.admin.command('ping')
        return {"status": "online", "database": "Connected"}
    except Exception:
        return {"status": "online", "database": "Disconnected"}