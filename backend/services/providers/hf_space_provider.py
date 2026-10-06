import os
import json
import asyncio
import logging
import tempfile
import shutil
import base64
from backend.services.video_provider import VideoProvider
from backend.services.storage_service import storage_service
from backend.services.ffmpeg_service import ffmpeg_service
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("cineforge.hf_space_provider")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
CONFIG_SPACES_PATH = os.path.join(BASE_DIR, "config", "spaces.json")


class HuggingFaceSpaceProvider(VideoProvider):
    def __init__(self, space_id: str = None, token: str = None):
        self.space_id = space_id or os.getenv("HF_SPACE_ID", "Lightricks/LTX-Video-Demo")
        self.token = token or os.getenv("HF_TOKEN", None) or None
        self._spaces_config = self._load_spaces_config()

    def _load_spaces_config(self) -> list:
        if os.path.exists(CONFIG_SPACES_PATH):
            try:
                with open(CONFIG_SPACES_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to read spaces.json: {e}")
        return []

    def get_space_info(self, space_id: str) -> dict:
        for space in self._spaces_config:
            if space.get("id") == space_id:
                return space
        return {
            "id": space_id,
            "name": space_id,
            "api_name": "/generate",
            "supported_modes": ["t2v", "i2v"]
        }

    async def is_available(self) -> bool:
        if not self.space_id:
            return False
        try:
            from gradio_client import Client
            client = Client(self.space_id, token=self.token)
            api_info = client.view_api(return_format="dict")
            logger.info(f"HuggingFace Space '{self.space_id}' API Signature: {api_info}")
            return True
        except Exception as e:
            logger.warning(f"HuggingFace Space '{self.space_id}' not reachable: {e}")
            return False

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
        try:
            from gradio_client import Client, handle_file
        except ImportError:
            err_msg = "gradio_client python package is not installed."
            logger.error(err_msg)
            raise RuntimeError(err_msg)

        if not self.space_id:
            err_msg = "No HuggingFace Space ID configured in HF_SPACE_ID."
            logger.error(err_msg)
            raise RuntimeError(err_msg)

        if progress_callback:
            await progress_callback({
                "job_id": job_id,
                "status": "processing",
                "progress": 10.0,
                "current_step": 1,
                "total_steps": steps or 25,
                "eta_seconds": 30,
                "message": f"Connecting to HuggingFace Space: {self.space_id}..."
            })

        try:
            client = Client(self.space_id, token=self.token)
        except Exception as e:
            err_msg = f"Failed to connect to HuggingFace Space '{self.space_id}': {e}"
            logger.error(err_msg)
            raise RuntimeError(err_msg)

        is_i2v = bool(image_url)
        space_info = self.get_space_info(self.space_id)
        api_name = space_info.get("api_name", "/generate")

        temp_img_file = None
        handle_img = None

        if is_i2v and image_url:
            if image_url.startswith("data:image"):
                header, encoded = image_url.split(",", 1)
                img_bytes = base64.b64decode(encoded)
                ext = ".png" if "png" in header else ".jpg"
                temp_img_file = tempfile.NamedTemporaryFile("wb", delete=False, suffix=ext)
                temp_img_file.write(img_bytes)
                temp_img_file.close()
                handle_img = handle_file(temp_img_file.name)
            elif os.path.exists(image_url):
                handle_img = handle_file(image_url)

        # Call client.submit with args according to Space API
        try:
            # Prepare arguments matching common LTX/Wan Gradio space signatures
            if is_i2v:
                args = (prompt, negative_prompt, handle_img, height, width, duration, seed, steps, guidance)
            else:
                args = (prompt, negative_prompt, height, width, duration, seed, steps, guidance)

            job = client.submit(*args, api_name=api_name)

            # Monitor queue position & status
            step_count = 1
            while not job.done():
                await asyncio.sleep(1.0)
                step_count += 1
                status = job.status()
                eta = status.eta if hasattr(status, 'eta') and status.eta is not None else max(0, 45 - step_count)
                queue_pos = getattr(status, 'queue_size', None)
                msg = f"HF Space Queue: position {queue_pos}" if queue_pos else "HF Space synthesizing video..."

                if progress_callback:
                    await progress_callback({
                        "job_id": job_id,
                        "status": "processing",
                        "progress": min(95.0, round(step_count * 3.5, 1)),
                        "current_step": min(steps or 25, step_count),
                        "total_steps": steps or 25,
                        "eta_seconds": int(eta),
                        "message": msg
                    })

            result_path = job.result()
        except Exception as e:
            if temp_img_file and os.path.exists(temp_img_file.name):
                try: os.remove(temp_img_file.name)
                except Exception: pass
            err_msg = f"HuggingFace Space '{self.space_id}' API error or quota exceeded: {e}"
            logger.error(err_msg)
            raise RuntimeError(err_msg)

        if temp_img_file and os.path.exists(temp_img_file.name):
            try: os.remove(temp_img_file.name)
            except Exception: pass

        if not result_path or not os.path.exists(result_path):
            err_msg = f"HuggingFace Space '{self.space_id}' returned no output file."
            logger.error(err_msg)
            raise RuntimeError(err_msg)

        # Copy & convert result file into generated/projects/default/videos/<job_id>.mp4
        project_id = "default"
        dirs = storage_service.get_project_dirs(project_id)
        local_video_filename = f"{job_id}.mp4"
        dest_abs_path = os.path.join(dirs["videos"], local_video_filename)

        # Ensure H.264 MP4 conversion if returned file is webm/avi/mkv
        if result_path.endswith(".mp4"):
            shutil.copy(result_path, dest_abs_path)
        else:
            ffmpeg_bin = ffmpeg_service.get_ffmpeg_path()
            if ffmpeg_bin:
                import subprocess
                subprocess.run([
                    ffmpeg_bin, "-y", "-i", result_path,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                    dest_abs_path
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                shutil.copy(result_path, dest_abs_path)

        local_url = f"/generated/projects/{project_id}/videos/{local_video_filename}"
        thumbnail_url = image_url if is_i2v else "https://images.unsplash.com/photo-1519501025264-65ba15a82390?auto=format&fit=crop&w=800&q=80"

        result = {
            "job_id": job_id,
            "status": "completed",
            "progress": 100.0,
            "current_step": steps or 25,
            "total_steps": steps or 25,
            "eta_seconds": 0,
            "video_url": local_url,
            "thumbnail_url": thumbnail_url,
            "is_mock": False,
            "provider_badge": f"AI: HuggingFace Space ({self.space_id})"
        }

        if progress_callback:
            await progress_callback(result)

        return result


hf_space_provider = HuggingFaceSpaceProvider()
