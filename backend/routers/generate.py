from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db, Generation
from backend.schemas import GenerationRequest, GenerationResponse, VariationRequest, ExtendRequest
from backend.services.video_service import video_service

router = APIRouter(prefix="/api/generate", tags=["Generation"])


@router.post("", response_model=GenerationResponse)
async def generate_text_to_video(req: GenerationRequest, db: Session = Depends(get_db)):
    req.mode = "text-to-video"
    gen = await video_service.create_and_run_generation(req, db)
    return gen


@router.post("/image-to-video", response_model=GenerationResponse)
async def generate_image_to_video(req: GenerationRequest, db: Session = Depends(get_db)):
    req.mode = "image-to-video"
    if not req.reference_image_url:
        raise HTTPException(status_code=400, detail="reference_image_url is required for image-to-video")
    gen = await video_service.create_and_run_generation(req, db)
    return gen


@router.post("/variation", response_model=GenerationResponse)
async def create_variation(req: VariationRequest, db: Session = Depends(get_db)):
    base_gen = db.query(Generation).filter(Generation.id == req.generation_id).first()
    if not base_gen:
        raise HTTPException(status_code=404, detail="Base generation not found")

    gen_req = GenerationRequest(
        prompt=base_gen.prompt,
        negative_prompt=base_gen.negative_prompt,
        mode=base_gen.mode,
        reference_image_url=base_gen.reference_image_url,
        model_id=base_gen.model_id,
        duration=base_gen.duration,
        aspect_ratio=base_gen.aspect_ratio,
        resolution=base_gen.resolution,
        fps=base_gen.fps,
        seed=req.seed,
        is_fixed_seed=True,
        steps=base_gen.steps,
        guidance=base_gen.guidance,
        project_id=base_gen.project_id
    )
    return await video_service.create_and_run_generation(gen_req, db)


@router.post("/extend", response_model=GenerationResponse)
async def extend_video(req: ExtendRequest, db: Session = Depends(get_db)):
    base_gen = db.query(Generation).filter(Generation.id == req.generation_id).first()
    if not base_gen:
        raise HTTPException(status_code=404, detail="Base generation not found")

    extended_prompt = f"{base_gen.prompt} (Continuation sequence +{req.additional_duration or 5}s)"
    gen_req = GenerationRequest(
        prompt=extended_prompt,
        negative_prompt=base_gen.negative_prompt,
        mode=base_gen.mode,
        reference_image_url=base_gen.reference_image_url,
        model_id=base_gen.model_id,
        duration=(base_gen.duration + (req.additional_duration or 5)),
        aspect_ratio=base_gen.aspect_ratio,
        resolution=base_gen.resolution,
        fps=base_gen.fps,
        seed=base_gen.seed + 1,
        steps=base_gen.steps,
        guidance=base_gen.guidance,
        project_id=base_gen.project_id
    )
    return await video_service.create_and_run_generation(gen_req, db)
