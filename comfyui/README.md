# ComfyUI Setup for LTX-Video (CineForge AI)

To run real local AI video generation with LTX-Video in CineForge AI:

## 1. Required Models
Download the LTX-Video checkpoint and place it in `ComfyUI/models/checkpoints/`:
- **Checkpoint**: `ltx-video-2b-v0.9.safetensors`
  - Download from: [HuggingFace: Lightricks/LTX-Video](https://huggingface.co/Lightricks/LTX-Video)

## 2. Required Custom Nodes
Install the following custom nodes via ComfyUI Manager or `git clone` into `ComfyUI/custom_nodes/`:
- **ComfyUI-VideoHelperSuite** (`VHS_VideoCombine` node)
  - `git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite`

## 3. Workflow Files
- `comfyui/workflows/ltxv_t2v.json` (Text-to-Video API format)
- `comfyui/workflows/ltxv_i2v.json` (Image-to-Video API format)
