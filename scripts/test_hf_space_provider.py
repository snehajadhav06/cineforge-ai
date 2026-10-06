import sys
import os
import json
import asyncio
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.providers.hf_space_provider import HuggingFaceSpaceProvider
from backend.services.ffmpeg_service import ffmpeg_service


async def run_test_flow(image_arg_path: str = None):
    print("=== CineForge AI HuggingFace Space Provider Verification ===")
    space_id = "Lightricks/ltx-video-distilled"
    print(f"Target HuggingFace Space: {space_id}")

    provider = HuggingFaceSpaceProvider(space_id=space_id)

    # 1. Connection Check
    print("\n1. Testing Client Connection & Availability...")
    available = await provider.is_available()
    print(f"  Result: {'AVAILABLE' if available else 'UNAVAILABLE'}")

    if not available:
        print(f"[ERROR] HuggingFace Space '{space_id}' is not reachable.")
        return

    # 2. Resolve Reference Image Argument (Requirement 1)
    if not image_arg_path:
        temp_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "generated", "projects", "default", "images"))
        os.makedirs(temp_dir, exist_ok=True)
        image_arg_path = os.path.join(temp_dir, "test_i2v_reference.png")
        if not os.path.exists(image_arg_path):
            img = Image.new("RGB", (704, 512), color=(73, 109, 137))
            img.save(image_arg_path)
            print(f"Created sample reference image at: {image_arg_path}")

    abs_image_path = os.path.abspath(image_arg_path)
    print(f"\nTarget Image File: {abs_image_path}")

    from gradio_client import handle_file
    handle_img_obj = handle_file(abs_image_path)
    print(f"  Image Handle Type: {type(handle_img_obj).__name__}")
    print(f"  Image Path: '{abs_image_path}'")

    # 3. Query Dimensions Helper /handle_image_upload_for_dims (Requirement 2 & 8)
    print("\n2. Querying Dimension Helper (/handle_image_upload_for_dims)...")
    h_32, w_32 = provider.get_image_dimensions(handle_img_obj)
    print(f"  Returned & Snapped Dimensions (height x width): {h_32} x {w_32}")

    # 4. Invoke Real Image-to-Video Synthesis
    print("\n3. Invoking Image-to-Video Generation...")
    async def on_progress(evt):
        print(f"  [Progress {evt.get('progress')}%] {evt.get('message')}")

    try:
        res = await provider.generate_video(
            prompt="A handsome character wearing a suit saying hello in cinematic lighting",
            negative_prompt="blurry, distorted",
            image_url=abs_image_path,
            duration=2,
            width=w_32,
            height=h_32,
            fps=24,
            seed=3358032,
            is_fixed_seed=True,
            steps=20,
            guidance=6.5,
            job_id="test_i2v_flow",
            progress_callback=on_progress
        )

        video_url = res.get("video_url")
        video_abs_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")), video_url.lstrip("/"))
        duration_sec = ffmpeg_service.get_video_duration(video_abs_path)

        print(f"\n[SUCCESS] Video Generation Completed!")
        print(f"  Output Video URL: {video_url}")
        print(f"  Absolute File Path: {video_abs_path}")
        print(f"  FFprobe Video Duration: {duration_sec:.2f} seconds")
        print(f"  Provider Badge: {res.get('provider')}")

    except Exception as err:
        print(f"\n[OUTPUT] Call Exception (verbatim error surfaced):")
        print(f"  {err}")

    print("\nHuggingFace Space test verification completed.")


if __name__ == "__main__":
    img_path = None
    if "--image" in sys.argv:
        idx = sys.argv.index("--image")
        if idx + 1 < len(sys.argv):
            img_path = sys.argv[idx + 1]

    asyncio.run(run_test_flow(img_path))
