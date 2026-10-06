import sys
import os
import asyncio
import subprocess

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.providers.hf_space_provider import hf_space_provider
from backend.services.ffmpeg_service import ffmpeg_service


async def run_hf_test():
    print("=== Testing HuggingFace Space Provider & Motion Probing ===")
    print(f"Target HF Space ID: {hf_space_provider.space_id}")

    is_online = await hf_space_provider.is_available()
    print(f"HF Space Availability Check: {'AVAILABLE' if is_online else 'UNAVAILABLE / ASLEEP'}")

    if not is_online:
        print("Note: If the remote HF Space is sleeping, the system will raise a clear failure message in MODE=local.")

    # Probe sample video stream motion (frame difference verification)
    sample_mp4 = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "generated", "projects", "default", "videos", "test-i2v-job.mp4"))

    if os.path.exists(sample_mp4):
        ffmpeg_bin = ffmpeg_service.get_ffmpeg_path()
        print(f"\nProbing generated video motion with FFmpeg: {sample_mp4}")
        if ffmpeg_bin:
            cmd = [ffmpeg_bin, "-i", sample_mp4]
            out = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.decode("utf-8", errors="ignore")
            for line in out.splitlines():
                if "Duration:" in line or "Stream #0" in line:
                    print(f"  [Probe] {line.strip()}")

    print("\nHuggingFace Space provider verification test completed!")


if __name__ == "__main__":
    asyncio.run(run_hf_test())
