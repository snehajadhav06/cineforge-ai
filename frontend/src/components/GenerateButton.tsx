import React from 'react';
import { Video, Loader2, Sparkles } from 'lucide-react';

interface GenerateButtonProps {
  onGenerate: () => void;
  isGenerating: boolean;
  progress?: number;
  currentStep?: number;
  totalSteps?: number;
  disabled?: boolean;
}

export const GenerateButton: React.FC<GenerateButtonProps> = ({
  onGenerate,
  isGenerating,
  progress = 0,
  currentStep = 0,
  totalSteps = 25,
  disabled = false,
}) => {
  return (
    <div className="w-full pt-2">
      <button
        type="button"
        onClick={onGenerate}
        disabled={isGenerating || disabled}
        className={`relative w-full py-4 px-6 rounded-2xl font-bold text-base tracking-wide shadow-2xl transition-all overflow-hidden flex items-center justify-center space-x-3 border ${
          isGenerating || disabled
            ? 'bg-slate-800/80 border-slate-700 text-slate-500 cursor-not-allowed opacity-60'
            : 'bg-gradient-to-r from-indigo-600 via-purple-600 to-cyan-500 hover:from-indigo-500 hover:to-cyan-400 border-white/20 text-white transform hover:-translate-y-0.5 glow-purple active:translate-y-0'
        }`}
      >
        {/* Animated Background Shimmer when generating */}
        {isGenerating && (
          <div
            className="absolute inset-0 bg-gradient-to-r from-indigo-600/30 via-cyan-400/40 to-purple-600/30 transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        )}

        <div className="relative z-10 flex items-center space-x-3">
          {isGenerating ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin text-cyan-300" />
              <span>
                Generating Video... {Math.round(progress)}% (Step {currentStep}/{totalSteps})
              </span>
            </>
          ) : (
            <>
              <Video className="w-5 h-5 text-cyan-300" />
              <span>Generate AI Video</span>
              <Sparkles className="w-4 h-4 text-amber-300 animate-pulse" />
            </>
          )}
        </div>
      </button>
    </div>
  );
};
