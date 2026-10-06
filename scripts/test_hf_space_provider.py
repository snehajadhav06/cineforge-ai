import sys
import os
import json
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.providers.hf_space_provider import HuggingFaceSpaceProvider
CONFIG_SPACES_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config", "spaces.json"))


async def test_spaces(run_test_generation: bool = False):
    print("=== CineForge AI HuggingFace Spaces Discovery & Verification ===")

    if not os.path.exists(CONFIG_SPACES_PATH):
        print(f"[ERROR] Config spaces.json file not found at: {CONFIG_SPACES_PATH}")
        return

    with open(CONFIG_SPACES_PATH, "r", encoding="utf-8") as f:
        spaces = json.load(f)

    valid_spaces = []

    try:
        from gradio_client import Client
    except ImportError:
        print("[ERROR] gradio_client python package is NOT installed. Run 'pip install gradio_client'.")
        sys.exit(1)

    for sp in spaces:
        space_id = sp.get("id")
        print(f"\nTesting HF Space: {space_id}...")

        provider = HuggingFaceSpaceProvider(space_id=space_id)
        try:
            client = Client(space_id)
            api_info = client.view_api(return_format="dict")


            named_endpoints = list(api_info.get("named_endpoints", {}).keys())
            unnamed_endpoints = list(api_info.get("unnamed_endpoints", {}).keys())
            all_endpoints = named_endpoints + unnamed_endpoints

            if all_endpoints:
                print(f"  [OK] Reachable! Discovered Endpoints: {all_endpoints}")
                sp["discovered_endpoints"] = all_endpoints
                valid_spaces.append(sp)
            else:
                print(f"  [WARN] Reachable but returned NO valid API endpoints.")
        except Exception as e:
            err_msg = str(e)
            if "404" in err_msg or "not found" in err_msg.lower():
                print(f"  [REMOVED] Space '{space_id}' does not exist (HTTP 404). Removing from config.")
            elif "sleeping" in err_msg.lower():
                print(f"  [SLEEPING] Space '{space_id}' is sleeping. Retaining in config.")
                valid_spaces.append(sp)
            else:
                print(f"  [UNREACHABLE] Space '{space_id}' error: {err_msg}")

    # Update spaces.json with valid / active spaces
    if len(valid_spaces) != len(spaces):
        print(f"\nUpdating {CONFIG_SPACES_PATH}: Keeping {len(valid_spaces)} active spaces.")
        with open(CONFIG_SPACES_PATH, "w", encoding="utf-8") as f:
            json.dump(valid_spaces, f, indent=2)

    # Optional 1-second tiny t2v generation run
    if run_test_generation and valid_spaces:
        target_space = valid_spaces[0].get("id")
        print(f"\nRunning test 1-second Text-to-Video generation on Space: {target_space}...")
        provider = HuggingFaceSpaceProvider(space_id=target_space)

        async def dummy_progress(evt):
            print(f"  [Progress] {evt.get('progress')}% - {evt.get('message')}")

        try:
            res = await provider.generate_video(
                prompt="A tiny test animation of a glowing golden star",
                negative_prompt="blurry",
                duration=1,
                width=512,
                height=512,
                fps=16,
                seed=42,
                steps=5,
                job_id="test_hf_run",
                progress_callback=dummy_progress
            )
            print(f"\n[SUCCESS] Test generation completed! Video URL: {res.get('video_url')}")
        except Exception as e:
            print(f"\n[FAILED] Test generation failed: {e}")

    print("\nHuggingFace Spaces Verification Completed.")


if __name__ == "__main__":
    run_gen = "--generate" in sys.argv
    asyncio.run(test_spaces(run_test_generation=run_gen))
