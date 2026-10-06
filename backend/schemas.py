from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class GenerationRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = "blurry, low quality, static, distorted faces, compression artifacts"
    mode: Optional[str] = "text-to-video"
    reference_image_url: Optional[str] = None
    model_id: Optional[str] = "ltx-video"
    duration: Optional[int] = 5
    aspect_ratio: Optional[str] = "16:9"
    resolution: Optional[str] = "720p"
    fps: Optional[int] = 24
    seed: Optional[int] = None
    is_fixed_seed: Optional[bool] = False
    steps: Optional[int] = 25
    guidance: Optional[float] = 6.5
    project_id: Optional[str] = "default"


class VariationRequest(BaseModel):
    generation_id: str
    seed: int


class ExtendRequest(BaseModel):
    generation_id: str
    additional_duration: Optional[int] = 5


class PromptEnhanceRequest(BaseModel):
    prompt: str
    provider: Optional[str] = "openrouter"


class PromptEnhanceResponse(BaseModel):
    original_prompt: str
    enhanced_prompt: str
    cached: bool
    notice: Optional[str] = None


class GenerationResponse(BaseModel):
    id: str
    project_id: str
    prompt: str
    enhanced_prompt: Optional[str] = None
    negative_prompt: str
    mode: str
    reference_image_url: Optional[str] = None
    model_id: str
    duration: int
    aspect_ratio: str
    resolution: str
    fps: int
    seed: int
    is_fixed_seed: bool
    steps: int
    guidance: float
    status: str
    progress: float
    current_step: int
    total_steps: int
    eta_seconds: int
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    is_favorite: bool
    sha256_hash: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class HardwareInfo(BaseModel):
    mode: str
    comfyui_connected: bool
    comfyui_url: str
    cpu_name: str
    cpu_cores: int
    cpu_usage_percent: float
    ram_total_gb: float
    ram_used_gb: float
    gpu_name: Optional[str] = None
    vram_total_gb: Optional[float] = None
    vram_used_gb: Optional[float] = None
    cuda_available: bool
    ffmpeg_installed: Optional[bool] = True
