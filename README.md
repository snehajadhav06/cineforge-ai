# CineForge AI 🎬⚡

**Local-first AI Text-to-Video & Image-to-Video Studio** built with React, TypeScript, Vite, Tailwind CSS, FastAPI, SQLite, and ComfyUI.

---

## 📌 Project Overview

CineForge AI brings local open-source AI video generation (LTX-Video, Wan 2.1, HunyuanVideo, CogVideoX, SVD) to your local machine with a high-performance dark-themed studio UI, SQLite history tracking, SHA256 prompt caching, and zero paid API dependencies.

---

## 🛠️ Stack & Architecture

- **Frontend**: React 19 + TypeScript + Vite + Tailwind CSS (v4) + Lucide Icons
- **Backend**: Python + FastAPI + SQLAlchemy ORM + Pydantic
- **Database**: SQLite (`database/cineforge.db`)
- **Video Engine**: ComfyUI (Local or Cloud GPU Tunnel) + FFmpeg
- **Text Models**: OpenRouter Free Models (`:free` suffix) or Ollama (Local) for Prompt Enhancement & Reference Image Captioning

---

## ⚙️ Environment Configuration (`.env`)

Copy `.env.example` to `.env` in the root folder:

```ini
# Engine Execution Mode: mock | local | cloud (default: mock)
MODE=mock

# ComfyUI Engine Backend URL (Local or Colab/Kaggle Tunnel URL)
COMFYUI_URL=http://127.0.0.1:8188

# OpenRouter Free LLM API Key (Free models ending in :free ONLY, no paid models)
OPENROUTER_API_KEY=your_free_openrouter_key

# Text Model for Prompt Enhancement
OPENROUTER_MODEL=meta-llama/llama-3.2-3b-instruct:free

# Vision Model for Reference Image Captioning
OPENROUTER_VISION_MODEL=meta-llama/llama-3.2-11b-vision-instruct:free

# Prompt Enhancer Provider: openrouter | ollama | none
PROMPT_ENHANCER=openrouter
```

---

## 🚀 How to Run CineForge AI on Windows

### 1. Prerequisites
- **Python**: 3.10, 3.11, 3.12, or 3.14
- **Node.js**: v18+ & npm
- **FFmpeg**: Added to Windows PATH (optional for video stitching)
- **NVIDIA CUDA Driver**: Required for local GPU video synthesis (or use Cloud GPU Tunnel)

### 2. Start the Backend API (Terminal 1)
Open PowerShell in the root project folder `cineforge-ai`:

```powershell
cd "C:\Users\Sneha Jadhav\.gemini\antigravity-ide\scratch\cineforge-ai"
python -m uvicorn backend.main:app --reload --port 8000
```
> **Note**: Make sure you run this command from the **root folder** `cineforge-ai` (not inside `backend/`).

The backend API will run at **`http://127.0.0.1:8000`** (Swagger docs available at `http://127.0.0.1:8000/docs`).

### 3. Start the Frontend Dev Server (Terminal 2)
Open a second PowerShell window:

```powershell
cd "C:\Users\Sneha Jadhav\.gemini\antigravity-ide\scratch\cineforge-ai\frontend"
npm run dev
```

Open your browser at **`http://localhost:3000`**.

---

## 🎥 ComfyUI & Local LTX-Video Model Setup

To synthesize real videos locally with open-source models:

1. **Install ComfyUI**: Download ComfyUI Portable from [github.com/comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI).
2. **Download LTX-Video Model**:
   - Download `ltx-video-2b-v0.9.safetensors` from HuggingFace (`Lightricks/LTX-Video`).
   - Place it inside `ComfyUI/models/checkpoints/`.
3. **Install VHS Node**: Install `ComfyUI-VideoHelperSuite` via ComfyUI Manager (for MP4 output video combined node).
4. **Launch ComfyUI**: Start `run_nvidia_gpu.bat` (runs on default port `8188`).
5. Set `MODE=local` in `.env` or in the Studio Settings modal.

---

## ☁️ Free Cloud GPU Option (Google Colab / Kaggle Tunnel)

If your local PC does not have a dedicated NVIDIA GPU (e.g. integrated Intel/AMD graphics), you can run ComfyUI for **free on Google Colab or Kaggle**:

1. Open a Google Colab notebook with GPU runtime (T4 / L4).
2. Install ComfyUI and download the LTX-Video checkpoint:
   ```bash
   !git clone https://github.com/comfyanonymous/ComfyUI
   !pip install -r ComfyUI/requirements.txt
   !wget -O ComfyUI/models/checkpoints/ltx-video-2b-v0.9.safetensors https://huggingface.co/Lightricks/LTX-Video/resolve/main/ltx-video-2b-v0.9.safetensors
   ```
3. Expose ComfyUI port 8188 via LocalTunnel or ngrok:
   ```bash
   !npx localtunnel --port 8188
   ```
4. Copy the generated public tunnel URL (e.g. `https://cool-panda-42.loca.lt`).
5. Paste this URL into **Studio Settings -> ComfyUI Server URL** (or set `COMFYUI_URL` in `.env`).

---

## 🛠️ Troubleshooting Guide

- **`ModuleNotFoundError: No module named 'backend'`**:
  Ensure you launch uvicorn from the root directory `cineforge-ai` using `python -m uvicorn backend.main:app --reload --port 8000`.
- **VRAM Warning Banner in UI**:
  If your model requires more VRAM than detected, lower the sampling steps (e.g., 15 steps) or use 512p resolution.
- **OpenRouter 429 Rate Limit**:
  OpenRouter free models enforce rate limits (~10 requests/minute). If hit, CineForge AI automatically falls back to your original prompt with zero error popups.

---
*CineForge AI Studio v1.0.0*
