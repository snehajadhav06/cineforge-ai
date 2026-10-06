import os
import httpx
from dotenv import load_dotenv

load_dotenv()
COMFYUI_URL = os.getenv("COMFYUI_URL", "http://127.0.0.1:8188")


class ComfyUIService:
    def __init__(self, url: str = COMFYUI_URL):
        self.url = url.rstrip("/")

    async def is_server_online(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(f"{self.url}/system_stats")
                return res.status_code == 200
        except Exception:
            return False

    async def queue_prompt(self, workflow_prompt: dict) -> str:
        payload = {"prompt": workflow_prompt}
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(f"{self.url}/prompt", json=payload)
            if res.status_code == 200:
                return res.json().get("prompt_id", "")
            else:
                raise RuntimeError(f"ComfyUI rejected prompt: {res.text}")


comfyui_service = ComfyUIService()
