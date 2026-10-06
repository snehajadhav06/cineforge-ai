import os
import sys
import json
import httpx
from dotenv import load_dotenv

load_dotenv()

COMFYUI_URL = os.getenv("COMFYUI_URL", "http://127.0.0.1:8188").rstrip("/")
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WORKFLOW_DIR = os.path.join(BASE_DIR, "comfyui", "workflows")


def get_workflow_class_types():
    class_types = set()
    for wf_file in ["ltxv_t2v.json", "ltxv_i2v.json"]:
        path = os.path.join(WORKFLOW_DIR, wf_file)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for node_id, node_def in data.items():
                    if isinstance(node_def, dict) and "class_type" in node_def:
                        class_types.add((node_def["class_type"], wf_file))
    return class_types


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
                free_gb = d.get('vram_free', 0) / (1024**3)
                print(f"  Device {idx}: {d.get('name', 'Unknown')} ({free_gb:.2f} GB free VRAM)")
        else:
            print(f"[ERROR] ComfyUI Server error: Status HTTP {res.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] ComfyUI not reachable at {COMFYUI_URL}: {e}")
        print("  -> Tip: Launch ComfyUI locally or configure HF_SPACE_ID in .env")
        return False

    # 2. Object Info & Node Class Verification
    try:
        res = httpx.get(f"{COMFYUI_URL}/object_info", timeout=5.0)
        if res.status_code != 200:
            print(f"[ERROR] Failed to query /object_info (Status {res.status_code})")
            return False

        nodes_info = res.json()
        workflow_nodes = get_workflow_class_types()

        missing_nodes = []
        verified_nodes = set()

        print("\nVerifying ComfyUI Workflow Nodes:")
        for class_type, wf_file in sorted(workflow_nodes):
            if class_type in nodes_info:
                if class_type not in verified_nodes:
                    print(f"  [OK] Node '{class_type}' : AVAILABLE")
                    verified_nodes.add(class_type)
            else:
                missing_nodes.append((class_type, wf_file))
                print(f"  [ERROR] Node '{class_type}' : MISSING (Required by {wf_file})")

        # 3. Model Files Verification
        print("\nVerifying Required Model Files:")
        ckpt_loader = nodes_info.get("CheckpointLoaderSimple", {})
        ckpt_inputs = ckpt_loader.get("input", {}).get("required", {}).get("ckpt_name", [[]])[0]

        ltx_found = False
        print("Available Checkpoint Models:")
        for ckpt in ckpt_inputs:
            print(f"  - {ckpt}")
            if "ltx" in str(ckpt).lower():
                ltx_found = True

        clip_loader = nodes_info.get("CLIPLoader", {})
        clip_inputs = clip_loader.get("input", {}).get("required", {}).get("clip_name", [[]])[0]

        clip_t5_found = False
        print("\nAvailable CLIP Models:")
        for clip in clip_inputs:
            print(f"  - {clip}")
            if "t5" in str(clip).lower() or "ltx" in str(clip).lower():
                clip_t5_found = True

        all_ok = True
        if not ltx_found:
            print("\n[ERROR] LTX-Video Checkpoint MISSING: 'ltx-video-2b-v0.9.safetensors' not found in ComfyUI/models/checkpoints/")
            all_ok = False
        else:
            print("\n[OK] LTX-Video Checkpoint: FOUND")

        if not clip_t5_found:
            print("[WARN] T5/LTX CLIP Model NOT FOUND in ComfyUI/models/clip/")

        if missing_nodes:
            all_ok = False
            print(f"\n[SUMMARY] {len(missing_nodes)} workflow nodes are missing from ComfyUI.")

        return all_ok
    except Exception as e:
        print(f"[ERROR] Failed to verify ComfyUI object info: {e}")
        return False


if __name__ == "__main__":
    success = check_comfyui()
    sys.exit(0 if success else 1)
