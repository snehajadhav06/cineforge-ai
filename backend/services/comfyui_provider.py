import os
import json
import asyncio
import httpx
import shutil
import base64
import tempfile
import logging
from backend.services.video_provider import VideoProvider
from backend.services.storage_service import storage_service

logger = logging.getLogger("cineforge.comfyui_provider")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
WORKFLOW_DIR = os.path.join(BASE_DIR, "comfyui", "workflows")


class ComfyUIProvider(VideoProvider):
    def __init__(self, comfyui_url: str = None):
        self.comfyui_url = (comfyui_url or os.getenv("COMFYUI_URL", "http://127.0.0.1:8188")).rstrip("/")

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(f"{self.comfyui_url}/system_stats")
                return res.status_code == 200
        except Exception:
            return False

    async def upload_image(self, image_data_or_path: str) -> str:
        """Uploads a reference image to ComfyUI server via POST /upload/image"""
        if not image_data_or_path:
            return None

        filename = f"ref_{int(asyncio.get_event_loop().time()*1000)}.png"
        img_bytes = None

        if image_data_or_path.startswith("data:image"):
            _, encoded = image_data_or_path.split(",", 1)
            img_bytes = base64.b64decode(encoded)
        elif os.path.exists(image_data_or_path):
            with open(image_data_or_path, "rb") as f:
                img_bytes = f.read()

        if not img_bytes:
            return None

        files = {"image": (filename, img_bytes, "image/png")}
        data = {"overwrite": "true"}

        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(f"{self.comfyui_url}/upload/image", files=files, data=data)
            if res.status_code == 200:
                uploaded = res.json()
                return uploaded.get("name", filename)
            else:
                raise RuntimeError(f"ComfyUI image upload failed ({res.status_code}): {res.text}")

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
        # Check connection first
        if not await self.is_available():
            err_msg = f"ComfyUI server not reachable at {self.comfyui_url}"
            logger.error(err_msg)
            raise RuntimeError(err_msg)

        total_steps = steps or 25
        # LTX-Video frames formula: duration * fps + 1
        frames = int(duration * fps) + 1

        is_i2v = bool(image_url)
        uploaded_image_name = None

        if is_i2v:
            try:
                uploaded_image_name = await self.upload_image(image_url)
            except Exception as e:
                err_msg = f"Failed to upload reference image to ComfyUI: {e}"
                logger.error(err_msg)
                raise RuntimeError(err_msg)

        wf_filename = "ltxv_i2v.json" if is_i2v else "ltxv_t2v.json"
        wf_path = os.path.join(WORKFLOW_DIR, wf_filename)

        if not os.path.exists(wf_path):
            err_msg = f"ComfyUI workflow file missing: {wf_filename}"
            logger.error(err_msg)
            raise RuntimeError(err_msg)

        with open(wf_path, "r", encoding="utf-8") as f:
            wf_str = f.read()

        # Substitute workflow placeholders
        wf_str = wf_str.replace("{{PROMPT}}", json.dumps(prompt)[1:-1])
        wf_str = wf_str.replace("{{NEGATIVE_PROMPT}}", json.dumps(negative_prompt or "")[1:-1])
        wf_str = wf_str.replace('"{{SEED}}"', str(seed)).replace("{{SEED}}", str(seed))
        wf_str = wf_str.replace('"{{STEPS}}"', str(steps)).replace("{{STEPS}}", str(steps))
        wf_str = wf_str.replace('"{{CFG}}"', str(guidance)).replace("{{CFG}}", str(guidance))
        wf_str = wf_str.replace('"{{WIDTH}}"', str(width)).replace("{{WIDTH}}", str(width))
        wf_str = wf_str.replace('"{{HEIGHT}}"', str(height)).replace("{{HEIGHT}}", str(height))
        wf_str = wf_str.replace('"{{FPS}}"', str(fps)).replace("{{FPS}}", str(fps))
        wf_str = wf_str.replace('"{{FRAMES}}"', str(frames)).replace("{{FRAMES}}", str(frames))
        if is_i2v and uploaded_image_name:
            wf_str = wf_str.replace("{{IMAGE_NAME}}", json.dumps(uploaded_image_name)[1:-1])

        try:
            workflow = json.loads(wf_str)
        except Exception as e:
            raise RuntimeError(f"Invalid workflow JSON template: {e}")

        # Submit prompt payload to ComfyUI
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.post(f"{self.comfyui_url}/prompt", json={"prompt": workflow})
            if res.status_code != 200:
                raise RuntimeError(f"ComfyUI prompt submission failed ({res.status_code}): {res.text}")
            prompt_id = res.json().get("prompt_id")

        if not prompt_id:
            raise RuntimeError("ComfyUI did not return a valid prompt_id")

        # Track execution via polling /history/{prompt_id}
        completed = False
        output_file_info = None

        for step in range(1, total_steps + 1):
            await asyncio.sleep(0.6)
            progress_pct = round((step / total_steps) * 100.0, 1)
            eta = max(0, int((total_steps - step) * 0.6))

            if progress_callback:
                await progress_callback({
                    "job_id": job_id,
                    "status": "processing",
                    "progress": progress_pct,
                    "current_step": step,
                    "total_steps": total_steps,
                    "eta_seconds": eta,
                    "message": f"ComfyUI Sampling ({step}/{total_steps})"
                })

            # Check history
            async with httpx.AsyncClient(timeout=5.0) as client:
                hist_res = await client.get(f"{self.comfyui_url}/history/{prompt_id}")
                if hist_res.status_code == 200:
                    hist_data = hist_res.json()
                    if prompt_id in hist_data:
                        completed = True
                        outputs = hist_data[prompt_id].get("outputs", {})
                        for node_id, node_out in outputs.items():
                            if "gifs" in node_out:
                                output_file_info = node_out["gifs"][0]
                                break
                            elif "images" in node_out:
                                output_file_info = node_out["images"][0]
                                break
                        break

        if not completed or not output_file_info:
            # Poll once more
            await asyncio.sleep(2.0)
            async with httpx.AsyncClient(timeout=5.0) as client:
                hist_res = await client.get(f"{self.comfyui_url}/history/{prompt_id}")
                if hist_res.status_code == 200 and prompt_id in hist_res.json():
                    outputs = hist_res.json()[prompt_id].get("outputs", {})
                    for node_id, node_out in outputs.items():
                        if "gifs" in node_out or "images" in node_out:
                            output_file_info = (node_out.get("gifs") or node_out.get("images"))[0]
                            break

        if not output_file_info:
            raise RuntimeError(f"ComfyUI execution failed or timed out for prompt_id: {prompt_id}")

        # Download generated video file from ComfyUI /view
        filename = output_file_info.get("filename")
        subfolder = output_file_info.get("subfolder", "")
        file_type = output_file_info.get("type", "output")

        view_url = f"{self.comfyui_url}/view?filename={filename}&subfolder={subfolder}&type={file_type}"

        project_id = "default"
        dirs = storage_service.get_project_dirs(project_id)
        local_video_filename = f"{job_id}.mp4"
        dest_abs_path = os.path.join(dirs["videos"], local_video_filename)

        async with httpx.AsyncClient(timeout=30.0) as client:
            v_res = await client.get(view_url)
            if v_res.status_code == 200 and len(v_res.content) > 0:
                with open(dest_abs_path, "wb") as f:
                    f.write(v_res.content)
            else:
                raise RuntimeError(f"Failed to download video from ComfyUI /view: HTTP {v_res.status_code}")

        local_url = f"/generated/projects/{project_id}/videos/{local_video_filename}"
        thumbnail_url = image_url if is_i2v else "https://images.unsplash.com/photo-1519501025264-65ba15a82390?auto=format&fit=crop&w=800&q=80"

        result = {
            "job_id": job_id,
            "status": "completed",
            "progress": 100.0,
            "current_step": total_steps,
            "total_steps": total_steps,
            "eta_seconds": 0,
            "video_url": local_url,
            "thumbnail_url": thumbnail_url,
            "is_mock": False
        }

        if progress_callback:
            await progress_callback(result)

        return result


comfyui_provider = ComfyUIProvider()
