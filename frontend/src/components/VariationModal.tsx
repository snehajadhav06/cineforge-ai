import React from 'react';
import { X, Grid, RefreshCw, Sparkles } from 'lucide-react';
import type { GenerationJob } from '../types/cineforge';

interface VariationModalProps {
  isOpen: boolean;
  onClose: () => void;
  baseJob: GenerationJob | null;
  onSelectVariation: (seed: number) => void;
}

export const VariationModal: React.FC<VariationModalProps> = ({
  isOpen,
  onClose,
  baseJob,
  onSelectVariation,
}) => {
  if (!isOpen || !baseJob) return null;

  const seeds = [
    baseJob.seed + 101,
    baseJob.seed + 404,
    baseJob.seed + 777,
    baseJob.seed + 999,
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fadeIn">
      <div className="relative w-full max-w-3xl glass-panel rounded-2xl border border-white/10 p-6 shadow-2xl overflow-hidden flex flex-col">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center space-x-3 mb-4">
          <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
            <Grid className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white my-0">Variation Matrix (4 Seeds)</h2>
            <p className="text-xs text-slate-400">
              Exploring seed variations for: "{baseJob.prompt.slice(0, 60)}..."
            </p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 py-2">
          {seeds.map((s, idx) => (
            <div
              key={s}
              className="relative aspect-video rounded-xl overflow-hidden bg-slate-950 border border-slate-800 group hover:border-cyan-500/60 transition-all flex flex-col justify-between"
            >
              <div className="relative w-full h-full bg-slate-900 flex items-center justify-center">
                {baseJob.thumbnailUrl ? (
                  <img
                    src={baseJob.thumbnailUrl}
                    alt={`Variation ${idx + 1}`}
                    className="w-full h-full object-cover opacity-85 group-hover:scale-105 transition-transform"
                  />
                ) : (
                  <Sparkles className="w-8 h-8 text-cyan-400" />
                )}

                <div className="absolute inset-0 bg-black/30 group-hover:bg-black/10 transition-colors" />

                <div className="absolute top-2 left-2 px-2 py-0.5 rounded bg-black/70 backdrop-blur-md text-[10px] font-mono text-cyan-300">
                  Variation #{idx + 1} (Seed: {s})
                </div>

                <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={() => {
                      onSelectVariation(s);
                      onClose();
                    }}
                    className="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs shadow-lg transition-transform transform scale-95 hover:scale-100 flex items-center space-x-1.5"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    <span>Generate with Seed {s}</span>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-4 pt-3 border-t border-slate-800 flex justify-between items-center text-xs text-slate-400">
          <span>Same settings ({baseJob.resolution}, {baseJob.fps}fps, {baseJob.duration}s), 4 distinct seeds.</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-medium text-xs transition-colors"
          >
            Close Matrix
          </button>
        </div>
      </div>
    </div>
  );
};
