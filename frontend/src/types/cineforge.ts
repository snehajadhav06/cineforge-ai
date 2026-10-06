export type GenerationMode = 'text-to-video' | 'image-to-video';
export type AspectRatio = '16:9' | '9:16' | '1:1' | '4:5';
export type Resolution = '512p' | '720p' | '1080p';

export interface ModelProfile {
  id: string;
  name: string;
  provider: string;
  requiredVramGb: number;
  recommendedVramGb: number;
  supportedResolutions: Resolution[];
  supportedRatios: AspectRatio[];
  supportedFps: number[];
  description: string;
  isDefault?: boolean;
}

export interface GenerationJob {
  id: string;
  prompt: string;
  enhancedPrompt?: string;
  negativePrompt: string;
  mode: GenerationMode;
  referenceImageUrl?: string;
  modelId: string;
  duration: number; // in seconds
  aspectRatio: AspectRatio;
  resolution: Resolution;
  fps: number;
  seed: number;
  isFixedSeed: boolean;
  steps: number;
  guidance: number;
  status: 'idle' | 'queued' | 'processing' | 'completed' | 'failed';
  progress: number; // 0 - 100
  currentStep: number;
  totalSteps: number;
  etaSeconds: number;
  videoUrl?: string;
  thumbnailUrl?: string;
  createdAt: string;
  isFavorite?: boolean;
  sha256Hash?: string;
  isMock?: boolean;
  providerBadge?: string;
  errorMessage?: string;
}

export interface SystemHardware {
  mode: 'mock' | 'local' | 'cloud';
  comfyuiConnected: boolean;
  comfyuiUrl: string;
  cpuName: string;
  cpuCores: number;
  cpuUsagePercent: number;
  ramTotalGb: number;
  ramUsedGb: number;
  gpuName: string | null;
  vramTotalGb: number | null;
  vramUsedGb: number | null;
  cudaAvailable: boolean;
}

export interface PromptTemplate {
  id: string;
  title: string;
  prompt: string;
  category: 'Cinematic' | 'Anime/Stylized' | 'Nature' | 'Sci-Fi' | 'Photorealistic';
  negativePrompt?: string;
}
