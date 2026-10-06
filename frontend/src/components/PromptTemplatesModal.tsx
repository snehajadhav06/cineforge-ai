import React, { useState } from 'react';
import { X, Sparkles } from 'lucide-react';
import type { PromptTemplate } from '../types/cineforge';

interface PromptTemplatesModalProps {
  isOpen: boolean;
  onClose: () => void;
  templates: PromptTemplate[];
  onSelectTemplate: (template: PromptTemplate) => void;
}

export const PromptTemplatesModal: React.FC<PromptTemplatesModalProps> = ({
  isOpen,
  onClose,
  templates,
  onSelectTemplate,
}) => {
  const [selectedCategory, setSelectedCategory] = useState<string>('All');

  if (!isOpen) return null;

  const categories = ['All', 'Cinematic', 'Anime/Stylized', 'Nature', 'Sci-Fi'];

  const filteredTemplates =
    selectedCategory === 'All'
      ? templates
      : templates.filter((t) => t.category === selectedCategory);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md animate-fadeIn">
      <div className="relative w-full max-w-2xl glass-panel rounded-2xl border border-white/10 p-6 shadow-2xl overflow-hidden max-h-[85vh] flex flex-col">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center space-x-3 mb-4">
          <div className="p-2.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-400">
            <Sparkles className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white my-0">Prompt Inspiration Library</h2>
            <p className="text-xs text-slate-400">Pre-built high performance cinematic video prompts</p>
          </div>
        </div>

        <div className="flex items-center space-x-2 pb-4 border-b border-slate-800 overflow-x-auto">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
                selectedCategory === cat
                  ? 'bg-amber-500 text-slate-950 font-bold shadow-md'
                  : 'bg-slate-900/80 text-slate-400 hover:text-slate-200 border border-slate-800'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        <div className="flex-1 overflow-y-auto py-4 space-y-3 pr-1">
          {filteredTemplates.map((tpl) => (
            <div
              key={tpl.id}
              className="p-4 rounded-xl glass-card border border-white/5 hover:border-amber-500/40 transition-all space-y-2 group"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-amber-300">{tpl.title}</span>
                <span className="px-2 py-0.5 rounded-md bg-slate-900 text-[10px] text-slate-400 font-mono">
                  {tpl.category}
                </span>
              </div>
              <p className="text-xs text-slate-200 leading-relaxed font-sans">{tpl.prompt}</p>
              {tpl.negativePrompt && (
                <p className="text-[11px] text-slate-500 italic">
                  <strong>Neg:</strong> {tpl.negativePrompt}
                </p>
              )}
              <div className="pt-2 flex justify-end">
                <button
                  onClick={() => {
                    onSelectTemplate(tpl);
                    onClose();
                  }}
                  className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 transition-colors flex items-center space-x-1.5"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Use Prompt</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
