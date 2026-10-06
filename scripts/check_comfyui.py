import os
import sys
import httpx
from dotenv import load_dotenv

load_dotenv()

COMFYUI_URL = os.getenv("COMFYUI_URL", "http://127.0.0.1:8188").rstrip("/")


def check_comfyui():
    print("=== CineForge AI ComfyUI Health & Dependency Verification ===")
    print(f"Checking ComfyUI URL: {COMFYUI_URL}")

    # 1. Server Stats Check
    try:
        res = httpx.get(f"{COMFYUI_URL}/system_stats", timeout=3.0)
        if res.status_code == 200:
            stats = res.json()
            print("[OK] ComfyUI Server Status: ONLINE")
            devices = stats.get("devices", [])
            for idx, d in enumerate(devices):
                print(f"  Device {idx}: {d.get('name', 'Unknown')} ({d.get('vram_free', 0) / (1024**3):.2f} GB free VRAM)")
        else:
            print(f"[ERROR] ComfyUI Server error: Status HTTP {res.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] ComfyUI not reachable at {COMFYUI_URL}: {e}")
        print("  -> Tip: Ensure ComfyUI is launched or start in MODE=mock for local simulation.")
        return False

    # 2. Object Info & Nodes Check
    try:
        res = httpx.get(f"{COMFYUI_URL}/object_info", timeout=5.0)
        if res.status_code == 200:
            nodes_info = res.json()

            required_nodes = ["CheckpointLoaderSimple", "KSampler", "VAEDecode", "VHS_VideoCombine"]
            missing_nodes = []
            for node in required_nodes:
                if node in nodes_info:
                    print(f"[OK] Required Node '{node}': AVAILABLE")
                else:
                    missing_nodes.append(node)
                    print(f"[ERROR] Required Node '{node}': MISSING")

            ckpt_loader = nodes_info.get("CheckpointLoaderSimple", {})
            ckpt_input = ckpt_loader.get("input", {}).get("required", {}).get("ckpt_name", [[]])[0]
            print("\nAvailable Checkpoint Models in ComfyUI:")
            ltx_found = False
            for ckpt in ckpt_input:
                print(f"  - {ckpt}")
                if "ltx" in ckpt.lower():
                    ltx_found = True

            if ltx_found:
                print("\n[OK] LTX-Video Checkpoint: FOUND")
            else:
                print("\n[WARN] LTX-Video Checkpoint: NOT FOUND (Please download ltx-video-2b-v0.9.safetensors to ComfyUI/models/checkpoints/)")

            return len(missing_nodes) == 0
    except Exception as e:
        print(f"[ERROR] Failed to query ComfyUI object info: {e}")
        return False


if __name__ == "__main__":
    success = check_comfyui()
    sys.exit(0 if success else 1)
