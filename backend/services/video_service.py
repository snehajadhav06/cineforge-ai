import os
import asyncio
import uuid
import json
import logging
from datetime import datetime
from typing import Dict, AsyncGenerator
from sqlalchemy.orm import Session
from backend.database import Generation, SessionLocal
from backend.schemas import GenerationRequest, ExtendRequest
from backend.services.cache_service import cache_service
from backend.services.storage_service import storage_service
from backend.services.resolution_helper import get_model_valid_dimensions
from backend.services.video_provider import mock_video_provider
from backend.services.comfyui_provider import comfyui_provider
from backend.services.providers.hf_space_provider import hf_space_provider

logger = logging.getLogger("cineforge.video_service")
JOB_QUEUES: Dict[str, asyncio.Queue] = {}

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


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

        mode_env = os.getenv("MODE", "local").lower()

        # Determine target provider for hash & DB tagging
        if mode_env == "mock":
            target_provider = "mock"
        else:
            if await comfyui_provider.is_available():
                target_provider = f"comfyui:{req.model_id or 'ltx-video'}"
            elif await hf_space_provider.is_available():
                target_provider = f"hf-space:{hf_space_provider.space_id}"
            else:
                target_provider = "none"

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
            input_image_hash=req.reference_image_url or "",
            mode=req.mode or "text-to-video",
            provider=target_provider
        )

        existing = db.query(Generation).filter(Generation.sha256_hash == sha256_hash).first()
        if existing:
            is_valid_cache = False
            if existing.status == "completed" and existing.video_url:
                clean_url = existing.video_url.lstrip("/")
                video_abs_path = os.path.join(BASE_DIR, clean_url)
                if os.path.exists(video_abs_path) and os.path.getsize(video_abs_path) > 0:
                    is_mock_result = (existing.provider == "mock")
                    if mode_env == "mock" or not is_mock_result:
                        is_valid_cache = True

            if is_valid_cache:
                logger.info(f"Returning cached generation {existing.id} (provider={existing.provider})")
                return existing
            else:
                logger.info(f"Invalidating stale cache row {existing.id} (status={existing.status}, provider={existing.provider})")
                db.delete(existing)
                db.commit()

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
            provider="mock" if mode_env == "mock" else target_provider,
            created_at=datetime.utcnow()
        )

        db.add(generation)
        db.commit()
        db.refresh(generation)

        asyncio.create_task(VideoService._run_async_job(gen_id, req, width, height, seed))
        return generation

    @staticmethod
    async def create_and_run_extension(base_gen: Generation, req: ExtendRequest, db: Session) -> Generation:
        gen_id = f"gen-{uuid.uuid4().hex[:12]}"
        extended_prompt = f"{base_gen.prompt} (Continuation sequence +{req.additional_duration or 5}s)"

        generation = Generation(
            id=gen_id,
            project_id=base_gen.project_id or "default",
            prompt=extended_prompt,
            negative_prompt=base_gen.negative_prompt,
            mode=base_gen.mode,
            reference_image_url=base_gen.reference_image_url,
            model_id=base_gen.model_id,
            duration=base_gen.duration + (req.additional_duration or 5),
            aspect_ratio=base_gen.aspect_ratio,
            resolution=base_gen.resolution,
            fps=base_gen.fps,
            seed=base_gen.seed + 1,
            is_fixed_seed=True,
            steps=base_gen.steps,
            guidance=base_gen.guidance,
            status="queued",
            progress=0.0,
            current_step=0,
            total_steps=base_gen.steps,
            eta_seconds=25,
            video_url=None,
            thumbnail_url=base_gen.thumbnail_url,
            is_favorite=False,
            provider=base_gen.provider or "hf-space:Lightricks/ltx-video-distilled",
            created_at=datetime.utcnow()
        )

        db.add(generation)
        db.commit()
        db.refresh(generation)

        asyncio.create_task(VideoService._run_async_extension_job(gen_id, base_gen, req))
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
                    if event.get("provider"):
                        g.provider = event["provider"]
                    db_session.commit()
            finally:
                db_session.close()

        mode_env = os.getenv("MODE", "local").lower()

        try:
            if mode_env == "mock":
                provider = mock_video_provider
                provider_tag = "mock"
            else:
                if await comfyui_provider.is_available():
                    provider = comfyui_provider
                    provider_tag = f"comfyui:{req.model_id or 'ltx-video'}"
                elif await hf_space_provider.is_available():
                    provider = hf_space_provider
                    provider_tag = f"hf-space:{hf_space_provider.space_id}"
                else:
                    err_msg = (
                        "No video generator is reachable. "
                        "ComfyUI is offline at http://127.0.0.1:8188 and HuggingFace Space is not reachable. "
                        "Please start ComfyUI locally or configure a valid HuggingFace Space in HF_SPACE_ID."
                    )
                    logger.error(err_msg)
                    fail_event = {"job_id": gen_id, "status": "failed", "error": err_msg, "message": err_msg}
                    await on_progress(fail_event)
                    return

            res = await provider.generate_video(
                prompt=req.prompt,
                negative_prompt=req.negative_prompt or "",
                image_url=req.reference_image_url,
                duration=req.duration or 5,
                width=width,
                height=height,
                fps=req.fps or 24,
                seed=seed,
                is_fixed_seed=req.is_fixed_seed or False,
                steps=req.steps or 25,
                guidance=req.guidance or 6.5,
                job_id=gen_id,
                progress_callback=on_progress
            )
            res["provider"] = provider_tag
            await on_progress(res)

        except Exception as err:
            err_msg = str(err)
            fail_event = {"job_id": gen_id, "status": "failed", "error": err_msg, "message": err_msg}
            await on_progress(fail_event)

    @staticmethod
    async def _run_async_extension_job(gen_id: str, base_gen: Generation, req: ExtendRequest):
        queue = VideoService.get_job_queue(gen_id)

        async def on_progress(event: dict):
            await queue.put(event)
            db_session = SessionLocal()
            try:
                g = db_session.query(Generation).filter(Generation.id == gen_id).first()
                if g:
                    g.status = event.get("status", g.status)
                    g.progress = event.get("progress", g.progress)
                    if event.get("video_url"):
                        g.video_url = event["video_url"]
                    if event.get("thumbnail_url"):
                        g.thumbnail_url = event["thumbnail_url"]
                    if event.get("provider"):
                        g.provider = event["provider"]
                    db_session.commit()
            finally:
                db_session.close()

        try:
            prev_video_url = base_gen.video_url.lstrip("/") if base_gen.video_url else ""
            prev_video_abs_path = os.path.join(BASE_DIR, prev_video_url)

            if await hf_space_provider.is_available():
                res = await hf_space_provider.extend_video(
                    prev_video_abs_path=prev_video_abs_path,
                    prompt=base_gen.prompt,
                    negative_prompt=base_gen.negative_prompt,
                    project_id=base_gen.project_id or "default",
                    job_id=gen_id,
                    progress_callback=on_progress
                )
                await on_progress(res)
            else:
                mock_res = await mock_video_provider.generate_video(
                    prompt=base_gen.prompt,
                    negative_prompt=base_gen.negative_prompt,
                    duration=5,
                    job_id=gen_id,
                    progress_callback=on_progress
                )
                await on_progress(mock_res)
        except Exception as err:
            err_msg = str(err)
            await on_progress({"job_id": gen_id, "status": "failed", "error": err_msg, "message": err_msg})


video_service = VideoService()
