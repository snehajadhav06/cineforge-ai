import React, { useState } from 'react';
import { X, Film, Copy, Check, Download, RotateCcw, Grid, Layers, Trash2, Hash, Calendar, Sliders } from 'lucide-react';
import type { GenerationJob } from '../types/cineforge';

interface GenerationDetailsModalProps {
  isOpen: boolean;
  onClose: () => void;
  job: GenerationJob | null;
  onDownload: (job: GenerationJob) => void;
  onRegenerate: (job: GenerationJob) => void;
  onCreateVariation: (job: GenerationJob) => void;
  onExtend: (job: GenerationJob) => void;
  onDelete: (jobId: string) => void;
}

export const GenerationDetailsModal: React.FC<GenerationDetailsModalProps> = ({
  isOpen,
  onClose,
  job,
  onDownload,
  onRegenerate,
  onCreateVariation,
  onExtend,
  onDelete,
}) => {
  const [copiedPrompt, setCopiedPrompt] = useState(false);

  if (!isOpen || !job) return null;

  const handleCopyPrompt = () => {
    navigator.clipboard.writeText(job.prompt);
    setCopiedPrompt(true);
    setTimeout(() => setCopiedPrompt(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fadeIn">
      <div className="relative w-full max-w-3xl glass-panel rounded-2xl border border-white/10 p-6 shadow-2xl overflow-hidden max-h-[90vh] flex flex-col">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Title */}
        <div className="flex items-center space-x-3 mb-4">
          <div className="p-2.5 rounded-xl bg-purple-500/10 border border-purple-500/30 text-purple-400">
            <Film className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white my-0">Generation Details</h2>
            <p className="text-xs text-slate-400 font-mono">ID: {job.id}</p>
          </div>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto space-y-4 pr-1">
          {/* Video / Thumbnail preview */}
          {job.videoUrl && (
            <div className="relative w-full aspect-video rounded-xl overflow-hidden bg-black border border-slate-800">
              <video
                src={job.videoUrl}
                poster={job.thumbnailUrl}
                className="w-full h-full object-contain"
                controls
                loop
              />
            </div>
          )}

          {/* Prompt Info Card */}
          <div className="p-4 rounded-xl glass-card border border-white/5 space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-purple-300 uppercase tracking-wider">Prompt</label>
              <button
                onClick={handleCopyPrompt}
                className="flex items-center space-x-1 px-2.5 py-1 rounded-lg text-[11px] bg-slate-800 text-slate-300 hover:text-white border border-slate-700"
              >
                {copiedPrompt ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copiedPrompt ? 'Copied' : 'Copy Prompt'}</span>
              </button>
            </div>
            <p className="text-xs text-slate-100 leading-relaxed font-sans">{job.prompt}</p>

            {job.enhancedPrompt && (
              <div className="pt-2 border-t border-slate-800">
                <label className="text-[11px] font-semibold text-amber-300 block mb-1">Enhanced Prompt</label>
                <p className="text-xs text-slate-300 italic">{job.enhancedPrompt}</p>
              </div>
            )}

            {job.negativePrompt && (
              <div className="pt-2 border-t border-slate-800">
                <label className="text-[11px] font-semibold text-rose-300 block mb-1">Negative Prompt</label>
                <p className="text-xs text-slate-400">{job.negativePrompt}</p>
              </div>
            )}
          </div>

          {/* Technical Specs Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-slate-500 block text-[10px] uppercase font-semibold">Model Engine</span>
              <span className="text-slate-200 font-bold font-mono">{job.modelId.toUpperCase()}</span>
            </div>
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-slate-500 block text-[10px] uppercase font-semibold">Resolution / Ratio</span>
              <span className="text-cyan-300 font-bold font-mono">{job.resolution} ({job.aspectRatio})</span>
            </div>
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-slate-500 block text-[10px] uppercase font-semibold">Framerate & Duration</span>
              <span className="text-purple-300 font-bold font-mono">{job.fps} FPS / {job.duration}s</span>
            </div>
            <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
              <span className="text-slate-500 block text-[10px] uppercase font-semibold">Seed</span>
              <span className="text-amber-300 font-bold font-mono">{job.seed}</span>
            </div>
          </div>

          {/* Advanced Pipeline Details */}
          <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-wrap justify-between text-xs gap-3 font-mono">
            <div className="flex items-center space-x-1.5">
              <Sliders className="w-3.5 h-3.5 text-cyan-400" />
              <span className="text-slate-400">Steps:</span>
              <span className="text-slate-100 font-bold">{job.steps}</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <span className="text-slate-400">CFG Guidance:</span>
              <span className="text-purple-300 font-bold">{job.guidance}</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <Calendar className="w-3.5 h-3.5 text-amber-400" />
              <span className="text-slate-400">Created:</span>
              <span className="text-slate-300">{new Date(job.createdAt).toLocaleString()}</span>
            </div>
          </div>

          {/* SHA256 Cache Hash */}
          {job.sha256Hash && (
            <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-[11px] font-mono flex items-center space-x-2 text-slate-400 overflow-x-auto">
              <Hash className="w-4 h-4 text-purple-400 flex-shrink-0" />
              <span>SHA256:</span>
              <span className="text-slate-200 select-all">{job.sha256Hash}</span>
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="mt-4 pt-3 border-t border-slate-800 flex flex-wrap justify-between items-center gap-2">
          <div className="flex items-center space-x-2">
            <button
              onClick={() => onDownload(job)}
              className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white shadow-md transition-all glow-indigo"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download MP4</span>
            </button>
            <button
              onClick={() => onRegenerate(job)}
              className="flex items-center space-x-1.5 px-3 py-2 rounded-xl text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5 text-purple-400" />
              <span>Regenerate</span>
            </button>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => onCreateVariation(job)}
              className="flex items-center space-x-1.5 px-3 py-2 rounded-xl text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
            >
              <Grid className="w-3.5 h-3.5 text-cyan-400" />
              <span>Variations</span>
            </button>
            <button
              onClick={() => onExtend(job)}
              className="flex items-center space-x-1.5 px-3 py-2 rounded-xl text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
            >
              <Layers className="w-3.5 h-3.5 text-amber-400" />
              <span>Extend (+5s)</span>
            </button>
            <button
              onClick={() => {
                onDelete(job.id);
                onClose();
              }}
              className="p-2 rounded-xl text-xs font-medium bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 transition-colors"
              title="Delete Video"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
