from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.schemas import PromptEnhanceRequest, PromptEnhanceResponse
from backend.services.prompt_service import prompt_service

router = APIRouter(prefix="/api/prompt", tags=["Prompt"])


@router.post("/enhance", response_model=PromptEnhanceResponse)
async def enhance_prompt(req: PromptEnhanceRequest, db: Session = Depends(get_db)):
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt string cannot be empty")
    res = await prompt_service.enhance_prompt(req.prompt, db, req.provider or "openrouter")
    return res
