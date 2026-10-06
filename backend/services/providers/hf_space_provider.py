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
        """Reuse one Gradio Client per provider instance (Requirement 4)"""
        if self._client is None:
            from gradio_client import Client
            self._client = Client(self.space_id, token=self.token)
            if not self._logged_api:
                try:
                    api_info = self._client.view_api(return_format="dict")
                    logger.info(f"Connected to HF Space '{self.space_id}' API Signature:\n{json.dumps(api_info, indent=2)}")
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

    def select_endpoint(self, is_i2v: bool) -> str:
        space_cfg = None
        for item in self._spaces_config:
            if item.get("id") == self.space_id:
                space_cfg = item
                break

        if space_cfg and "endpoints" in space_cfg:
            ep = space_cfg["endpoints"].get("i2v" if is_i2v else "t2v")
            if ep:
                return ep

        return "/image_to_video" if is_i2v else "/text_to_video"

    def _validate_and_coerce_type(self, p_name: str, val: any, p_python_type: str, spec: dict) -> any:
        if val is None:
            return None

        # Check Literal / enum options
        enum_options = spec.get("type", {}).get("enum")
        if enum_options and val not in enum_options:
            raise RuntimeError(f"Parameter '{p_name}' value '{val}' is invalid. Allowed options: {enum_options}")

        p_type_str = str(spec.get("type", "")).lower()

        if p_python_type == "bool" or "boolean" in p_type_str:
            if isinstance(val, str):
                if val.lower() in ["true", "1"]: return True
                if val.lower() in ["false", "0"]: return False
            return bool(val)
        elif p_python_type == "int" or "integer" in p_type_str:
            try:
                return int(val)
            except Exception:
                raise RuntimeError(f"Parameter '{p_name}' expected int, got '{type(val).__name__}': {val}")
        elif p_python_type == "float" or "number" in p_type_str:
            try:
                return float(val)
            except Exception:
                raise RuntimeError(f"Parameter '{p_name}' expected float, got '{type(val).__name__}': {val}")
        elif p_python_type == "str" or "string" in p_type_str:
            if not isinstance(val, (str, type(None))):
                return str(val)

        return val

    def map_and_validate_parameters(
        self,
        client,
        endpoint_name: str,
        prompt: str,
        negative_prompt: str,
        image_path: str = None,
        duration: int = 5,
        width: int = 704,
        height: int = 512,
        fps: int = 24,
        seed: int = 42,
        is_fixed_seed: bool = False,
        steps: int = 25,
        guidance: float = 6.5,
        is_i2v: bool = False
    ) -> tuple[list, dict, list]:
        from gradio_client import handle_file

        api_dict = client.view_api(return_format="dict")
        named = api_dict.get("named_endpoints", {})
        unnamed = api_dict.get("unnamed_endpoints", {})
        all_endpoints = {**named, **unnamed}

        if endpoint_name not in all_endpoints:
            endpoint_name = list(all_endpoints.keys())[0]

        param_specs = all_endpoints[endpoint_name].get("parameters", [])

        args = []
        mapped_log = {}
        clamped_notes = []

        space_cfg = None
        for item in self._spaces_config:
            if item.get("id") == self.space_id:
                space_cfg = item
                break

        param_map_table = space_cfg.get("parameter_mapping", {}) if space_cfg else {}

        handle_img = handle_file(image_path) if (is_i2v and image_path and os.path.exists(image_path)) else None

        for spec in param_specs:
            p_name = spec.get("parameter_name") or spec.get("name") or ""
            p_default = spec.get("parameter_default", spec.get("default", None))
            p_type_info = spec.get("type", {})
            p_python_type = spec.get("python_type", {}).get("type", "")

            val = None

            # Explicit parameter_name mapping (Requirement 1)
            if p_name == "prompt":
                val = prompt
            elif p_name == "negative_prompt":
                val = negative_prompt or ""
            elif p_name == "input_image_filepath":
                val = handle_img if is_i2v else None
            elif p_name == "input_video_filepath":
                val = None
            elif p_name == "height_ui":
                val = height
            elif p_name == "width_ui":
                val = width
            elif p_name == "mode":
                val = "image-to-video" if is_i2v else "text-to-video"
            elif p_name == "duration_ui":
                val = duration
            elif p_name == "ui_frames_to_use":
                # Leave at Space's parameter_default (9); never derive from duration
                val = p_default if p_default is not None else 9
            elif p_name == "seed_ui":
                val = seed
            elif p_name == "randomize_seed":
                val = not bool(is_fixed_seed)
            elif p_name == "ui_guidance_scale":
                # Distilled model default is 1.0 unless user changed it from default 6.5
                val = 1.0 if (guidance == 6.5 or guidance is None) else float(guidance)
            elif p_name == "improve_texture_flag":
                val = True
            else:
                val = p_default
                logger.info(f"Parameter '{p_name}' has no explicit mapping rule. Using parameter_default: {p_default}")

            # Numeric slider range bounds check
            if isinstance(p_type_info, dict) and "description" in p_type_info:
                desc = p_type_info["description"]
                m = re.search(r"between\s+([\d\.]+)\s+and\s+([\d\.]+)", desc)
                if m and isinstance(val, (int, float)):
                    min_b = float(m.group(1))
                    max_b = float(m.group(2))
                    if val < min_b:
                        logger.warning(f"Parameter '{p_name}' value {val} is below minimum {min_b}. Clamping to {min_b}")
                        val = type(val)(min_b)
                    elif val > max_b:
                        logger.warning(f"Parameter '{p_name}' value {val} exceeds maximum {max_b}. Clamping to {max_b}")
                        if p_name == "duration_ui":
                            clamped_notes.append(f"Duration clamped to Space maximum ({max_b}s). Use 'Extend (+5s)' to generate longer clips.")
                        val = type(val)(max_b)

            # Validate and coerce type (Requirement 2)
            val = self._validate_and_coerce_type(p_name, val, p_python_type, spec)

            args.append(val)
            mapped_log[p_name] = val

        return args, mapped_log, clamped_notes

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
        is_fixed_seed: bool = False,
        steps: int = 25,
        guidance: float = 6.5,
        job_id: str = None,
        progress_callback = None
    ) -> dict:
        try:
            client = self.get_client()
        except Exception as e:
            err_msg = f"Failed to connect to HuggingFace Space '{self.space_id}': {e}"
            logger.error(err_msg)
            raise RuntimeError(err_msg)

        is_i2v = bool(image_url)
        temp_img_file = None
        local_img_path = None

        if is_i2v and image_url:
            if image_url.startswith("data:image"):
                header, encoded = image_url.split(",", 1)
                img_bytes = base64.b64decode(encoded)
                ext = ".png" if "png" in header else ".jpg"
                temp_img_file = tempfile.NamedTemporaryFile("wb", delete=False, suffix=ext)
                temp_img_file.write(img_bytes)
                temp_img_file.close()
                local_img_path = temp_img_file.name
            elif os.path.exists(image_url):
                local_img_path = image_url

        endpoint_name = self.select_endpoint(is_i2v)
        args, mapped_log, clamped_notes = self.map_and_validate_parameters(
            client=client,
            endpoint_name=endpoint_name,
            prompt=prompt,
            negative_prompt=negative_prompt,
            image_path=local_img_path,
            duration=duration,
            width=width,
            height=height,
            fps=fps,
            seed=seed,
            is_fixed_seed=is_fixed_seed,
            steps=steps,
            guidance=guidance,
            is_i2v=is_i2v
        )

        logger.info(f"Submitting to HF Space '{self.space_id}' endpoint '{endpoint_name}' with parameter values:\n{json.dumps({k: str(v) for k, v in mapped_log.items()}, indent=2)}")

        if progress_callback:
            msg = f"Connecting to HuggingFace Space: {self.space_id}..."
            if clamped_notes:
                msg += f" ({clamped_notes[0]})"
            await progress_callback({
                "job_id": job_id,
                "status": "processing",
                "progress": 10.0,
                "current_step": 1,
                "total_steps": steps or 25,
                "eta_seconds": 30,
                "message": msg
            })

        # Submit to Gradio queue with automated range error retry handling (Requirement 3)
        result_tuple = None
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
        except Exception as err:
            err_str = str(err)
            # Range error parsing & one-time retry
            m_range = re.search(r"Value\s+([\d\.]+)\s+is\s+(less|greater)\s+than\s+(minimum|maximum)\s+value\s+([\d\.]+)", err_str)
            if m_range:
                bad_val = float(m_range.group(1))
                bound_val = float(m_range.group(4))
                logger.warning(f"Gradio Range Error: Value {bad_val} out of bounds. Retrying once with clamped value {bound_val}...")
                
                # Update failing argument in positional list
                for i in range(len(args)):
                    if args[i] == bad_val or (isinstance(args[i], (int, float)) and abs(args[i] - bad_val) < 0.01):
                        args[i] = type(args[i])(bound_val) if isinstance(args[i], int) else bound_val

                # Single retry
                retry_job = client.submit(*args, api_name=endpoint_name)
                while not retry_job.done():
                    await asyncio.sleep(1.0)
                result_tuple = retry_job.result()
            else:
                # Verbatim error surfacing (Requirement 5)
                if temp_img_file and os.path.exists(temp_img_file.name):
                    try: os.remove(temp_img_file.name)
                    except Exception: pass
                logger.error(f"HuggingFace Space '{self.space_id}' verbatim error: {err_str}")
                raise RuntimeError(err_str)

        if temp_img_file and os.path.exists(temp_img_file.name):
            try: os.remove(temp_img_file.name)
            except Exception: pass

        # Parse Gradio result tuple
        if isinstance(result_tuple, (list, tuple)) and len(result_tuple) > 0:
            result_path = result_tuple[0]
        else:
            result_path = result_tuple

        if isinstance(result_path, dict) and "path" in result_path:
            result_path = result_path["path"]

        if not result_path or not os.path.exists(str(result_path)):
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
                    ffmpeg_bin, "-y", "-i", str(result_path),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                    dest_abs_path
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                shutil.copy(result_path, dest_abs_path)

        local_url = f"/generated/projects/{project_id}/videos/{local_video_filename}"
        thumbnail_url = image_url if is_i2v else "https://images.unsplash.com/photo-1519501025264-65ba15a82390?auto=format&fit=crop&w=800&q=80"

        # Requirement 5: Provider badge hf-space:Lightricks/ltx-video-distilled
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
            "is_mock": False,
            "provider": provider_badge
        }

        if progress_callback:
            await progress_callback(result)

        return result


hf_space_provider = HuggingFaceSpaceProvider()
