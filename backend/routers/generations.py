import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.database import get_db, Generation
from backend.schemas import GenerationResponse
from backend.services.video_service import video_service

router = APIRouter(prefix="/api/generations", tags=["Generations History"])


@router.get("", response_model=List[GenerationResponse])
def list_generations(
    search: Optional[str] = None,
    favorite_only: Optional[bool] = False,
    mode: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Generation)

    if favorite_only:
        query = query.filter(Generation.is_favorite == True)

    if mode:
        query = query.filter(Generation.mode == mode)

    if search:
        query = query.filter(Generation.prompt.ilike(f"%{search}%"))

    return query.order_by(Generation.created_at.desc()).all()


@router.get("/{id}", response_model=GenerationResponse)
def get_generation(id: str, db: Session = Depends(get_db)):
    gen = db.query(Generation).filter(Generation.id == id).first()
    if not gen:
        raise HTTPException(status_code=404, detail="Generation not found")
    return gen


@router.get("/{id}/stream")
async def stream_generation_progress(id: str):
    return StreamingResponse(
        video_service.stream_job_events(id),
        media_type="text/event-stream"
    )


@router.get("/{id}/status")
def get_generation_status(id: str, db: Session = Depends(get_db)):
    gen = db.query(Generation).filter(Generation.id == id).first()
    if not gen:
        raise HTTPException(status_code=404, detail="Generation not found")
    return {
        "id": gen.id,
        "status": gen.status,
        "progress": gen.progress,
        "current_step": gen.current_step,
        "total_steps": gen.total_steps,
        "eta_seconds": gen.eta_seconds,
        "video_url": gen.video_url,
    }


@router.get("/{id}/download")
def download_generation_video(id: str, db: Session = Depends(get_db)):
    gen = db.query(Generation).filter(Generation.id == id).first()
    if not gen:
        raise HTTPException(status_code=404, detail="Generation not found")

    # If local generated file exists, serve as attachment; else redirect/stream sample
    if gen.video_url and gen.video_url.startswith("/generated/"):
        rel_path = gen.video_url.lstrip("/")
        abs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", rel_path))
        if os.path.exists(abs_path):
            return FileResponse(
                abs_path,
                media_type="video/mp4",
                filename=f"cineforge-{gen.id}.mp4"
            )

    return {
        "download_url": gen.video_url or "/generated/projects/default/videos/sample.mp4",
        "filename": f"cineforge-{gen.id}.mp4"
    }


@router.patch("/{id}/favorite", response_model=GenerationResponse)
def toggle_favorite(id: str, db: Session = Depends(get_db)):
    gen = db.query(Generation).filter(Generation.id == id).first()
    if not gen:
        raise HTTPException(status_code=404, detail="Generation not found")

    gen.is_favorite = not gen.is_favorite
    db.commit()
    db.refresh(gen)
    return gen


@router.delete("/{id}")
def delete_generation(id: str, db: Session = Depends(get_db)):
    gen = db.query(Generation).filter(Generation.id == id).first()
    if not gen:
        raise HTTPException(status_code=404, detail="Generation not found")
    db.delete(gen)
    db.commit()
    return {"message": "Generation deleted successfully", "id": id}
