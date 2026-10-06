import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.database import init_db
from backend.routers import generate, prompt, generations, system
from backend.services.ffmpeg_service import ffmpeg_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cineforge.main")

# Initialize SQLite database schema
init_db()

app = FastAPI(
    title="CineForge AI Backend API",
    description="Local-first AI Text-to-Video & Image-to-Video Engine API",
    version="1.0.0"
)

# CORS Middleware for Frontend (port 3000 / 5173)
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

# Resolve absolute path to generated directory from project root
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
GENERATED_DIR = os.path.abspath(os.path.join(BASE_DIR, "generated"))
os.makedirs(GENERATED_DIR, exist_ok=True)

# Mount generated directory as static files (supports HTTP Range requests & video/mp4 headers)
app.mount("/generated", StaticFiles(directory=GENERATED_DIR), name="generated")

# Include Routers
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
    logger.info(f"Resolved GENERATED_DIR: {GENERATED_DIR}")
    logger.info(f"FFmpeg Installed: {ffmpeg_ok} (Path: {ffmpeg_path})")
    logger.info("==================================================")


@app.get("/api/health")
def health_check():
    ffmpeg_ok = ffmpeg_service.is_ffmpeg_installed()
    return {
        "ffmpeg": ffmpeg_ok,
        "generated_dir": GENERATED_DIR,
        "mode": os.getenv("MODE", "mock"),
    }


@app.get("/")
def root():
    return {
        "status": "online",
        "app": "CineForge AI Backend Engine",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
