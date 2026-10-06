import os
import asyncio
import uuid
import json
import logging
from datetime import datetime
from typing import Dict, AsyncGenerator
from sqlalchemy.orm import Session
from backend.database import Generation, SessionLocal
from backend.schemas import GenerationRequest
from backend.services.cache_service import cache_service
from backend.services.storage_service import storage_service
from backend.services.resolution_helper import get_model_valid_dimensions
from backend.services.video_provider import mock_video_provider
from backend.services.comfyui_provider import comfyui_provider
from backend.services.providers.hf_space_provider import hf_space_provider

logger = logging.getLogger("cineforge.video_service")
JOB_QUEUES: Dict[str, asyncio.Queue] = {}


class VideoService:
    @staticmethod
    def get_job_queue(job_id: str) -> asyncio.Queue:
        if job_id not in JOB_QUEUES:
            JOB_QUEUES[job_id] = asyncio.Queue()
        return JOB_QUEUES[job_id]

    @staticmethod
    async def stream_job_events(job_id: str) -> AsyncGenerator[str, None]:
        queue = VideoService.get_job_queue(job_id)
        try:
            while True:
                data = await queue.get()
                yield f"data: {json.dumps(data)}\n\n"
                if data.get("status") in ["completed", "failed"]:
                    break
        except asyncio.CancelledError:
            pass
        finally:
            if job_id in JOB_QUEUES:
                del JOB_QUEUES[job_id]

    @staticmethod
    async def create_and_run_generation(req: GenerationRequest, db: Session) -> Generation:
        seed = req.seed if req.seed is not None else int(datetime.utcnow().timestamp() * 1000) % 90000000

        width, height = get_model_valid_dimensions(req.resolution or "512p", req.aspect_ratio or "16:9")

        sha256_hash = cache_service.compute_generation_hash(
            prompt=req.prompt,
            negative_prompt=req.negative_prompt or "",
            model_id=req.model_id or "ltx-video",
            seed=seed,
            width=width,
            height=height,
            duration=req.duration or 5,
            fps=req.fps or 24,
            steps=req.steps or 25,
            guidance=req.guidance or 6.5,
            input_image_hash=req.reference_image_url or ""
        )

        existing = db.query(Generation).filter(Generation.sha256_hash == sha256_hash).first()
        if existing:
            return existing

        storage_service.get_project_dirs(req.project_id or "default")
        gen_id = f"gen-{uuid.uuid4().hex[:12]}"

        generation = Generation(
            id=gen_id,
            project_id=req.project_id or "default",
            prompt=req.prompt,
            negative_prompt=req.negative_prompt or "",
            mode=req.mode or "text-to-video",
            reference_image_url=req.reference_image_url,
            model_id=req.model_id or "ltx-video",
            duration=req.duration or 5,
            aspect_ratio=req.aspect_ratio or "16:9",
            resolution=req.resolution or "512p",
            fps=req.fps or 24,
            seed=seed,
            is_fixed_seed=req.is_fixed_seed or False,
            steps=req.steps or 25,
            guidance=req.guidance or 6.5,
            status="queued",
            progress=0.0,
            current_step=0,
            total_steps=req.steps or 25,
            eta_seconds=int((req.steps or 25) * 0.4),
            video_url=None,
            thumbnail_url=req.reference_image_url,
            is_favorite=False,
            sha256_hash=sha256_hash,
            created_at=datetime.utcnow()
        )

        db.add(generation)
        db.commit()
        db.refresh(generation)

        asyncio.create_task(VideoService._run_async_job(gen_id, req, width, height, seed))
        return generation

    @staticmethod
    async def _run_async_job(gen_id: str, req: GenerationRequest, width: int, height: int, seed: int):
        queue = VideoService.get_job_queue(gen_id)

        async def on_progress(event: dict):
            await queue.put(event)
            db_session = SessionLocal()
            try:
                g = db_session.query(Generation).filter(Generation.id == gen_id).first()
                if g:
                    g.status = event.get("status", g.status)
                    g.progress = event.get("progress", g.progress)
                    g.current_step = event.get("current_step", g.current_step)
                    g.eta_seconds = event.get("eta_seconds", g.eta_seconds)
                    if event.get("video_url"):
                        g.video_url = event["video_url"]
                    if event.get("thumbnail_url"):
                        g.thumbnail_url = event["thumbnail_url"]
                    db_session.commit()
            finally:
                db_session.close()

        mode_env = os.getenv("MODE", "mock").lower()

        try:
            if mode_env == "mock":
                provider = mock_video_provider
            else:
                # MODE is local or cloud: Provider Order Check
                # 1. ComfyUI if reachable
                if await comfyui_provider.is_available():
                    provider = comfyui_provider
                # 2. HuggingFace Space if configured and reachable
                elif await hf_space_provider.is_available():
                    provider = hf_space_provider
                # 3. Otherwise show clear error message. NEVER fall back to mock when MODE is not mock!
                else:
                    err_msg = (
                        "No video generator available. Please start ComfyUI locally (http://127.0.0.1:8188) "
                        "or configure a valid HuggingFace Space in HF_SPACE_ID."
                    )
                    logger.error(err_msg)
                    fail_event = {"job_id": gen_id, "status": "failed", "error": err_msg, "message": err_msg}
                    await on_progress(fail_event)
                    return

            await provider.generate_video(
                prompt=req.prompt,
                negative_prompt=req.negative_prompt or "",
                image_url=req.reference_image_url,
                duration=req.duration or 5,
                width=width,
                height=height,
                fps=req.fps or 24,
                seed=seed,
                steps=req.steps or 25,
                guidance=req.guidance or 6.5,
                job_id=gen_id,
                progress_callback=on_progress
            )
        except Exception as err:
            err_msg = str(err)
            fail_event = {"job_id": gen_id, "status": "failed", "error": err_msg, "message": err_msg}
            await on_progress(fail_event)


video_service = VideoService()
