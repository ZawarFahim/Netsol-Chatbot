from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi.responses import HTMLResponse, Response
from backend.routes.chat import router
from backend.routes.auth import auth_router
from backend.routes.upload import upload_router
from backend.database import client
from backend.services.audio import get_whisper_model, get_kokoro_engine
import logfire
import os

try:
    if os.getenv("LOGFIRE_TOKEN"):
        logfire.configure()
    else:
        logfire.configure(send_to_logfire=False)
except Exception as e:
    print(f"Logfire initialization warning: {e}")


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
logfire.instrument_fastapi(app)

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

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)

@app.get("/app", response_class=HTMLResponse)
def serve_app():
    with open("frontend/index.html", "r") as f: return f.read()

@app.get("/loginpage.html", response_class=HTMLResponse)
def serve_login():
    with open("frontend/loginpage.html", "r") as f: return f.read()

@app.get("/")
def home():
    try:
        client.admin.command('ping')
        return {"status": "online", "database": "Connected"}
    except Exception:
        return {"status": "online", "database": "Disconnected"}