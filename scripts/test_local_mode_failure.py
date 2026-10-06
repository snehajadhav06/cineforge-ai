import sys
import os
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ["MODE"] = "local"
os.environ["COMFYUI_URL"] = "http://127.0.0.1:8188"

from backend.database import SessionLocal
from backend.schemas import GenerationRequest
from backend.services.video_service import video_service


async def test_failure():
    print("=== Testing MODE=local Failure Behavior when ComfyUI is Offline ===")
    db = SessionLocal()

    req = GenerationRequest(
        prompt="Test prompt in local mode",
        mode="text-to-video",
        model_id="ltx-video",
        steps=5
    )

    try:
        gen = await video_service.create_and_run_generation(req, db)
        print(f"Generation record created in DB: ID={gen.id}, status={gen.status}")

        # Wait for async background task to complete
        await asyncio.sleep(1.5)

        # Re-fetch record from DB
        db.refresh(gen)
        print(f"Final DB Record Status: {gen.status}")
        print(f"Video URL: {gen.video_url}")

        if gen.status == "failed":
            print("[SUCCESS] Job correctly marked as FAILED in local mode when ComfyUI is unreachable!")
            print("No fallback to mock/Ken Burns occurred.")
        else:
            print(f"[FAIL] Expected status 'failed', got '{gen.status}'")

    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_failure())
