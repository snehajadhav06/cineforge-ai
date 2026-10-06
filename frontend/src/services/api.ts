import type { GenerationJob, SystemHardware, GenerationMode, AspectRatio, Resolution } from '../types/cineforge';

export interface GeneratePayload {
  prompt: string;
  negative_prompt?: string;
  mode?: GenerationMode;
  reference_image_url?: string;
  model_id?: string;
  duration?: number;
  aspect_ratio?: AspectRatio;
  resolution?: Resolution;
  fps?: number;
  seed?: number;
  is_fixed_seed?: boolean;
  steps?: number;
  guidance?: number;
}

export function resolveMediaUrl(path?: string | null): string {
  if (!path) return '';
  if (path.startsWith('http://') || path.startsWith('https://') || path.startsWith('data:')) {
    return path;
  }
  const baseUrl = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${baseUrl}${cleanPath}`;
}

export async function fetchHealth(): Promise<{ ffmpeg: boolean; generated_dir: string; mode: string } | null> {
  try {
    const res = await fetch('/api/health');
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function fetchSystemHardware(): Promise<SystemHardware | null> {
  try {
    const res = await fetch('/api/system');
    if (!res.ok) return null;
    const data = await res.json();
    return {
      mode: data.mode,
      comfyuiConnected: data.comfyui_connected,
      comfyuiUrl: data.comfyui_url,
      cpuName: data.cpu_name,
      cpuCores: data.cpu_cores,
      cpuUsagePercent: data.cpu_usage_percent,
      ramTotalGb: data.ram_total_gb,
      ramUsedGb: data.ram_used_gb,
      gpuName: data.gpu_name,
      vramTotalGb: data.vram_total_gb,
      vramUsedGb: data.vram_used_gb,
      cudaAvailable: data.cuda_available,
    };
  } catch {
    return null;
  }
}

export async function fetchGenerations(search?: string, favoriteOnly?: boolean, mode?: string): Promise<GenerationJob[]> {
  try {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (favoriteOnly) params.append('favorite_only', 'true');
    if (mode) params.append('mode', mode);

    const res = await fetch(`/api/generations?${params.toString()}`);
    if (!res.ok) return [];
    const list = await res.json();
    return list.map((item: any) => ({
      id: item.id,
      prompt: item.prompt,
      enhancedPrompt: item.enhanced_prompt,
      negativePrompt: item.negative_prompt,
      mode: item.mode,
      referenceImageUrl: item.reference_image_url,
      modelId: item.model_id,
      duration: item.duration,
      aspectRatio: item.aspect_ratio,
      resolution: item.resolution,
      fps: item.fps,
      seed: item.seed,
      isFixedSeed: item.is_fixed_seed,
      steps: item.steps,
      guidance: item.guidance,
      status: item.status,
      progress: item.progress,
      currentStep: item.current_step,
      totalSteps: item.total_steps,
      etaSeconds: item.eta_seconds,
      videoUrl: resolveMediaUrl(item.video_url),
      thumbnailUrl: resolveMediaUrl(item.thumbnail_url),
      createdAt: item.created_at,
      isFavorite: item.is_favorite,
      sha256Hash: item.sha256_hash,
      isMock: item.is_mock,
      providerBadge: item.provider_badge,
      errorMessage: item.error_message || item.error,
    }));
  } catch {
    return [];
  }
}

export async function generateVideoApi(payload: GeneratePayload): Promise<GenerationJob> {
  const endpoint = payload.mode === 'image-to-video' ? '/api/generate/image-to-video' : '/api/generate';
  const res = await fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Generation failed' }));
    throw new Error(err.detail || 'Failed to start generation');
  }

  const item = await res.json();
  return {
    id: item.id,
    prompt: item.prompt,
    enhancedPrompt: item.enhanced_prompt,
    negativePrompt: item.negative_prompt,
    mode: item.mode,
    referenceImageUrl: item.reference_image_url,
    modelId: item.model_id,
    duration: item.duration,
    aspectRatio: item.aspect_ratio,
    resolution: item.resolution,
    fps: item.fps,
    seed: item.seed,
    isFixedSeed: item.is_fixed_seed,
    steps: item.steps,
    guidance: item.guidance,
    status: item.status,
    progress: item.progress,
    currentStep: item.current_step,
    totalSteps: item.total_steps,
    etaSeconds: item.eta_seconds,
    videoUrl: resolveMediaUrl(item.video_url),
    thumbnailUrl: resolveMediaUrl(item.thumbnail_url),
    createdAt: item.created_at,
    isFavorite: item.is_favorite,
    sha256Hash: item.sha256_hash,
    isMock: item.is_mock,
    providerBadge: item.provider_badge,
    errorMessage: item.error_message || item.error,
  };
}

export async function enhancePromptApi(prompt: string): Promise<{ original_prompt: string; enhanced_prompt: string; cached: boolean; notice?: string }> {
  const res = await fetch('/api/prompt/enhance', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt }),
  });
  if (!res.ok) {
    throw new Error('Prompt enhancement failed');
  }
  return await res.json();
}

export function subscribeProgress(jobId: string, onEvent: (data: any) => void): () => void {
  const eventSource = new EventSource(`/api/generations/${jobId}/stream`);

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.video_url) {
        data.video_url = resolveMediaUrl(data.video_url);
      }
      if (data.thumbnail_url) {
        data.thumbnail_url = resolveMediaUrl(data.thumbnail_url);
      }
      onEvent(data);
      if (data.status === 'completed' || data.status === 'failed') {
        eventSource.close();
      }
    } catch {
      // Ignore
    }
  };

  eventSource.onerror = () => {
    eventSource.close();
  };

  return () => {
    eventSource.close();
  };
}

export async function toggleFavoriteApi(jobId: string): Promise<boolean> {
  try {
    const res = await fetch(`/api/generations/${jobId}/favorite`, { method: 'PATCH' });
    if (res.ok) {
      const data = await res.json();
      return data.is_favorite;
    }
  } catch {
    // Ignore
  }
  return false;
}

export async function deleteGenerationApi(jobId: string): Promise<void> {
  await fetch(`/api/generations/${jobId}`, { method: 'DELETE' });
}
