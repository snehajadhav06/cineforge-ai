import React, { useState, useRef } from 'react';
import { Sparkles, Upload, Image as ImageIcon, X, Copy, Check, Info } from 'lucide-react';
import type { GenerationMode } from '../types/cineforge';

interface PromptSectionProps {
  prompt: string;
  onChangePrompt: (val: string) => void;
  mode: GenerationMode;
  onChangeMode: (mode: GenerationMode) => void;
  referenceImage: string | null;
  onUploadImage: (url: string | null) => void;
  onEnhancePrompt: () => void;
  isEnhancing: boolean;
  enhanceNotice?: string | null;
}

export const PromptSection: React.FC<PromptSectionProps> = ({
  prompt,
  onChangePrompt,
  mode,
  onChangeMode,
  referenceImage,
  onUploadImage,
  onEnhancePrompt,
  isEnhancing,
  enhanceNotice,
}) => {
  const [copied, setCopied] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleCopy = () => {
    if (!prompt) return;
    navigator.clipboard.writeText(prompt);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleImageFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (evt) => {
        if (evt.target?.result) {
          onUploadImage(evt.target.result as string);
        }
      };
      reader.readAsDataURL(file);
    }
  };

  const isExceeded = prompt.length > 2000;

  return (
    <div className="w-full space-y-3">
      {/* Mode Switcher Tabs */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-1 p-1 rounded-xl bg-slate-900/90 border border-slate-800">
          <button
            type="button"
            onClick={() => onChangeMode('text-to-video')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              mode === 'text-to-video'
                ? 'bg-purple-600 text-white shadow-md glow-purple'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Text-to-Video
          </button>
          <button
            type="button"
            onClick={() => onChangeMode('image-to-video')}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              mode === 'image-to-video'
                ? 'bg-indigo-600 text-white shadow-md glow-indigo'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Image-to-Video
          </button>
        </div>

        {prompt && (
          <button
            type="button"
            onClick={handleCopy}
            className="flex items-center space-x-1 px-2.5 py-1 rounded-lg text-xs text-slate-400 hover:text-white bg-slate-900/60 border border-slate-800"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>
        )}
      </div>

      {/* Image Upload Box */}
      {mode === 'image-to-video' && (
        <div className="p-3.5 rounded-2xl glass-card border border-indigo-500/20 bg-indigo-950/20 space-y-2">
          <label className="block text-xs font-semibold text-indigo-300 flex items-center justify-between">
            <span className="flex items-center space-x-1.5">
              <ImageIcon className="w-4 h-4 text-indigo-400" />
              <span>Reference Starting Image</span>
            </span>
            {referenceImage && (
              <button
                type="button"
                onClick={() => onUploadImage(null)}
                className="text-[11px] text-rose-400 hover:underline flex items-center space-x-1"
              >
                <X className="w-3 h-3" />
                <span>Remove</span>
              </button>
            )}
          </label>

          {referenceImage ? (
            <div className="relative w-full h-32 rounded-xl overflow-hidden border border-indigo-500/30 bg-black flex items-center justify-center">
              <img src={referenceImage} alt="Reference" className="w-full h-full object-cover" />
            </div>
          ) : (
            <div
              onClick={() => fileInputRef.current?.click()}
              className="w-full h-28 rounded-xl border-2 border-dashed border-indigo-500/40 hover:border-indigo-400 bg-slate-950/50 hover:bg-indigo-950/40 cursor-pointer flex flex-col items-center justify-center transition-all p-3 text-center"
            >
              <Upload className="w-6 h-6 text-indigo-400 mb-1" />
              <p className="text-xs font-medium text-slate-200">Click to upload reference image</p>
              <p className="text-[10px] text-slate-400 mt-0.5">PNG, JPG, WEBP (Max 10MB)</p>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleImageFileChange}
                className="hidden"
              />
            </div>
          )}
        </div>
      )}

      {/* Main Text Prompt Box */}
      <div className={`relative glass-panel rounded-2xl border p-3 shadow-xl transition-all ${
        isExceeded ? 'border-rose-500/80 bg-rose-950/10' : 'border-white/10 focus-within:border-purple-500/50'
      }`}>
        <textarea
          value={prompt}
          onChange={(e) => onChangePrompt(e.target.value)}
          placeholder={
            mode === 'image-to-video'
              ? 'Describe the desired motion and camera action (e.g. slow zoom in, hair blowing in the wind)...'
              : 'Describe the video you want to create...'
          }
          rows={3}
          className="w-full bg-transparent text-slate-100 placeholder-slate-500 text-sm focus:outline-none resize-none leading-relaxed"
        />

        {enhanceNotice && (
          <div className="mb-2 p-2 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-300 text-[11px] flex items-center space-x-1.5">
            <Info className="w-3.5 h-3.5 flex-shrink-0" />
            <span>{enhanceNotice}</span>
          </div>
        )}

        <div className="flex items-center justify-between pt-2 border-t border-slate-800/80">
          <span className={`text-[11px] font-mono ${isExceeded ? 'text-rose-400 font-bold' : 'text-slate-500'}`}>
            {prompt.length} / 2000 chars {isExceeded && '(Exceeded Limit!)'}
          </span>

          <button
            type="button"
            onClick={onEnhancePrompt}
            disabled={isEnhancing || !prompt.trim() || isExceeded}
            className={`flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all ${
              isEnhancing || !prompt.trim() || isExceeded
                ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                : 'bg-gradient-to-r from-amber-500 via-purple-600 to-indigo-600 hover:from-amber-400 hover:to-indigo-500 text-white shadow-md glow-purple'
            }`}
          >
            <Sparkles className={`w-3.5 h-3.5 ${isEnhancing ? 'animate-spin' : 'text-amber-300'}`} />
            <span>{isEnhancing ? 'Enhancing...' : 'Enhance Prompt'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
