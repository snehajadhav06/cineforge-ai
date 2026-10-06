import os
import re
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
DEFAULT_NEGATIVE_PROMPT = "worst quality, inconsistent motion, blurry, jittery, distorted"


def snap_to_multiple_of_32(val: int) -> int:
    return max(32, int(round(val / 32.0)) * 32)


def find_video_path_in_obj(obj) -> str:
    """Recursively extract local MP4/video filepath string from Gradio return objects"""
    if isinstance(obj, str):
        if obj.endswith((".mp4", ".webm", ".avi", ".mkv")) or os.path.exists(obj):
            return obj
    elif isinstance(obj, dict):
        if "path" in obj and isinstance(obj["path"], str) and os.path.exists(obj["path"]):
            return obj["path"]
        for key, val in obj.items():
            res = find_video_path_in_obj(val)
            if res:
                return res
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            res = find_video_path_in_obj(item)
            if res:
                return res
    return None


class HuggingFaceSpaceProvider(VideoProvider):
    def __init__(self, space_id: str = None, token: str = None):
        self.space_id = space_id or os.getenv("HF_SPACE_ID", "Lightricks/ltx-video-distilled")
        self.token = token or os.getenv("HF_TOKEN", None) or None
        self._client = None
        self._logged_api = False
        self._spaces_config = self._load_spaces_config()

    def _load_spaces_config(self) -> list:
        if os.path.exists(CONFIG_SPACES_PATH):
            try:
                with open(CONFIG_SPACES_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to read spaces.json: {e}")
        return []

    def get_client(self):
        """Reuse one Gradio Client instance per provider instance (Requirement 4)"""
        if self._client is None:
            from gradio_client import Client
            self._client = Client(self.space_id, token=self.token)
            if not self._logged_api:
                try:
                    api_info = self._client.view_api(return_format="dict")
                    logger.info(f"Connected to HF Space '{self.space_id}' - API Signature:\n{json.dumps(api_info, indent=2)}")
                except Exception as e:
                    logger.info(f"Connected to HF Space '{self.space_id}': {e}")
                self._logged_api = True
        return self._client

    async def is_available(self) -> bool:
        if not self.space_id:
            return False
        try:
            client = self.get_client()
            api_info = client.view_api(return_format="dict")
            return bool(api_info)
        except Exception as e:
            logger.warning(f"HuggingFace Space '{self.space_id}' not reachable: {e}")
            return False

    def get_image_dimensions(self, handle_img_obj) -> tuple[int, int]:
        """
        Call /handle_image_upload_for_dims helper endpoint (Requirement 2)
        """
        try:
            client = self.get_client()
            res = client.predict(handle_img_obj, 512, 704, api_name="/handle_image_upload_for_dims")
            if isinstance(res, (list, tuple)) and len(res) >= 2:
                raw_h, raw_w = float(res[0]), float(res[1])
                h_32 = snap_to_multiple_of_32(int(raw_h))
                w_32 = snap_to_multiple_of_32(int(raw_w))
                logger.info(f"Helper /handle_image_upload_for_dims returned raw {raw_h}x{raw_w} -> snapped to {h_32}x{w_32}")
                return h_32, w_32
        except Exception as e:
            logger.warning(f"Failed to query /handle_image_upload_for_dims: {e}")
        return 512, 704

    async def generate_video(
        self,
        prompt: str,
        negative_prompt: str,
        image_url: str = None,
        duration: int = 5,
        width: int = 704,
        height: int = 512,
        fps: int = 24,
        seed: int = 42,
        is_fixed_seed: bool = False,
        steps: int = 25,
        guidance: float = 6.5,
        job_id: str = None,
        progress_callback = None
    ) -> dict:
        try:
            from gradio_client import handle_file
        except ImportError:
            err_msg = "gradio_client python package is not installed."
            logger.error(err_msg)
            raise RuntimeError(err_msg)

        client = self.get_client()
        is_i2v = bool(image_url)

        # 1. Process Reference Image Argument (Requirement 1)
        abs_img_path = None
        handle_img_obj = None
        temp_img_file = None

        if is_i2v and image_url:
            if image_url.startswith("data:image"):
                header, encoded = image_url.split(",", 1)
                img_bytes = base64.b64decode(encoded)
                ext = ".png" if "png" in header else ".jpg"
                temp_img_file = tempfile.NamedTemporaryFile("wb", delete=False, suffix=ext)
                temp_img_file.write(img_bytes)
                temp_img_file.close()
                abs_img_path = os.path.abspath(temp_img_file.name)
            elif os.path.exists(image_url):
                abs_img_path = os.path.abspath(image_url)

            if abs_img_path and os.path.exists(abs_img_path):
                handle_img_obj = handle_file(abs_img_path)
                logger.info(f"Image Argument - Type: {type(handle_img_obj).__name__}, Absolute Path: '{abs_img_path}'")
            else:
                logger.warning(f"Provided image path '{image_url}' could not be resolved.")

        # 2. Dimensions calculation (Requirement 2)
        if is_i2v and handle_img_obj:
            height_ui, width_ui = self.get_image_dimensions(handle_img_obj)
        else:
            height_ui = snap_to_multiple_of_32(height or 512)
            width_ui = snap_to_multiple_of_32(width or 704)

        # 3. Duration clamping to 2s max on first attempt (Requirement 3)
        duration_ui = min(int(duration or 2), 2)
        job_msg = "This Space generates up to ~2 s per clip; use Extend to chain clips."
        logger.info(f"Target duration_ui set to {duration_ui}s (Requested: {duration}s). {job_msg}")

        # 4. Construct exact positional arguments for /image_to_video or /text_to_video (Requirement 4)
        api_name = "/image_to_video" if is_i2v else "/text_to_video"
        neg_prompt_clean = negative_prompt.strip() if (negative_prompt and negative_prompt.strip()) else DEFAULT_NEGATIVE_PROMPT

        args = [
            str(prompt),
            str(neg_prompt_clean),
            handle_img_obj if is_i2v else None,
            None,  # input_video_filepath
            float(height_ui),
            float(width_ui),
            "image-to-video" if is_i2v else "text-to-video",
            float(duration_ui),
            9.0,   # ui_frames_to_use (fixed at Space default 9)
            int(seed),
            not bool(is_fixed_seed),  # randomize_seed (bool)
            1.0 if (guidance == 6.5 or guidance is None) else float(guidance),  # ui_guidance_scale
            True   # improve_texture_flag (bool)
        ]

        logger.info(
            f"Invoking HF Space '{self.space_id}' API '{api_name}' with argument types: "
            f"{[type(a).__name__ for a in args]}"
        )

        if progress_callback:
            await progress_callback({
                "job_id": job_id,
                "status": "processing",
                "progress": 10.0,
                "current_step": 1,
                "total_steps": steps or 25,
                "eta_seconds": 25,
                "message": f"HF Space: {job_msg}"
            })

        # 5. Execute predict call with queue polling (Requirement 5)
        try:
            job = client.submit(*args, api_name=api_name)
            step_count = 1
            while not job.done():
                await asyncio.sleep(1.0)
                step_count += 1
                status = job.status()
                eta = status.eta if hasattr(status, 'eta') and status.eta is not None else max(0, 30 - step_count)
                queue_pos = getattr(status, 'queue_size', None)
                msg = f"HF Space Queue position: {queue_pos}" if queue_pos else "Synthesizing AI video..."

                if progress_callback:
                    await progress_callback({
                        "job_id": job_id,
                        "status": "processing",
                        "progress": min(95.0, round(step_count * 4.0, 1)),
                        "current_step": min(steps or 25, step_count),
                        "total_steps": steps or 25,
                        "eta_seconds": int(eta),
                        "message": msg
                    })

            result_tuple = job.result()
            logger.info(f"Gradio raw return object: {result_tuple}")
        except Exception as err:
            if temp_img_file and os.path.exists(temp_img_file.name):
                try: os.remove(temp_img_file.name)
                except Exception: pass

            err_str = str(err)
            verbatim_error = f"HuggingFace Space '{self.space_id}' ({api_name}) Error: {err_str}"
            logger.error(verbatim_error)
            raise RuntimeError(verbatim_error)

        if temp_img_file and os.path.exists(temp_img_file.name):
            try: os.remove(temp_img_file.name)
            except Exception: pass

        # 6. Parse Gradio output tuple (Requirement 5)
        returned_seed = seed
        if isinstance(result_tuple, (list, tuple)) and len(result_tuple) > 1:
            try: returned_seed = int(result_tuple[1])
            except Exception: pass

        video_path_str = find_video_path_in_obj(result_tuple)

        if not video_path_str or not os.path.exists(video_path_str):
            err_msg = f"HuggingFace Space '{self.space_id}' returned output object without valid video path: {result_tuple}"
            logger.error(err_msg)
            raise RuntimeError(err_msg)

        logger.info(f"Successfully resolved output video path: {video_path_str}")

        # Copy into generated/projects/<id>/videos/<job_id>.mp4
        project_id = "default"
        dirs = storage_service.get_project_dirs(project_id)
        local_video_filename = f"{job_id}.mp4"
        dest_abs_path = os.path.join(dirs["videos"], local_video_filename)

        ffmpeg_bin = ffmpeg_service.get_ffmpeg_path()
        if ffmpeg_bin:
            import subprocess
            subprocess.run([
                ffmpeg_bin, "-y", "-i", video_path_str,
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                dest_abs_path
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            shutil.copy(video_path_str, dest_abs_path)

        local_url = f"/generated/projects/{project_id}/videos/{local_video_filename}"

        # Generate thumbnail image
        thumb_filename = f"{job_id}.jpg"
        thumb_abs_path = os.path.join(dirs["thumbnails"], thumb_filename)
        if ffmpeg_service.extract_thumbnail(dest_abs_path, thumb_abs_path):
            thumbnail_url = f"/generated/projects/{project_id}/thumbnails/{thumb_filename}"
        else:
            thumbnail_url = image_url if is_i2v else "https://images.unsplash.com/photo-1519501025264-65ba15a82390?auto=format&fit=crop&w=800&q=80"

        provider_badge = f"hf-space:{self.space_id}"

        result = {
            "job_id": job_id,
            "status": "completed",
            "progress": 100.0,
            "current_step": steps or 25,
            "total_steps": steps or 25,
            "eta_seconds": 0,
            "video_url": local_url,
            "thumbnail_url": thumbnail_url,
            "seed": returned_seed,
            "is_mock": False,
            "provider": provider_badge,
            "message": job_msg
        }

        if progress_callback:
            await progress_callback(result)

        return result

    async def extend_video(
        self,
        prev_video_abs_path: str,
        prompt: str,
        negative_prompt: str,
        project_id: str = "default",
        job_id: str = None,
        progress_callback = None
    ) -> dict:
        if not os.path.exists(prev_video_abs_path):
            raise RuntimeError(f"Previous video file for Extend not found: {prev_video_abs_path}")

        dirs = storage_service.get_project_dirs(project_id)
        last_frame_path = os.path.join(dirs["images"], f"ext_frame_{job_id}.png")

        # 1. Extract last frame from previous clip
        if not ffmpeg_service.extract_last_frame(prev_video_abs_path, last_frame_path):
            raise RuntimeError("Failed to extract end frame from previous video for extension.")

        # 2. Synthesize new ~2s continuation clip
        new_clip_job_id = f"{job_id}_clip2"
        res_new = await self.generate_video(
            prompt=prompt or "Seamless camera continuation movement",
            negative_prompt=negative_prompt or "",
            image_url=last_frame_path,
            duration=2,
            width=704,
            height=512,
            fps=24,
            job_id=new_clip_job_id,
            progress_callback=progress_callback
        )

        new_clip_rel_url = res_new.get("video_url")
        new_clip_abs_path = os.path.join(BASE_DIR, new_clip_rel_url.lstrip("/"))

        # 3. Concatenate clips with FFmpeg
        final_filename = f"{job_id}.mp4"
        final_abs_path = os.path.join(dirs["videos"], final_filename)

        if not ffmpeg_service.concat_videos([prev_video_abs_path, new_clip_abs_path], final_abs_path):
            raise RuntimeError("FFmpeg concatenation of video extension clips failed.")

        if os.path.exists(last_frame_path):
            try: os.remove(last_frame_path)
            except Exception: pass

        local_url = f"/generated/projects/{project_id}/videos/{final_filename}"
        thumb_filename = f"{job_id}.jpg"
        thumb_abs_path = os.path.join(dirs["thumbnails"], thumb_filename)
        ffmpeg_service.extract_thumbnail(final_abs_path, thumb_abs_path)
        thumbnail_url = f"/generated/projects/{project_id}/thumbnails/{thumb_filename}"

        warn_msg = "Chained video clips with HuggingFace Space. Note: Long video chains may exhibit slight quality or motion drift."

        result = {
            "job_id": job_id,
            "status": "completed",
            "progress": 100.0,
            "video_url": local_url,
            "thumbnail_url": thumbnail_url,
            "is_mock": False,
            "provider": f"hf-space:{self.space_id}",
            "message": warn_msg
        }

        if progress_callback:
            await progress_callback(result)

        return result


hf_space_provider = HuggingFaceSpaceProvider()
