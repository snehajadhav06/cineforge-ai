import sys
import os
import json
import asyncio
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.providers.hf_space_provider import HuggingFaceSpaceProvider


async def run_i2v_test():
    print("=== CineForge AI HuggingFace Space Provider i2v Verification ===")
    space_id = "Lightricks/ltx-video-distilled"
    print(f"Target HuggingFace Space: {space_id}")

    provider = HuggingFaceSpaceProvider(space_id=space_id)

    # 1. Connectivity Check (reuses cached Client instance & logs API signature once)
    print("\n1. Testing Client Connection & Availability...")
    available = await provider.is_available()
    print(f"  Result: {'AVAILABLE' if available else 'UNAVAILABLE'}")

    if not available:
        print(f"[ERROR] HuggingFace Space '{space_id}' is not reachable.")
        return

    # 2. Prepare Sample Reference Image for i2v Call
    temp_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "generated", "projects", "default", "images"))
    os.makedirs(temp_dir, exist_ok=True)
    sample_img_path = os.path.join(temp_dir, "test_i2v_reference.png")

    if not os.path.exists(sample_img_path):
        img = Image.new("RGB", (704, 512), color=(73, 109, 137))
        img.save(sample_img_path)
        print(f"\nCreated test reference image: {sample_img_path}")

    # 3. Perform i2v Parameter Mapping Inspection & Call
    print("\n2. Performing i2v Parameter Mapping & Client Call...")
    client = provider.get_client()

    endpoint_name = provider.select_endpoint(is_i2v=True)
    args, mapped_log, clamped_notes = provider.map_and_validate_parameters(
        client=client,
        endpoint_name=endpoint_name,
        prompt="A handsome character wearing a suit saying hello in cinematic lighting",
        negative_prompt="blurry, distorted",
        image_path=sample_img_path,
        duration=2,
        width=704,
        height=512,
        fps=24,
        seed=3358032,
        is_fixed_seed=True,
        steps=20,
        guidance=6.5,
        is_i2v=True
    )

    print(f"\nTarget Endpoint: {endpoint_name}")
    print("Exact Parameter Values Mapped & Validated:")
    for k, v in mapped_log.items():
        print(f"  - {k}: {v}")

    if clamped_notes:
        print("\nClamping Notes:")
        for note in clamped_notes:
            print(f"  - {note}")

    print("\n3. Invoking Real Image-to-Video Generation...")

    async def on_progress(evt):
        print(f"  [Progress {evt.get('progress')}%] {evt.get('message')}")

    try:
        res = await provider.generate_video(
            prompt="A handsome character wearing a suit saying hello in cinematic lighting",
            negative_prompt="blurry, distorted",
            image_url=sample_img_path,
            duration=2,
            width=704,
            height=512,
            fps=24,
            seed=3358032,
            is_fixed_seed=True,
            steps=20,
            guidance=6.5,
            job_id="test_i2v_verify",
            progress_callback=on_progress
        )

        print(f"\n[SUCCESS] i2v Video Generation Completed!")
        print(f"  Video URL: {res.get('video_url')}")
        print(f"  Provider Badge: {res.get('provider')}")

    except Exception as err:
        print(f"\n[OUTPUT] Call Exception (verbatim error surfaced):")
        print(f"  {err}")

    print("\nHuggingFace Space i2v verification test completed.")


if __name__ == "__main__":
    asyncio.run(run_i2v_test())
