import React, { useState, useEffect } from 'react';
import { Sliders, ChevronDown, ChevronUp, Shuffle, AlertCircle } from 'lucide-react';
import type { AspectRatio, Resolution, ModelProfile } from '../types/cineforge';

interface ControlsSectionProps {
  models: ModelProfile[];
  selectedModelId: string;
  onChangeModel: (modelId: string) => void;
  duration: number;
  onChangeDuration: (d: number) => void;
  aspectRatio: AspectRatio;
  onChangeAspectRatio: (ar: AspectRatio) => void;
  resolution: Resolution;
  onChangeResolution: (res: Resolution) => void;
  fps: number;
  onChangeFps: (fps: number) => void;
  seed: number;
  onChangeSeed: (seed: number) => void;
  isFixedSeed: boolean;
  onChangeIsFixedSeed: (fixed: boolean) => void;
  steps: number;
  onChangeSteps: (steps: number) => void;
  guidance: number;
  onChangeGuidance: (guidance: number) => void;
  negativePrompt: string;
  onChangeNegativePrompt: (neg: string) => void;
  hardwareVramGb?: number | null;
}

export const ControlsSection: React.FC<ControlsSectionProps> = ({
  models,
  selectedModelId,
  onChangeModel,
  duration,
  onChangeDuration,
  aspectRatio,
  onChangeAspectRatio,
  resolution,
  onChangeResolution,
  fps,
  onChangeFps,
  seed,
  onChangeSeed,
  isFixedSeed,
  onChangeIsFixedSeed,
  steps,
  onChangeSteps,
  guidance,
  onChangeGuidance,
  negativePrompt,
  onChangeNegativePrompt,
  hardwareVramGb,
}) => {
  const [showAdvanced, setShowAdvanced] = useState(false);

  const activeModel = models.find((m) => m.id === selectedModelId) || models[0];

  const supportedResolutions: Resolution[] = activeModel.supportedResolutions;

  useEffect(() => {
    if (!supportedResolutions.includes(resolution)) {
      onChangeResolution(supportedResolutions[supportedResolutions.length - 1]);
    }
  }, [selectedModelId]);

  const showVramWarning =
    hardwareVramGb !== undefined &&
    hardwareVramGb !== null &&
    hardwareVramGb < activeModel.requiredVramGb;

  return (
    <div className="w-full space-y-4">
      {showVramWarning && (
        <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0 text-amber-400" />
          <span>
            <strong>VRAM Warning:</strong> {activeModel.name} requires at least {activeModel.requiredVramGb}GB VRAM (detected: {hardwareVramGb}GB). Generation may fall back to CPU or take longer.
          </span>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-3">
        <div className="space-y-1.5 lg:col-span-1">
          <label className="block text-xs font-semibold text-slate-300">Model Engine</label>
          <select
            value={selectedModelId}
            onChange={(e) => onChangeModel(e.target.value)}
            className="w-full px-3 py-2 rounded-xl bg-slate-900/90 border border-slate-700/80 text-slate-100 text-xs font-medium focus:outline-none focus:border-purple-500"
          >
            {models.map((m) => (
              <option key={m.id} value={m.id}>
                {m.name} ({m.requiredVramGb}GB VRAM)
              </option>
            ))}
          </select>
        </div>

        <div className="space-y-1.5">
          <label className="block text-xs font-semibold text-slate-300">Duration</label>
          <div className="grid grid-cols-3 gap-1 p-1 rounded-xl bg-slate-900/90 border border-slate-800">
            {[5, 10, 15].map((d) => (
              <button
                type="button"
                key={d}
                onClick={() => onChangeDuration(d)}
                className={`py-1 rounded-lg text-xs font-semibold transition-all ${
                  duration === d
                    ? 'bg-purple-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {d}s
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-1.5">
          <label className="block text-xs font-semibold text-slate-300">Aspect Ratio</label>
          <div className="grid grid-cols-4 gap-1 p-1 rounded-xl bg-slate-900/90 border border-slate-800">
            {(['16:9', '9:16', '1:1', '4:5'] as AspectRatio[]).map((ar) => (
              <button
                type="button"
                key={ar}
                onClick={() => onChangeAspectRatio(ar)}
                className={`py-1 rounded-lg text-[11px] font-semibold transition-all ${
                  aspectRatio === ar
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {ar}
              </button>
            ))}
          </div>
        </div>

        <div className="space-y-1.5">
          <label className="block text-xs font-semibold text-slate-300">Resolution</label>
          <div className="flex items-center space-x-1 p-1 rounded-xl bg-slate-900/90 border border-slate-800">
            {(['512p', '720p', '1080p'] as Resolution[]).map((res) => {
              const isSupported = activeModel.supportedResolutions.includes(res);
              if (!isSupported) return null;
              return (
                <button
                  type="button"
                  key={res}
                  onClick={() => onChangeResolution(res)}
                  className={`flex-1 py-1 rounded-lg text-xs font-semibold transition-all ${
                    resolution === res
                      ? 'bg-cyan-600 text-white shadow-sm'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {res}
                </button>
              );
            })}
          </div>
        </div>

        <div className="space-y-1.5">
          <label className="block text-xs font-semibold text-slate-300">Framerate (FPS)</label>
          <div className="grid grid-cols-3 gap-1 p-1 rounded-xl bg-slate-900/90 border border-slate-800">
            {[16, 24, 30].map((f) => {
              const isSupported = activeModel.supportedFps.includes(f);
              return (
                <button
                  type="button"
                  key={f}
                  disabled={!isSupported}
                  onClick={() => onChangeFps(f)}
                  className={`py-1 rounded-lg text-xs font-semibold transition-all ${
                    !isSupported
                      ? 'opacity-30 cursor-not-allowed text-slate-600'
                      : fps === f
                      ? 'bg-purple-600 text-white shadow-sm'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {f}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      <div className="pt-2">
        <button
          type="button"
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex items-center space-x-1.5 text-xs font-semibold text-slate-400 hover:text-purple-300 transition-colors"
        >
          <Sliders className="w-3.5 h-3.5 text-purple-400" />
          <span>Advanced Pipeline Settings</span>
          {showAdvanced ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>

        {showAdvanced && (
          <div className="mt-3 p-4 rounded-2xl glass-card border border-white/10 space-y-4 animate-fadeIn">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-1.5">
                <div className="flex justify-between items-center text-xs font-semibold text-slate-300">
                  <span>Seed</span>
                  <button
                    type="button"
                    onClick={() => onChangeIsFixedSeed(!isFixedSeed)}
                    className="text-[11px] text-purple-400 hover:underline flex items-center space-x-1"
                  >
                    <Shuffle className="w-3 h-3" />
                    <span>{isFixedSeed ? 'Fixed Seed' : 'Randomize'}</span>
                  </button>
                </div>
                {isFixedSeed ? (
                  <input
                    type="number"
                    value={seed}
                    onChange={(e) => onChangeSeed(parseInt(e.target.value) || 0)}
                    className="w-full px-3 py-1.5 rounded-xl bg-slate-950/80 border border-slate-700 text-xs font-mono text-slate-100"
                  />
                ) : (
                  <div className="w-full px-3 py-1.5 rounded-xl bg-slate-950/40 border border-slate-800 text-xs font-mono text-slate-500 italic flex items-center justify-between">
                    <span>Random per generation</span>
                    <Shuffle className="w-3.5 h-3.5 text-slate-600 animate-spin" />
                  </div>
                )}
              </div>

              <div className="space-y-1.5">
                <div className="flex justify-between items-center text-xs font-semibold text-slate-300">
                  <span>Sampling Steps</span>
                  <span className="font-mono text-cyan-400 font-bold">{steps}</span>
                </div>
                <input
                  type="range"
                  min={10}
                  max={50}
                  step={1}
                  value={steps}
                  onChange={(e) => onChangeSteps(parseInt(e.target.value))}
                  className="w-full accent-cyan-500 cursor-pointer"
                />
              </div>

              <div className="space-y-1.5">
                <div className="flex justify-between items-center text-xs font-semibold text-slate-300">
                  <span>CFG Guidance</span>
                  <span className="font-mono text-purple-400 font-bold">{guidance.toFixed(1)}</span>
                </div>
                <input
                  type="range"
                  min={1.0}
                  max={15.0}
                  step={0.5}
                  value={guidance}
                  onChange={(e) => onChangeGuidance(parseFloat(e.target.value))}
                  className="w-full accent-purple-500 cursor-pointer"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="block text-xs font-semibold text-slate-300">
                Negative Prompt (What to exclude)
              </label>
              <textarea
                value={negativePrompt}
                onChange={(e) => onChangeNegativePrompt(e.target.value)}
                rows={2}
                placeholder="blurry, low quality, static, distorted faces, compression artifacts..."
                className="w-full px-3 py-2 rounded-xl bg-slate-950/80 border border-slate-700/80 text-xs text-slate-200 focus:outline-none focus:border-purple-500 resize-none"
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
