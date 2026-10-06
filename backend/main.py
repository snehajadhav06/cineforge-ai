import os
import shutil
import logging
from dotenv import load_dotenv

# Resolve absolute path to project base directory
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENV_PATH = os.path.join(BASE_DIR, ".env")
ENV_EXAMPLE_PATH = os.path.join(BASE_DIR, ".env.example")

# Create .env from .env.example if missing and set MODE=local
if not os.path.exists(ENV_PATH):
    if os.path.exists(ENV_EXAMPLE_PATH):
        shutil.copy(ENV_EXAMPLE_PATH, ENV_PATH)
    else:
        with open(ENV_PATH, "w", encoding="utf-8") as f:
            f.write("MODE=local\n")

# Load environment once at startup before any service imports
load_dotenv(ENV_PATH)

# Retrieve and log resolved MODE
RESOLVED_MODE = os.getenv("MODE", "local").strip().lower()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cineforge.main")
logger.info(f"Loaded environment from {ENV_PATH}. Resolved MODE: {RESOLVED_MODE}")

# Startup import check for gradio_client dependency
try:
    import gradio_client
    GRADIO_CLIENT_INSTALLED = True
    logger.info("gradio_client package is installed and importable.")
except ImportError:
    GRADIO_CLIENT_INSTALLED = False
    logger.warning("WARNING: gradio_client python package is NOT installed. HuggingFace Space provider will fail if invoked.")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.database import init_db
from backend.routers import generate, prompt, generations, system
from backend.services.ffmpeg_service import ffmpeg_service
from backend.services.comfyui_provider import comfyui_provider

# Initialize SQLite database schema & migrations
init_db()

app = FastAPI(
    title="CineForge AI Backend API",
    description="Local-first AI Text-to-Video & Image-to-Video Engine API",
    version="1.0.0"
)

# CORS Middleware for Frontend
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GENERATED_DIR = os.path.abspath(os.path.join(BASE_DIR, "generated"))
os.makedirs(GENERATED_DIR, exist_ok=True)

# Mount generated directory as static files (supports Range requests & MP4 streaming)
app.mount("/generated", StaticFiles(directory=GENERATED_DIR), name="generated")

# Include API Routers
app.include_router(generate.router)
app.include_router(prompt.router)
app.include_router(generations.router)
app.include_router(system.router)


@app.on_event("startup")
def startup_event():
    ffmpeg_ok = ffmpeg_service.is_ffmpeg_installed()
    ffmpeg_path = ffmpeg_service.get_ffmpeg_path()
    logger.info("==================================================")
    logger.info(f"CineForge AI Backend Starting on Port 8000")
    logger.info(f"Execution MODE: {RESOLVED_MODE}")
    logger.info(f"Resolved GENERATED_DIR: {GENERATED_DIR}")
    logger.info(f"FFmpeg Installed: {ffmpeg_ok} (Path: {ffmpeg_path})")
    logger.info(f"gradio_client installed: {GRADIO_CLIENT_INSTALLED}")
    logger.info("==================================================")


@app.get("/api/health")
async def health_check():
    ffmpeg_ok = ffmpeg_service.is_ffmpeg_installed()
    comfyui_ok = await comfyui_provider.is_available()
    hf_space_id = os.getenv("HF_SPACE_ID", "").strip()
    hf_configured = bool(hf_space_id)

    return {
        "mode": os.getenv("MODE", "local"),
        "comfyui_reachable": comfyui_ok,
        "hf_space_configured": hf_configured,
        "gradio_client_installed": GRADIO_CLIENT_INSTALLED,
        "ffmpeg": ffmpeg_ok,
        "generated_dir": GENERATED_DIR,
    }


@app.get("/")
def root():
    return {
        "status": "online",
        "app": "CineForge AI Backend Engine",
        "version": "1.0.0",
        "mode": os.getenv("MODE", "local"),
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
