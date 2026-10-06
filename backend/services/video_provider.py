from abc import ABC, abstractmethod
import asyncio
import os
import time
import logging
from backend.services.ffmpeg_service import ffmpeg_service
from backend.services.storage_service import storage_service

logger = logging.getLogger("cineforge.video_provider")


class VideoProvider(ABC):
    @abstractmethod
    async def generate_video(
        self,
        prompt: str,
        negative_prompt: str,
        image_url: str = None,
        duration: int = 5,
        width: int = 1280,
        height: int = 720,
        fps: int = 24,
        seed: int = 42,
        steps: int = 25,
        guidance: float = 6.5,
        job_id: str = None,
        progress_callback = None
    ) -> dict:
        pass


class MockVideoProvider(VideoProvider):
    async def generate_video(
        self,
        prompt: str,
        negative_prompt: str,
        image_url: str = None,
        duration: int = 5,
        width: int = 1280,
        height: int = 720,
        fps: int = 24,
        seed: int = 42,
        steps: int = 25,
        guidance: float = 6.5,
        job_id: str = None,
        progress_callback = None
    ) -> dict:
        total_steps = steps or 25
        start_time = time.time()
        project_id = "default"

        # 1. Simulate progress steps
        for step in range(1, total_steps + 1):
            await asyncio.sleep(0.12)
            progress_pct = round((step / total_steps) * 100.0, 1)
            elapsed = time.time() - start_time
            avg_per_step = elapsed / step
            remaining_steps = total_steps - step
            eta_seconds = max(0, int(remaining_steps * avg_per_step))

            if progress_callback:
                await progress_callback({
                    "job_id": job_id,
                    "status": "processing",
                    "progress": progress_pct,
                    "current_step": step,
                    "total_steps": total_steps,
                    "eta_seconds": eta_seconds,
                    "message": f"Sampling step {step}/{total_steps} (Mock FFmpeg Engine)"
                })

        # 2. Check if FFmpeg is installed
        if not ffmpeg_service.is_ffmpeg_installed():
            err_msg = "FFmpeg is not installed or not found on system PATH. Cannot synthesize MP4 video."
            logger.error(err_msg)
            fail_result = {
                "job_id": job_id,
                "status": "failed",
                "progress": 0,
                "error": err_msg,
                "message": err_msg,
            }
            if progress_callback:
                await progress_callback(fail_result)
            raise RuntimeError(err_msg)

        # 3. Generate playable MP4 file in generated/projects/<project_id>/videos/<job_id>.mp4
        dirs = storage_service.get_project_dirs(project_id)
        video_filename = f"{job_id}.mp4"
        output_abs_path = os.path.join(dirs["videos"], video_filename)

        is_i2v = bool(image_url)

        if is_i2v:
            success = ffmpeg_service.generate_ken_burns_video(
                image_input=image_url,
                output_path=output_abs_path,
                width=width,
                height=height,
                fps=fps,
                duration=duration
            )
        else:
            success = ffmpeg_service.generate_test_pattern_video(
                output_path=output_abs_path,
                width=width,
                height=height,
                fps=fps,
                duration=duration
            )

        # 4. Strictly verify file exists and size > 0 bytes
        if not success or not os.path.exists(output_abs_path) or os.path.getsize(output_abs_path) == 0:
            err_msg = f"FFmpeg video synthesis failed: Output file {output_abs_path} could not be created or is 0 bytes."
            logger.error(err_msg)
            fail_result = {
                "job_id": job_id,
                "status": "failed",
                "progress": 0,
                "error": err_msg,
                "message": err_msg,
            }
            if progress_callback:
                await progress_callback(fail_result)
            raise RuntimeError(err_msg)

        local_url = f"/generated/projects/{project_id}/videos/{video_filename}"
        thumbnail_url = image_url if is_i2v else "https://images.unsplash.com/photo-1519501025264-65ba15a82390?auto=format&fit=crop&w=800&q=80"

        # Final completed result payload
        result = {
            "job_id": job_id,
            "status": "completed",
            "progress": 100.0,
            "current_step": total_steps,
            "total_steps": total_steps,
            "eta_seconds": 0,
            "video_url": local_url,
            "thumbnail_url": thumbnail_url,
            "is_mock": True,
            "provider": "mock"
        }

        if progress_callback:
            await progress_callback(result)

        return result



mock_video_provider = MockVideoProvider()
