# ComfyUI Setup for LTX-Video (CineForge AI)

To run real local AI video generation with LTX-Video in CineForge AI:

## 1. Exact Model Files & Directory Structure

Download the following model files and place them in your ComfyUI installation directory:

| Model File | Target Folder | Source Link |
| :--- | :--- | :--- |
| `ltx-video-2b-v0.9.safetensors` | `ComfyUI/models/checkpoints/` | [HuggingFace: Lightricks/LTX-Video](https://huggingface.co/Lightricks/LTX-Video) |
| `t5xxl_fp16.safetensors` | `ComfyUI/models/clip/` | [HuggingFace: google/t5-v1_1-xxl](https://huggingface.co/comfyanonymous/flux_text_encoders/tree/main) |

## 2. Required Nodes & Custom Nodes

Ensure the following node types are installed in ComfyUI:
- **Core Nodes**: `CheckpointLoaderSimple`, `CLIPLoader`, `CLIPTextEncode`, `KSampler`, `VAEDecode`, `LoadImage`
- **LTX-Video Nodes**: `LTXVConditioning`, `EmptyLTXVLatentVideo`, `LTXVImgToVideo`
- **Video Exporter Node**: `VHS_VideoCombine` (Provided by [ComfyUI-VideoHelperSuite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite))

Install ComfyUI-VideoHelperSuite into `ComfyUI/custom_nodes/`:
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite
```

## 3. Workflow Files

- `comfyui/workflows/ltxv_t2v.json` (Text-to-Video API format)
- `comfyui/workflows/ltxv_i2v.json` (Image-to-Video API format)
