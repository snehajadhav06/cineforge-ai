import React from 'react';
import { Video, Cpu, Settings, Sparkles, Server, AlertTriangle } from 'lucide-react';
import type { SystemHardware } from '../types/cineforge';

interface NavbarProps {
  hardware: SystemHardware;
  ffmpegInstalled?: boolean;
  onOpenHardware: () => void;
  onOpenSettings: () => void;
  onOpenTemplates: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  hardware,
  ffmpegInstalled = true,
  onOpenHardware,
  onOpenSettings,
  onOpenTemplates,
}) => {
  return (
    <div className="w-full flex flex-col">
      {/* Warning Banner if FFmpeg is Missing */}
      {!ffmpegInstalled && (
        <div className="w-full py-2 px-4 bg-rose-500/90 text-white text-xs font-semibold flex items-center justify-center space-x-2 shadow-md">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          <span>
            <strong>System Warning:</strong> FFmpeg binary is not detected. Please ensure FFmpeg is installed to generate playable MP4 clips.
          </span>
        </div>
      )}

      <header className="sticky top-0 z-40 w-full glass-panel border-b border-white/10 px-4 lg:px-8 py-3.5 flex items-center justify-between shadow-lg">
        <div className="flex items-center space-x-3">
          <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-purple-600 to-cyan-400 p-0.5 glow-purple">
            <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
              <Video className="w-5 h-5 text-purple-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold bg-gradient-to-r from-white via-slate-200 to-purple-300 bg-clip-text text-transparent my-0 leading-tight">
                CineForge AI
              </h1>
              <span className="px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider text-purple-300 bg-purple-950/60 border border-purple-500/30 rounded-full">
                Local-First
              </span>
            </div>
            <p className="text-xs text-slate-400">Open-Source AI Video Studio</p>
          </div>
        </div>

        <div className="hidden md:flex items-center space-x-3">
          <button
            onClick={onOpenTemplates}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-800/70 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-700/60 transition-all hover:border-purple-500/40"
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            <span>Prompt Ideas</span>
          </button>

          <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-900/80 border border-slate-800 text-xs">
            <Server className="w-3.5 h-3.5 text-indigo-400" />
            <span className="text-slate-400">Mode:</span>
            <span className="font-semibold text-indigo-300 uppercase">{hardware.mode}</span>
          </div>
        </div>

        <div className="flex items-center space-x-2 lg:space-x-3">
          <button
            onClick={onOpenHardware}
            className="flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-900/90 hover:bg-slate-800 border border-slate-700/80 transition-all"
          >
            <Cpu className="w-3.5 h-3.5 text-cyan-400" />
            <span className="hidden sm:inline text-slate-300">
              {hardware.gpuName ? hardware.gpuName.split(' ')[0] : 'CPU Mode'}
            </span>
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          </button>

          <button
            onClick={onOpenSettings}
            className="p-2 rounded-lg bg-slate-900/80 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-700/80 transition-colors"
            title="App Settings"
          >
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </header>
    </div>
  );
};
