import httpx


class OllamaService:
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self.base_url = base_url
        self.model = model

    async def enhance_prompt(self, prompt: str) -> str:
        payload = {
            "model": self.model,
            "prompt": f"Enhance this video generation prompt with rich cinematic detail and motion: {prompt}",
            "stream": False,
        }
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.post(f"{self.base_url}/api/generate", json=payload)
                if res.status_code == 200:
                    return res.json().get("response", "").strip()
        except Exception:
            pass
        return f"Cinematic high quality motion video: {prompt.strip()}"


ollama_service = OllamaService()
