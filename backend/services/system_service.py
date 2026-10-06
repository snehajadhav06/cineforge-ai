import os
import psutil
import platform
import httpx
from dotenv import load_dotenv
from backend.services.ffmpeg_service import ffmpeg_service

load_dotenv()

MODE = os.getenv("MODE", "mock")
COMFYUI_URL = os.getenv("COMFYUI_URL", "http://127.0.0.1:8188")


class SystemService:
    @staticmethod
    def check_comfyui_connection(url: str = COMFYUI_URL) -> bool:
        try:
            with httpx.Client(timeout=2.0) as client:
                res = client.get(f"{url.rstrip('/')}/system_stats")
                return res.status_code == 200
        except Exception:
            return False

    @staticmethod
    def get_hardware_info() -> dict:
        cpu_name = platform.processor() or "Generic Processor"
        cpu_cores = psutil.cpu_count(logical=True) or 4
        cpu_usage = psutil.cpu_percent(interval=0.1)

        mem = psutil.virtual_memory()
        ram_total = round(mem.total / (1024 ** 3), 2)
        ram_used = round(mem.used / (1024 ** 3), 2)

        gpu_name = None
        vram_total = None
        vram_used = None
        cuda_available = False

        try:
            import torch
            if torch.cuda.is_available():
                cuda_available = True
                gpu_name = torch.cuda.get_device_name(0)
                vram_total = round(torch.cuda.get_device_properties(0).total_memory / (1024 ** 3), 2)
                vram_used = round(torch.cuda.memory_allocated(0) / (1024 ** 3), 2)
        except Exception:
            pass

        comfy_connected = SystemService.check_comfyui_connection(COMFYUI_URL)
        ffmpeg_available = ffmpeg_service.is_ffmpeg_installed()

        return {
            "mode": MODE,
            "comfyui_connected": comfy_connected,
            "comfyui_url": COMFYUI_URL,
            "cpu_name": cpu_name,
            "cpu_cores": cpu_cores,
            "cpu_usage_percent": cpu_usage,
            "ram_total_gb": ram_total,
            "ram_used_gb": ram_used,
            "gpu_name": gpu_name,
            "vram_total_gb": vram_total,
            "vram_used_gb": vram_used,
            "cuda_available": cuda_available,
            "ffmpeg_installed": ffmpeg_available,
        }


system_service = SystemService()
