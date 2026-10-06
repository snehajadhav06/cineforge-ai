import React, { useState } from 'react';
import { X, Settings, Key, Server, Save } from 'lucide-react';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({ isOpen, onClose }) => {
  const [comfyUrl, setComfyUrl] = useState('http://127.0.0.1:8188');
  const [openRouterKey, setOpenRouterKey] = useState('');
  const [mode, setMode] = useState<'mock' | 'local' | 'cloud'>('mock');
  const [promptEnhancer, setPromptEnhancer] = useState<'openrouter' | 'ollama' | 'none'>('openrouter');
  const [openRouterModel, setOpenRouterModel] = useState('meta-llama/llama-3.2-3b-instruct:free');

  if (!isOpen) return null;

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md animate-fadeIn">
      <div className="relative w-full max-w-lg glass-panel rounded-2xl border border-white/10 p-6 shadow-2xl overflow-hidden">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center space-x-3 mb-6">
          <div className="p-2.5 rounded-xl bg-purple-500/10 border border-purple-500/30 text-purple-400">
            <Settings className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white my-0">Engine & API Settings</h2>
            <p className="text-xs text-slate-400">Configure ComfyUI address and OpenRouter free text keys</p>
          </div>
        </div>

        <form onSubmit={handleSave} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">Execution Mode</label>
            <div className="grid grid-cols-3 gap-2">
              {(['mock', 'local', 'cloud'] as const).map((m) => (
                <button
                  type="button"
                  key={m}
                  onClick={() => setMode(m)}
                  className={`py-2 px-3 rounded-xl text-xs font-medium border capitalize transition-all ${
                    mode === m
                      ? 'bg-purple-600/30 border-purple-500 text-purple-200 glow-purple'
                      : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700'
                  }`}
                >
                  {m} Engine
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center space-x-1.5">
              <Server className="w-3.5 h-3.5 text-cyan-400" />
              <span>ComfyUI Server URL</span>
            </label>
            <input
              type="text"
              value={comfyUrl}
              onChange={(e) => setComfyUrl(e.target.value)}
              placeholder="http://127.0.0.1:8188"
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950/80 border border-slate-800 text-slate-100 text-xs font-mono focus:outline-none focus:border-cyan-500"
            />
            <p className="text-[11px] text-slate-400 mt-1">Default local port is 8188 or remote tunnel URL (Colab/Kaggle).</p>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">Prompt Enhancer Provider</label>
            <select
              value={promptEnhancer}
              onChange={(e) => setPromptEnhancer(e.target.value as any)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950/80 border border-slate-800 text-slate-200 text-xs focus:outline-none focus:border-purple-500"
            >
              <option value="openrouter">OpenRouter (Free Models Only)</option>
              <option value="ollama">Ollama (Local LLM)</option>
              <option value="none">Disabled (No LLM Enhancement)</option>
            </select>
          </div>

          {promptEnhancer === 'openrouter' && (
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5 flex items-center space-x-1.5">
                <Key className="w-3.5 h-3.5 text-amber-400" />
                <span>OpenRouter API Key (Free Models Only)</span>
              </label>
              <input
                type="password"
                value={openRouterKey}
                onChange={(e) => setOpenRouterKey(e.target.value)}
                placeholder="sk-or-v1-..."
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950/80 border border-slate-800 text-slate-100 text-xs font-mono focus:outline-none focus:border-purple-500"
              />
              <p className="text-[11px] text-slate-400 mt-1">
                Used only for text tasks (prompt enhancement & vision captioning). No paid API calls.
              </p>
            </div>
          )}

          {promptEnhancer === 'openrouter' && (
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">Free LLM Model ID</label>
              <input
                type="text"
                value={openRouterModel}
                onChange={(e) => setOpenRouterModel(e.target.value)}
                placeholder="meta-llama/llama-3.2-3b-instruct:free"
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-950/80 border border-slate-800 text-slate-100 text-xs font-mono focus:outline-none focus:border-purple-500"
              />
            </div>
          )}

          <div className="pt-4 flex items-center justify-end space-x-3 border-t border-slate-800/80">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex items-center space-x-2 px-5 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white shadow-md transition-all glow-purple"
            >
              <Save className="w-4 h-4" />
              <span>Save Configuration</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
