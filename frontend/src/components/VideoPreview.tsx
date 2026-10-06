import React, { useRef, useState, useEffect } from 'react';
import {
  Download,
  RotateCcw,
  Grid,
  Layers,
  Trash2,
  Film,
  Sparkles,
  Clock,
  Zap,
  AlertTriangle,
  Server,
} from 'lucide-react';
import type { GenerationJob } from '../types/cineforge';

interface VideoPreviewProps {
  currentJob: GenerationJob | null;
  onDownload?: (job: GenerationJob) => void;
  onRegenerate?: (job: GenerationJob) => void;
  onCreateVariation?: (job: GenerationJob) => void;
  onExtend?: (job: GenerationJob) => void;
  onDelete?: (jobId: string) => void;
}

export const VideoPreview: React.FC<VideoPreviewProps> = ({
  currentJob,
  onDownload,
  onRegenerate,
  onCreateVariation,
  onExtend,
  onDelete,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [videoError, setVideoError] = useState<string | null>(null);

  useEffect(() => {
    setVideoError(null);
  }, [currentJob?.id, currentJob?.videoUrl]);

  const getAspectClass = (ratio?: string) => {
    switch (ratio) {
      case '9:16':
        return 'aspect-[9/16] max-h-[500px]';
      case '1:1':
        return 'aspect-square max-h-[480px]';
      case '4:5':
        return 'aspect-[4/5] max-h-[480px]';
      case '16:9':
      default:
        return 'aspect-video max-h-[480px]';
    }
  };

  const isGenerating = currentJob?.status === 'processing' || currentJob?.status === 'queued';
  const isFailed = currentJob?.status === 'failed';

  return (
    <div className="w-full space-y-4">
      {/* Main Container */}
      <div className="relative w-full rounded-2xl glass-panel border border-white/10 overflow-hidden shadow-2xl flex items-center justify-center bg-slate-950/80">
        {/* Failed Status Box */}
        {isFailed && (
          <div className="w-full aspect-video max-h-[440px] flex flex-col items-center justify-center p-6 text-center bg-rose-950/20 border border-rose-500/30">
            <div className="p-3 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/30 mb-3">
              <AlertTriangle className="w-7 h-7" />
            </div>
            <h3 className="text-base font-bold text-rose-300 mb-1">Generation Failed</h3>
            <p className="text-xs text-slate-300 max-w-md font-mono bg-black/60 p-3 rounded-xl border border-rose-500/20 leading-relaxed mb-4">
              {currentJob?.errorMessage || 'An error occurred during AI video synthesis.'}
            </p>
            <p className="text-[11px] text-slate-400">
              Ensure local ComfyUI is running or configure a valid HuggingFace Space in .env.
            </p>
          </div>
        )}

        {/* Active Progress Overlay */}
        {isGenerating && (
          <div className="absolute inset-0 z-20 bg-slate-950/90 backdrop-blur-md flex flex-col items-center justify-center p-6 text-center">
            <div className="relative mb-6">
              <div className="w-20 h-20 rounded-full border-4 border-purple-500/20 border-t-purple-500 border-r-cyan-400 animate-spin" />
              <div className="absolute inset-0 flex items-center justify-center text-purple-400 font-bold text-sm font-mono">
                {Math.round(currentJob.progress)}%
              </div>
            </div>

            <h3 className="text-base font-bold text-white mb-1">Synthesizing AI Video...</h3>
            <p className="text-xs text-slate-400 max-w-md line-clamp-2 italic mb-4">
              "{currentJob.prompt}"
            </p>

            <div className="w-full max-w-md space-y-2">
              <div className="flex justify-between items-center text-xs text-slate-300 font-mono">
                <span className="flex items-center space-x-1 text-cyan-400">
                  <Zap className="w-3.5 h-3.5" />
                  <span>
                    Step {currentJob.currentStep} / {currentJob.totalSteps}
                  </span>
                </span>
                <span className="flex items-center space-x-1 text-slate-400">
                  <Clock className="w-3.5 h-3.5" />
                  <span>ETA: ~{currentJob.etaSeconds}s</span>
                </span>
              </div>

              <div className="w-full h-2.5 bg-slate-900 rounded-full overflow-hidden p-0.5 border border-slate-800">
                <div
                  className="h-full bg-gradient-to-r from-indigo-500 via-purple-500 to-cyan-400 rounded-full transition-all duration-300 shadow-[0_0_12px_rgba(168,85,247,0.5)]"
                  style={{ width: `${currentJob.progress}%` }}
                />
              </div>

              <p className="text-[11px] text-slate-500 mt-2">
                Pipeline Model: {currentJob.modelId.toUpperCase()}
              </p>
            </div>
          </div>
        )}

        {/* Video Player Display */}
        {currentJob?.videoUrl && !isGenerating && !isFailed ? (
          <div className={`relative w-full ${getAspectClass(currentJob.aspectRatio)} bg-black flex items-center justify-center group`}>
            {videoError ? (
              <div className="p-6 text-center space-y-3">
                <div className="p-3 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/30 w-12 h-12 mx-auto flex items-center justify-center">
                  <AlertTriangle className="w-6 h-6" />
                </div>
                <h4 className="text-sm font-bold text-rose-300">Video Loading Error</h4>
                <p className="text-xs text-slate-400 max-w-md font-mono break-all">{videoError}</p>
                <p className="text-[11px] text-slate-500">Failed URL: {currentJob.videoUrl}</p>
              </div>
            ) : (
              <video
                ref={videoRef}
                src={currentJob.videoUrl}
                poster={currentJob.thumbnailUrl}
                controls
                playsInline
                preload="metadata"
                className="w-full h-full object-contain"
                loop
                onError={() => {
                  setVideoError(`Unable to load MP4 stream from URL: ${currentJob.videoUrl}`);
                }}
              />
            )}

            {/* Provider Result Badge Overlay */}
            <div className="absolute top-3 left-3 z-10 pointer-events-none">
              {currentJob.providerBadge ? (
                <span className="px-3 py-1 rounded-full bg-indigo-600/90 text-white text-[10px] font-bold tracking-wider shadow-lg border border-indigo-400/50 flex items-center space-x-1.5 backdrop-blur-md">
                  <Server className="w-3 h-3 text-cyan-300" />
                  <span>{currentJob.providerBadge}</span>
                </span>
              ) : currentJob.isMock ? (
                <span className="px-3 py-1 rounded-full bg-amber-500/90 text-slate-950 text-[10px] font-bold tracking-wider uppercase shadow-lg border border-amber-300/50 flex items-center space-x-1 backdrop-blur-md">
                  <AlertTriangle className="w-3 h-3 text-slate-950" />
                  <span>MOCK: placeholder video, not AI-generated</span>
                </span>
              ) : (
                <span className="px-3 py-1 rounded-full bg-purple-600/90 text-white text-[10px] font-bold tracking-wider shadow-lg border border-purple-400/50 flex items-center space-x-1 backdrop-blur-md">
                  <Sparkles className="w-3 h-3 text-amber-300" />
                  <span>AI: ComfyUI (LTX-Video)</span>
                </span>
              )}
            </div>

            {/* Top Right Badges */}
            <div className="absolute top-3 right-3 flex items-center space-x-2 z-10 pointer-events-none">
              <span className="px-2.5 py-1 rounded-lg bg-black/70 backdrop-blur-md text-[11px] font-mono font-semibold text-cyan-300 border border-cyan-500/30">
                {currentJob.resolution}
              </span>
              <span className="px-2.5 py-1 rounded-lg bg-black/70 backdrop-blur-md text-[11px] font-mono text-purple-300 border border-purple-500/30">
                {currentJob.fps} FPS
              </span>
            </div>
          </div>
        ) : !isGenerating && !isFailed ? (
          /* Empty State Placeholder */
          <div className="w-full aspect-video max-h-[440px] flex flex-col items-center justify-center p-8 text-center bg-gradient-to-b from-slate-950 via-slate-900/60 to-slate-950">
            <div className="relative mb-4">
              <div className="w-16 h-16 rounded-2xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 glow-purple">
                <Film className="w-8 h-8" />
              </div>
              <Sparkles className="w-5 h-5 text-cyan-400 absolute -top-2 -right-2 animate-bounce" />
            </div>
            <h2 className="text-lg font-bold text-white mb-1.5">No Video Generated Yet</h2>
            <p className="text-xs text-slate-400 max-w-md mb-4 leading-relaxed">
              Enter a prompt below or pick a template to synthesize high-quality AI video using local open-source models or HuggingFace Cloud Spaces.
            </p>
          </div>
        ) : null}
      </div>

      {/* Action Toolbar below video */}
      {currentJob?.videoUrl && !isGenerating && !isFailed && (
        <div className="glass-card rounded-xl p-3 flex flex-wrap items-center justify-between gap-2 border border-white/5">
          <div className="flex items-center space-x-2">
            <button
              onClick={() => onDownload?.(currentJob)}
              className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white shadow-md transition-all glow-indigo"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download MP4</span>
            </button>

            <button
              onClick={() => onRegenerate?.(currentJob)}
              className="flex items-center space-x-1.5 px-3 py-2 rounded-xl text-xs font-medium bg-slate-800/80 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5 text-purple-400" />
              <span>Generate Again</span>
            </button>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => onCreateVariation?.(currentJob)}
              className="flex items-center space-x-1.5 px-3 py-2 rounded-xl text-xs font-medium bg-slate-800/80 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
              title="Generate 4 variations with different seeds"
            >
              <Grid className="w-3.5 h-3.5 text-cyan-400" />
              <span>Variations (x4)</span>
            </button>

            <button
              onClick={() => onExtend?.(currentJob)}
              className="flex items-center space-x-1.5 px-3 py-2 rounded-xl text-xs font-medium bg-slate-800/80 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
              title="Extend video continuation (+5s)"
            >
              <Layers className="w-3.5 h-3.5 text-amber-400" />
              <span>Extend (+5s)</span>
            </button>

            <button
              onClick={() => onDelete?.(currentJob.id)}
              className="p-2 rounded-xl text-xs font-medium bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 transition-colors"
              title="Delete Video"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
