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
        self.space_id = space_id or os.getenv("HF_SPACE_ID", "Lightricks/ltx-video-distilled")
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

    async def is_available(self) -> bool:
        if not self.space_id:
            return False
        try:
            from gradio_client import Client
            client = Client(self.space_id, token=self.token)
            api_info = client.view_api(return_format="dict")
            return bool(api_info)
        except Exception as e:
            logger.warning(f"HuggingFace Space '{self.space_id}' not reachable: {e}")
            return False

    def inspect_and_map_endpoint(self, client, is_i2v: bool) -> tuple[str, list]:
        """
        Inspect client.view_api(return_format="dict") and find target endpoint parameter specs.
        """
        api_dict = client.view_api(return_format="dict")
        named = api_dict.get("named_endpoints", {})
        unnamed = api_dict.get("unnamed_endpoints", {})

        all_endpoints = {**named, **unnamed}
        if not all_endpoints:
            raise RuntimeError(f"HuggingFace Space '{self.space_id}' has no active API endpoints.")

        chosen_endpoint = None
        if is_i2v:
            for candidate in ["/image_to_video", "/i2v", "/generate", "/predict"]:
                if candidate in all_endpoints:
                    chosen_endpoint = candidate
                    break
        else:
            for candidate in ["/text_to_video", "/t2v", "/generate", "/predict"]:
                if candidate in all_endpoints:
                    chosen_endpoint = candidate
                    break

        if not chosen_endpoint:
            chosen_endpoint = list(all_endpoints.keys())[0]

        endpoint_info = all_endpoints[chosen_endpoint]
        parameters = endpoint_info.get("parameters", [])

        logger.info(f"Selected HF Space '{self.space_id}' endpoint '{chosen_endpoint}' with {len(parameters)} parameters.")
        return chosen_endpoint, parameters

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
            err_msg = str(e)
            if "quota" in err_msg.lower():
                err_msg = f"ZeroGPU quota exceeded for Space '{self.space_id}': {e}"
            elif "sleeping" in err_msg.lower() or "building" in err_msg.lower():
                err_msg = f"HuggingFace Space '{self.space_id}' is sleeping or building."
            else:
                err_msg = f"Failed to connect to HuggingFace Space '{self.space_id}': {e}"
            logger.error(err_msg)
            raise RuntimeError(err_msg)

        is_i2v = bool(image_url)
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

        endpoint_name, param_specs = self.inspect_and_map_endpoint(client, is_i2v)

        args = []
        mapped_log = {}
        unmapped = []

        for spec in param_specs:
            p_name = str(spec.get("parameter_name") or spec.get("name") or "").lower()
            p_label = str(spec.get("label", "")).lower()
            p_type = str(spec.get("type", "")).lower()

            combined = f"{p_name} {p_label}"

            if "frames_to_use" in combined or "frames to use" in combined or "ui_frames_to_use" in combined:
                # Slider minimum is 9 for LTX-Video distilled
                num_frames = max(9, int(duration * fps + 1))
                args.append(num_frames)
                mapped_log[p_name or p_label] = f"num_frames={num_frames}"
            elif "duration" in combined:
                args.append(duration)
                mapped_log[p_name or p_label] = f"duration={duration}"
            elif "prompt" in combined and "neg" not in combined:
                args.append(prompt)
                mapped_log[p_name or p_label] = "prompt"
            elif "neg" in combined or "negative" in combined:
                args.append(negative_prompt or "")
                mapped_log[p_name or p_label] = "negative_prompt"
            elif ("image" in combined or "img" in combined or "file" in p_type) and is_i2v and "video" not in combined:
                args.append(handle_img)
                mapped_log[p_name or p_label] = "image"
            elif "video" in combined and "input" in combined:
                args.append(None)
                mapped_log[p_name or p_label] = "input_video=None"
            elif "width" in combined:
                args.append(width)
                mapped_log[p_name or p_label] = f"width={width}"
            elif "height" in combined:
                args.append(height)
                mapped_log[p_name or p_label] = f"height={height}"
            elif "mode" in combined or "task" in combined:
                mode_str = "image-to-video" if is_i2v else "text-to-video"
                args.append(mode_str)
                mapped_log[p_name or p_label] = f"mode={mode_str}"
            elif "randomize" in combined:
                args.append(False)
                mapped_log[p_name or p_label] = "randomize_seed=False"
            elif "texture" in combined:
                args.append(True)
                mapped_log[p_name or p_label] = "improve_texture=True"
            elif "seed" in combined:
                args.append(seed)
                mapped_log[p_name or p_label] = f"seed={seed}"
            elif "step" in combined:
                args.append(steps or 25)
                mapped_log[p_name or p_label] = f"steps={steps}"
            elif "cfg" in combined or "guidance" in combined:
                args.append(guidance or 6.5)
                mapped_log[p_name or p_label] = f"guidance={guidance}"
            else:
                default_val = spec.get("parameter_default", spec.get("default", None))
                args.append(default_val)
                mapped_log[p_name or p_label] = f"default={default_val}"

        logger.info(f"Mapped parameter inputs for endpoint '{endpoint_name}': {mapped_log}")

        mapped_values = list(mapped_log.values())
        if "prompt" not in mapped_values:
            unmapped.append("prompt")
        if is_i2v and "image" not in mapped_values:
            unmapped.append("image")

        if unmapped:
            err_msg = f"HuggingFace Space '{self.space_id}' endpoint '{endpoint_name}' signature could not map required parameters: {unmapped}"
            logger.error(err_msg)
            raise RuntimeError(err_msg)

        try:
            job = client.submit(*args, api_name=endpoint_name)

            step_count = 1
            while not job.done():
                await asyncio.sleep(1.0)
                step_count += 1
                status = job.status()
                eta = status.eta if hasattr(status, 'eta') and status.eta is not None else max(0, 45 - step_count)
                queue_pos = getattr(status, 'queue_size', None)
                msg = f"HF Space Queue position: {queue_pos}" if queue_pos else "HF Space synthesizing AI video..."

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

            result_tuple = job.result()
            # Gradio returns (video_dict_or_path, seed)
            if isinstance(result_tuple, (list, tuple)) and len(result_tuple) > 0:
                result_path = result_tuple[0]
            else:
                result_path = result_tuple

            if isinstance(result_path, dict) and "path" in result_path:
                result_path = result_path["path"]

        except Exception as e:
            if temp_img_file and os.path.exists(temp_img_file.name):
                try: os.remove(temp_img_file.name)
                except Exception: pass
            err_str = str(e)
            if "quota" in err_str.lower() or "zerogpu" in err_str.lower():
                err_msg = f"ZeroGPU Quota Exceeded on HuggingFace Space '{self.space_id}': {e}"
            elif "timeout" in err_str.lower() or "queue" in err_str.lower():
                err_msg = f"Queue Timeout on HuggingFace Space '{self.space_id}': {e}"
            elif "sleeping" in err_str.lower():
                err_msg = f"HuggingFace Space '{self.space_id}' is sleeping. Please wake it up on HF."
            else:
                err_msg = f"HuggingFace Space '{self.space_id}' API error: {e}"
            logger.error(err_msg)
            raise RuntimeError(err_msg)

        if temp_img_file and os.path.exists(temp_img_file.name):
            try: os.remove(temp_img_file.name)
            except Exception: pass

        if not result_path or not os.path.exists(result_path):
            err_msg = f"HuggingFace Space '{self.space_id}' returned no output video file."
            logger.error(err_msg)
            raise RuntimeError(err_msg)

        project_id = "default"
        dirs = storage_service.get_project_dirs(project_id)
        local_video_filename = f"{job_id}.mp4"
        dest_abs_path = os.path.join(dirs["videos"], local_video_filename)

        if str(result_path).endswith(".mp4"):
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
            "provider": f"hf-space:{self.space_id}"
        }

        if progress_callback:
            await progress_callback(result)

        return result


hf_space_provider = HuggingFaceSpaceProvider()
