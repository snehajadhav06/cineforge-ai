import os
from sqlalchemy.orm import Session
from backend.database import PromptCache
from backend.services.cache_service import cache_service
from backend.services.openrouter_service import openrouter_service
from backend.services.ollama_service import ollama_service
from dotenv import load_dotenv

load_dotenv()
PROMPT_ENHANCER = os.getenv("PROMPT_ENHANCER", "openrouter")


class PromptService:
    @staticmethod
    async def enhance_prompt(prompt: str, db: Session, provider: str = PROMPT_ENHANCER) -> dict:
        prompt_hash = cache_service.compute_prompt_hash(prompt)

        # Check SQLite prompt cache first!
        cached = db.query(PromptCache).filter(PromptCache.prompt_hash == prompt_hash).first()
        if cached:
            return {
                "original_prompt": prompt,
                "enhanced_prompt": cached.enhanced_prompt,
                "cached": True,
                "notice": "Retrieved from SQLite prompt cache"
            }

        enhanced_text = prompt
        notice = None

        if provider == "openrouter":
            enhanced_text = await openrouter_service.enhance_prompt(prompt)
        elif provider == "ollama":
            enhanced_text = await ollama_service.enhance_prompt(prompt)
        else:
            enhanced_text = f"Cinematic video: {prompt.strip()}"

        # Save to SQLite Cache
        new_cache = PromptCache(
            id=f"pr-{prompt_hash[:12]}",
            prompt_hash=prompt_hash,
            original_prompt=prompt,
            enhanced_prompt=enhanced_text,
            provider=provider
        )
        db.add(new_cache)
        db.commit()

        return {
            "original_prompt": prompt,
            "enhanced_prompt": enhanced_text,
            "cached": False,
            "notice": notice
        }


prompt_service = PromptService()
