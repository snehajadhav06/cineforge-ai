import sys
import os
import shutil
import tempfile
import subprocess
from PIL import Image, ImageChops

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.services.ffmpeg_service import ffmpeg_service


def get_ffmpeg_path():
    path = ffmpeg_service.get_ffmpeg_path()
    if path:
        return path
    res = shutil.which("ffmpeg")
    return res or "ffmpeg"



def extract_frames(video_path: str, temp_dir: str, num_frames: int = 5) -> list:
    ffmpeg_bin = get_ffmpeg_path()
    output_pattern = os.path.join(temp_dir, "frame_%03d.png")

    cmd = [
        ffmpeg_bin, "-y", "-i", video_path,
        "-vf", "fps=2",
        "-vframes", str(num_frames),
        output_pattern
    ]

    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg frame extraction failed: {proc.stderr.decode('utf-8', errors='ignore')}")

    extracted = sorted([
        os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if f.endswith(".png")
    ])
    return extracted


def compute_frame_diff(img1_path: str, img2_path: str) -> float:
    img1 = Image.open(img1_path).convert("RGB")
    img2 = Image.open(img2_path).convert("RGB")

    if img1.size != img2.size:
        img2 = img2.resize(img1.size)

    diff_img = ImageChops.difference(img1, img2)
    stat = list(diff_img.getdata())
    total_diff = sum(sum(pixel) for pixel in stat)
    num_pixels = len(stat) * 3
    mean_diff = total_diff / max(1, num_pixels)
    return mean_diff


def check_zoompan_signature(img1_path: str, img2_path: str, raw_diff: float) -> bool:
    if raw_diff < 1.0:
        return False

    img1 = Image.open(img1_path).convert("RGB")
    img2 = Image.open(img2_path).convert("RGB")
    w, h = img1.size

    crop_margin = 0.04
    crop_box = (
        int(w * crop_margin),
        int(h * crop_margin),
        int(w * (1 - crop_margin)),
        int(h * (1 - crop_margin))
    )
    img2_cropped = img2.crop(crop_box).resize((w, h))

    diff_cropped = ImageChops.difference(img1, img2_cropped)
    stat = list(diff_cropped.getdata())
    total_diff = sum(sum(pixel) for pixel in stat)
    num_pixels = len(stat) * 3
    cropped_mean_diff = total_diff / max(1, num_pixels)

    if cropped_mean_diff < (raw_diff * 0.45):
        return True
    return False


def verify_motion(video_path: str):
    print("=== CineForge AI Video Motion Verification ===")
    print(f"Target Video Path: {video_path}")

    if not os.path.exists(video_path):
        print(f"[ERROR] Video file does not exist: {video_path}")
        sys.exit(1)

    temp_dir = tempfile.mkdtemp(prefix="motion_verify_")
    try:
        frames = extract_frames(video_path, temp_dir, num_frames=5)
        print(f"Extracted {len(frames)} sample frames for motion probing.")

        if len(frames) < 2:
            print("[RESULT] STATIC / LIKELY FAKE (Insufficient frames extracted)")
            return

        diffs = []
        is_zoompan = False

        for i in range(len(frames) - 1):
            diff = compute_frame_diff(frames[i], frames[i+1])
            diffs.append(diff)
            zp = check_zoompan_signature(frames[i], frames[i+1], diff)
            if zp:
                is_zoompan = True
            print(f"  Frame {i+1} -> Frame {i+2}: Mean Pixel Difference = {diff:.2f}" + (" [ZOOMPAN SIGNATURE]" if zp else ""))

        avg_diff = sum(diffs) / len(diffs)
        print(f"\nAverage Consecutive Frame Difference: {avg_diff:.2f}")

        if is_zoompan:
            print("\n[RESULT] STATIC / LIKELY FAKE (Zoompan / Ken Burns pan-zoom effect detected)")
        elif avg_diff < 2.5:
            print("\n[RESULT] STATIC / LIKELY FAKE (Low temporal pixel variance)")
        else:
            print("\n[RESULT] REAL MOTION (Substantial temporal pixel variation across frames)")

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sample_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__), "..", "generated", "projects", "default", "videos", "test-i2v-job.mp4"
        ))
        if os.path.exists(sample_path):
            video_path = sample_path
        else:
            print("Usage: python scripts/verify_motion.py <path_to_video.mp4>")
            sys.exit(1)
    else:
        video_path = sys.argv[1]

    verify_motion(video_path)
