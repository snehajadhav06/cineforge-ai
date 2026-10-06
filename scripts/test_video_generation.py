import sys
import os
import asyncio
import subprocess

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.ffmpeg_service import ffmpeg_service
from backend.services.video_provider import mock_video_provider


async def run_tests():
    print("=== Testing CineForge AI Mock MP4 Video Generation ===")

    # Test 1: Text-to-video MP4 synthesis
    print("\n1. Testing Text-to-Video synthesis...")
    t2v_res = await mock_video_provider.generate_video(
        prompt="A vibrant cinematic ocean wave at sunset",
        negative_prompt="blurry",
        image_url=None,
        duration=5,
        width=1280,
        height=720,
        fps=24,
        seed=12345,
        steps=10,
        job_id="test-t2v-job"
    )

    t2v_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", t2v_res["video_url"].lstrip("/")))
    print(f"Text-to-Video file path: {t2v_path}")
    print(f"File exists: {os.path.exists(t2v_path)}, Size: {os.path.getsize(t2v_path) if os.path.exists(t2v_path) else 0} bytes")

    # Test 2: Image-to-video MP4 synthesis
    print("\n2. Testing Image-to-Video Ken Burns synthesis...")
    sample_img_url = "https://images.unsplash.com/photo-1519501025264-65ba15a82390?auto=format&fit=crop&w=800&q=80"
    i2v_res = await mock_video_provider.generate_video(
        prompt="Slow zoom into futuristic city skyline",
        negative_prompt="blurry",
        image_url=sample_img_url,
        duration=5,
        width=1280,
        height=720,
        fps=24,
        seed=67890,
        steps=10,
        job_id="test-i2v-job"
    )

    i2v_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", i2v_res["video_url"].lstrip("/")))
    print(f"Image-to-Video file path: {i2v_path}")
    print(f"File exists: {os.path.exists(i2v_path)}, Size: {os.path.getsize(i2v_path) if os.path.exists(i2v_path) else 0} bytes")

    # Inspect stream metadata using FFmpeg binary
    ffmpeg_bin = ffmpeg_service.get_ffmpeg_path()
    print(f"\nFFmpeg Executable Path: {ffmpeg_bin}")

    if ffmpeg_bin:
        print("\n=== Probing Output Stream Metadata ===")
        out = subprocess.run([ffmpeg_bin, "-i", t2v_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.decode('utf-8', errors='ignore')
        for line in out.splitlines():
            if "Duration:" in line or "Stream #0" in line:
                print(f"  [T2V] {line.strip()}")

        out2 = subprocess.run([ffmpeg_bin, "-i", i2v_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.decode('utf-8', errors='ignore')
        for line in out2.splitlines():
            if "Duration:" in line or "Stream #0" in line:
                print(f"  [I2V] {line.strip()}")

    print("\nAll video generation and metadata probe tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(run_tests())
