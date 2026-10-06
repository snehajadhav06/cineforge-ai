import os
import re
import shutil
import subprocess
import base64
import tempfile
import logging

logger = logging.getLogger("cineforge.ffmpeg")

class FFmpegService:
    def __init__(self):
        self._ffmpeg_path = self._find_ffmpeg()

    def _find_ffmpeg(self) -> str:
        # Check system PATH first
        path = shutil.which("ffmpeg")
        if path:
            return path

        # Try imageio_ffmpeg
        try:
            import imageio_ffmpeg
            path = imageio_ffmpeg.get_ffmpeg_exe()
            if path and os.path.exists(path):
                return path
        except Exception:
            pass

        logger.error("FFmpeg executable NOT FOUND on system! Video generation may fail.")
        return None

    def is_ffmpeg_installed(self) -> bool:
        if not self._ffmpeg_path:
            return False
        try:
            res = subprocess.run([self._ffmpeg_path, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return res.returncode == 0
        except Exception:
            return False

    def get_ffmpeg_path(self) -> str:
        return self._ffmpeg_path

    def generate_test_pattern_video(self, output_path: str, width: int = 1280, height: int = 720, fps: int = 24, duration: int = 5) -> bool:
        ffmpeg_bin = self.get_ffmpeg_path()
        if not ffmpeg_bin:
            logger.error("Cannot generate video: FFmpeg is not installed.")
            return False

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        cmd = [
            ffmpeg_bin, "-y",
            "-f", "lavfi",
            "-i", f"testsrc=size={width}x{height}:rate={fps}:duration={duration}",
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            output_path
        ]

        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if res.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return True
            else:
                logger.error(f"FFmpeg test pattern generation failed: {res.stderr.decode('utf-8', errors='ignore')}")
                return False
        except Exception as e:
            logger.error(f"Exception running FFmpeg test pattern: {e}")
            return False

    def generate_ken_burns_video(self, image_input: str, output_path: str, width: int = 1280, height: int = 720, fps: int = 24, duration: int = 5) -> bool:
        ffmpeg_bin = self.get_ffmpeg_path()
        if not ffmpeg_bin:
            logger.error("Cannot generate video: FFmpeg is not installed.")
            return False

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        temp_img_file = None

        try:
            # Handle base64 / data URL input image or local file path
            if image_input and image_input.startswith("data:image"):
                header, encoded = image_input.split(",", 1)
                img_bytes = base64.b64decode(encoded)
                ext = ".png" if "png" in header else ".jpg"
                temp_img_file = tempfile.NamedTemporaryFile("wb", delete=False, suffix=ext)
                temp_img_file.write(img_bytes)
                temp_img_file.close()
                input_path = temp_img_file.name
            elif image_input and os.path.exists(image_input):
                input_path = image_input
            else:
                return self.generate_test_pattern_video(output_path, width, height, fps, duration)

            total_frames = int(duration * fps)
            zoompan_filter = f"zoompan=z='min(zoom+0.0015,1.15)':d={total_frames}:s={width}x{height},format=yuv420p"

            cmd = [
                ffmpeg_bin, "-y",
                "-loop", "1",
                "-i", input_path,
                "-vf", zoompan_filter,
                "-c:v", "libx264",
                "-t", str(duration),
                "-r", str(fps),
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                output_path
            ]

            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            if temp_img_file and os.path.exists(temp_img_file.name):
                try: os.remove(temp_img_file.name)
                except Exception: pass

            if res.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                return True
            else:
                logger.error(f"FFmpeg Ken Burns zoompan failed: {res.stderr.decode('utf-8', errors='ignore')}")
                return self.generate_test_pattern_video(output_path, width, height, fps, duration)
        except Exception as e:
            logger.error(f"Exception generating Ken Burns video: {e}")
            return self.generate_test_pattern_video(output_path, width, height, fps, duration)

    def extract_last_frame(self, video_path: str, output_image_path: str) -> bool:
        ffmpeg_bin = self.get_ffmpeg_path()
        if not ffmpeg_bin or not os.path.exists(video_path):
            return False
        os.makedirs(os.path.dirname(output_image_path), exist_ok=True)
        cmd = [
            ffmpeg_bin, "-y",
            "-sseof", "-1",
            "-i", video_path,
            "-update", "1",
            "-q:v", "2",
            output_image_path
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return res.returncode == 0 and os.path.exists(output_image_path) and os.path.getsize(output_image_path) > 0
        except Exception as e:
            logger.error(f"Failed to extract last frame with FFmpeg: {e}")
            return False

    def concat_videos(self, video_paths: list[str], output_path: str) -> bool:
        ffmpeg_bin = self.get_ffmpeg_path()
        if not ffmpeg_bin or not video_paths:
            return False
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        list_file = tempfile.NamedTemporaryFile("w", delete=False, suffix=".txt")
        for vp in video_paths:
            clean_vp = os.path.abspath(vp).replace("\\", "/")
            list_file.write(f"file '{clean_vp}'\n")
        list_file.close()

        cmd = [
            ffmpeg_bin, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", list_file.name,
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            output_path
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if os.path.exists(list_file.name):
                try: os.remove(list_file.name)
                except Exception: pass
            return res.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0
        except Exception as e:
            if os.path.exists(list_file.name):
                try: os.remove(list_file.name)
                except Exception: pass
            logger.error(f"Failed to concat videos with FFmpeg: {e}")
            return False

    def extract_thumbnail(self, video_path: str, output_thumb_path: str) -> bool:
        ffmpeg_bin = self.get_ffmpeg_path()
        if not ffmpeg_bin or not os.path.exists(video_path):
            return False
        os.makedirs(os.path.dirname(output_thumb_path), exist_ok=True)
        cmd = [
            ffmpeg_bin, "-y",
            "-ss", "00:00:00.500",
            "-i", video_path,
            "-vframes", "1",
            "-q:v", "2",
            output_thumb_path
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return res.returncode == 0 and os.path.exists(output_thumb_path)
        except Exception:
            return False

    def get_video_duration(self, video_path: str) -> float:
        ffmpeg_bin = self.get_ffmpeg_path()
        if not ffmpeg_bin or not os.path.exists(video_path):
            return 0.0
        cmd = [
            ffmpeg_bin, "-i", video_path
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout.decode("utf-8", errors="ignore")
            m = re.search(r"Duration:\s*(\d+):(\d+):([\d\.]+)", res)
            if m:
                hrs, mins, secs = float(m.group(1)), float(m.group(2)), float(m.group(3))
                return hrs * 3600 + mins * 60 + secs
        except Exception:
            pass
        return 0.0


ffmpeg_service = FFmpegService()
