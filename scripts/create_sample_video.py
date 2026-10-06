import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.ffmpeg_service import ffmpeg_service

if __name__ == "__main__":
    out_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "generated", "projects", "default", "videos", "sample.mp4"))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    res = ffmpeg_service.generate_test_pattern_video(out_path, 1280, 720, 24, 5)
    print(f"Generated default local sample.mp4: {res} at {out_path}")
