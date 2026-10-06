import os
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.2-3b-instruct:free")
OPENROUTER_VISION_MODEL = os.getenv("OPENROUTER_VISION_MODEL", "meta-llama/llama-3.2-11b-vision-instruct:free")


class OpenRouterService:
    def __init__(self, api_key: str = OPENROUTER_API_KEY, model: str = OPENROUTER_MODEL):
        self.api_key = api_key
        self.model = model

    async def enhance_prompt(self, prompt: str, retry_count: int = 1) -> dict:
        # HARD RULE: OpenRouter FREE models (:free) only!
        selected_model = self.model if self.model.endswith(":free") else "meta-llama/llama-3.2-3b-instruct:free"

        if not self.api_key:
            return {
                "enhanced_prompt": f"Masterpiece 8k cinematic video shot, volumetric lighting, hyper-detailed motion: {prompt.strip()}",
                "notice": "Using default local enhancer (No OpenRouter API key set)"
            }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://cineforge.ai",
            "X-Title": "CineForge AI",
            "Content-Type": "application/json",
        }

        system_msg = (
            "You are a master cinematic video director. Transform the given prompt into a detailed text-to-video AI prompt. "
            "Describe camera movement, lighting, atmosphere, cinematic style, textures, and fluid motion. Output direct prompt text only."
        )

        payload = {
            "model": selected_model,
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": f"Enhance this video prompt: {prompt}"},
            ],
            "max_tokens": 150,
            "temperature": 0.7,
        }

        for attempt in range(retry_count + 1):
            try:
                async with httpx.AsyncClient(timeout=8.0) as client:
                    res = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        enhanced = data["choices"][0]["message"]["content"].strip()
                        return {"enhanced_prompt": enhanced, "notice": None}
                    elif res.status_code == 429:
                        # Rate limited: backoff retry once
                        if attempt < retry_count:
                            await asyncio.sleep(1.5)
                            continue
                        return {
                            "enhanced_prompt": prompt.strip(),
                            "notice": "Rate limit hit (429). Silently using original prompt."
                        }
            except Exception:
                if attempt < retry_count:
                    await asyncio.sleep(1.0)
                    continue

        return {
            "enhanced_prompt": f"Cinematic video shot, 8k resolution, dynamic motion: {prompt.strip()}",
            "notice": "OpenRouter timeout or error. Using fallback prompt."
        }

    async def caption_reference_image(self, image_url_or_b64: str) -> str:
        selected_vision = OPENROUTER_VISION_MODEL if OPENROUTER_VISION_MODEL.endswith(":free") else "meta-llama/llama-3.2-11b-vision-instruct:free"

        if not self.api_key:
            return "Reference image showing detailed subject with natural lighting and smooth composition."

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://cineforge.ai",
            "X-Title": "CineForge AI",
            "Content-Type": "application/json",
        }

        payload = {
            "model": selected_vision,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe the key subject, composition, and lighting of this image for AI video generation in one sentence."},
                        {"type": "image_url", "image_url": {"url": image_url_or_b64}}
                    ]
                }
            ],
            "max_tokens": 100
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
                if res.status_code == 200:
                    return res.json()["choices"][0]["message"]["content"].strip()
        except Exception:
            pass
        return "Reference image scene with dynamic lighting and composition."


openrouter_service = OpenRouterService()
