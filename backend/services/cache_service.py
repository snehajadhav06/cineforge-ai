import hashlib


class CacheService:
    @staticmethod
    def compute_prompt_hash(prompt: str) -> str:
        normalized = prompt.strip().lower()
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

    @staticmethod
    def compute_generation_hash(
        prompt: str,
        negative_prompt: str,
        model_id: str,
        seed: int,
        width: int,
        height: int,
        duration: int,
        fps: int,
        steps: int,
        guidance: float,
        input_image_hash: str = "",
        mode: str = "text-to-video",
        provider: str = "mock"
    ) -> str:
        content = f"{prompt.strip()}|{negative_prompt.strip()}|{model_id}|{seed}|{width}|{height}|{duration}|{fps}|{steps}|{guidance}|{input_image_hash}|{mode}|{provider}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()


cache_service = CacheService()
