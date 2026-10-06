import React from 'react';
import { X, Cpu, HardDrive, Zap, CheckCircle2, AlertTriangle } from 'lucide-react';
import type { SystemHardware } from '../types/cineforge';

interface HardwareModalProps {
  isOpen: boolean;
  onClose: () => void;
  hardware: SystemHardware;
}

export const HardwareModal: React.FC<HardwareModalProps> = ({ isOpen, onClose, hardware }) => {
  if (!isOpen) return null;

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
          <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
            <Cpu className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white my-0">Hardware Diagnostic Panel</h2>
            <p className="text-xs text-slate-400">Detected compute resources & local engine status</p>
          </div>
        </div>

        <div className="space-y-4">
          <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Zap className="w-4 h-4 text-purple-400" />
              <div>
                <p className="text-xs font-semibold text-slate-200">ComfyUI Backend Engine</p>
                <p className="text-[11px] text-slate-400">{hardware.comfyuiUrl}</p>
              </div>
            </div>
            {hardware.comfyuiConnected ? (
              <span className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Connected</span>
              </span>
            ) : (
              <span className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/30">
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>Mock Mode Active</span>
              </span>
            )}
          </div>

          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="font-semibold text-slate-300 flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5 text-slate-400" /> CPU ({hardware.cpuCores} Cores)
              </span>
              <span className="text-cyan-400 font-mono">{hardware.cpuUsagePercent}% Used</span>
            </div>
            <p className="text-[11px] text-slate-400 truncate">{hardware.cpuName}</p>
            <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-cyan-500 to-indigo-500 transition-all duration-500"
                style={{ width: `${hardware.cpuUsagePercent}%` }}
              />
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="font-semibold text-slate-300 flex items-center gap-1.5">
                <HardDrive className="w-3.5 h-3.5 text-slate-400" /> System Memory (RAM)
              </span>
              <span className="text-purple-400 font-mono">
                {hardware.ramUsedGb.toFixed(1)} GB / {hardware.ramTotalGb.toFixed(1)} GB
              </span>
            </div>
            <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-purple-500 to-indigo-500 transition-all duration-500"
                style={{ width: `${(hardware.ramUsedGb / hardware.ramTotalGb) * 100}%` }}
              />
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="font-semibold text-slate-300 flex items-center gap-1.5">
                <Zap className="w-3.5 h-3.5 text-amber-400" /> Dedicated GPU & VRAM
              </span>
              <span className="font-mono text-slate-300">
                {hardware.cudaAvailable ? (
                  <span className="text-emerald-400 font-semibold">CUDA Ready</span>
                ) : (
                  <span className="text-slate-400">CPU Fallback</span>
                )}
              </span>
            </div>

            {hardware.gpuName ? (
              <>
                <p className="text-xs text-slate-200 font-medium">{hardware.gpuName}</p>
                <div className="flex justify-between text-[11px] text-slate-400 font-mono">
                  <span>VRAM: {hardware.vramUsedGb?.toFixed(1)} GB used</span>
                  <span>Total: {hardware.vramTotalGb?.toFixed(1)} GB</span>
                </div>
                <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-amber-500 to-rose-500 transition-all duration-500"
                    style={{
                      width: hardware.vramTotalGb
                        ? `${((hardware.vramUsedGb || 0) / hardware.vramTotalGb) * 100}%`
                        : '0%',
                    }}
                  />
                </div>
              </>
            ) : (
              <div className="p-2.5 rounded-lg bg-slate-950/70 text-[11px] text-slate-400 border border-slate-800 flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0" />
                <span>
                  No discrete NVIDIA CUDA GPU detected. Models will run via CPU/integrated graphics or high-speed Mock Mode.
                </span>
              </div>
            )}
          </div>
        </div>

        <div className="mt-6 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white transition-colors"
          >
            Close Diagnostics
          </button>
        </div>
      </div>
    </div>
  );
};
