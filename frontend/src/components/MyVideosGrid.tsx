import React, { useState } from 'react';
import { Play, Download, Trash2, Heart, RotateCcw, Grid, Layers, Film, Search, Info } from 'lucide-react';
import type { GenerationJob } from '../types/cineforge';

interface MyVideosGridProps {
  generations: GenerationJob[];
  currentJobId?: string;
  onSelectJob: (job: GenerationJob) => void;
  onOpenDetails: (job: GenerationJob) => void;
  onDownload: (job: GenerationJob) => void;
  onRegenerate: (job: GenerationJob) => void;
  onCreateVariation: (job: GenerationJob) => void;
  onExtend: (job: GenerationJob) => void;
  onDelete: (jobId: string) => void;
  onToggleFavorite: (jobId: string) => void;
}

export const MyVideosGrid: React.FC<MyVideosGridProps> = ({
  generations,
  currentJobId,
  onSelectJob,
  onOpenDetails,
  onDownload,
  onRegenerate,
  onCreateVariation,
  onExtend,
  onDelete,
  onToggleFavorite,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [filterMode, setFilterMode] = useState<'all' | 'favorites' | 'text-to-video' | 'image-to-video'>('all');

  const filteredGenerations = generations.filter((job) => {
    if (filterMode === 'favorites' && !job.isFavorite) return false;
    if (filterMode === 'text-to-video' && job.mode !== 'text-to-video') return false;
    if (filterMode === 'image-to-video' && job.mode !== 'image-to-video') return false;

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      return (
        job.prompt.toLowerCase().includes(q) ||
        job.modelId.toLowerCase().includes(q) ||
        (job.enhancedPrompt && job.enhancedPrompt.toLowerCase().includes(q))
      );
    }
    return true;
  });

  return (
    <div className="w-full space-y-4">
      {/* Header with Search & Filter Tabs */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-sm font-bold text-slate-200 uppercase tracking-wider my-0 flex items-center space-x-2">
          <Film className="w-4 h-4 text-purple-400" />
          <span>My Video Generations ({filteredGenerations.length})</span>
        </h2>

        <div className="flex flex-wrap items-center gap-2">
          {/* Search bar */}
          <div className="relative flex items-center">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 pointer-events-none" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search prompts..."
              className="pl-8 pr-3 py-1.5 rounded-xl bg-slate-900/90 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-purple-500 w-44"
            />
          </div>

          {/* Filter Tabs */}
          <div className="flex items-center space-x-1 p-1 rounded-xl bg-slate-900/90 border border-slate-800">
            {(['all', 'favorites', 'text-to-video', 'image-to-video'] as const).map((m) => (
              <button
                key={m}
                onClick={() => setFilterMode(m)}
                className={`px-2.5 py-1 rounded-lg text-[11px] font-semibold capitalize transition-all ${
                  filterMode === m
                    ? 'bg-purple-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {m === 'text-to-video' ? 'Text' : m === 'image-to-video' ? 'Image' : m}
              </button>
            ))}
          </div>
        </div>
      </div>

      {filteredGenerations.length === 0 ? (
        <div className="p-8 rounded-2xl glass-card border border-white/5 text-center text-slate-500 space-y-1">
          <Film className="w-8 h-8 mx-auto mb-2 text-slate-600" />
          <p className="text-xs font-medium text-slate-400">No matching videos found.</p>
          <p className="text-[11px] text-slate-600">Try adjusting your search query or filters above.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filteredGenerations.map((job) => {
            const isSelected = job.id === currentJobId;

            return (
              <div
                key={job.id}
                className={`group relative rounded-2xl overflow-hidden glass-card border transition-all duration-300 ${
                  isSelected
                    ? 'border-purple-500 shadow-[0_0_20px_rgba(168,85,247,0.3)] ring-1 ring-purple-500'
                    : 'border-white/10 hover:border-slate-700'
                }`}
              >
                <div
                  onClick={() => onSelectJob(job)}
                  className="relative aspect-video bg-black cursor-pointer overflow-hidden"
                >
                  {job.thumbnailUrl ? (
                    <img
                      src={job.thumbnailUrl}
                      alt={job.prompt}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                    />
                  ) : (
                    <div className="w-full h-full bg-slate-900 flex items-center justify-center">
                      <Film className="w-8 h-8 text-slate-700" />
                    </div>
                  )}

                  <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                    <div className="p-3 rounded-full bg-white/20 backdrop-blur-md text-white">
                      <Play className="w-5 h-5 fill-current ml-0.5" />
                    </div>
                  </div>

                  <div className="absolute top-2 left-2 right-2 flex justify-between items-center pointer-events-none">
                    <span className="px-2 py-0.5 rounded-md bg-black/70 backdrop-blur-md text-[10px] font-mono text-cyan-300 font-semibold border border-white/10">
                      {job.resolution}
                    </span>
                    <div className="flex items-center space-x-1 pointer-events-auto">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onOpenDetails(job);
                        }}
                        className="p-1 rounded-md bg-black/60 hover:bg-black/80 backdrop-blur-md text-slate-300 hover:text-white"
                        title="View Details"
                      >
                        <Info className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onToggleFavorite(job.id);
                        }}
                        className="p-1 rounded-md bg-black/60 hover:bg-black/80 backdrop-blur-md text-amber-400"
                        title="Favorite"
                      >
                        <Heart
                          className={`w-3.5 h-3.5 ${job.isFavorite ? 'fill-amber-400 text-amber-400' : 'text-slate-400'}`}
                        />
                      </button>
                    </div>
                  </div>

                  <div className="absolute bottom-2 right-2 px-2 py-0.5 rounded bg-black/80 text-[10px] font-mono text-slate-300">
                    {job.duration}s
                  </div>
                </div>

                <div className="p-3 space-y-2">
                  <p className="text-xs text-slate-200 font-medium line-clamp-2 leading-snug" title={job.prompt}>
                    {job.prompt}
                  </p>

                  <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono pt-1 border-t border-slate-800">
                    <span>{job.modelId.toUpperCase()}</span>
                    <span>{new Date(job.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  </div>

                  <div className="flex items-center justify-between pt-1 gap-1">
                    <button
                      onClick={() => onDownload(job)}
                      className="p-1.5 rounded-lg bg-slate-900 hover:bg-indigo-600 text-slate-300 hover:text-white transition-colors"
                      title="Download MP4"
                    >
                      <Download className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => onRegenerate(job)}
                      className="p-1.5 rounded-lg bg-slate-900 hover:bg-purple-600 text-slate-300 hover:text-white transition-colors"
                      title="Generate Again"
                    >
                      <RotateCcw className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => onCreateVariation(job)}
                      className="p-1.5 rounded-lg bg-slate-900 hover:bg-cyan-600 text-slate-300 hover:text-white transition-colors"
                      title="4 Variations"
                    >
                      <Grid className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => onExtend(job)}
                      className="p-1.5 rounded-lg bg-slate-900 hover:bg-amber-600 text-slate-300 hover:text-white transition-colors"
                      title="Extend Video"
                    >
                      <Layers className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => onDelete(job.id)}
                      className="p-1.5 rounded-lg bg-slate-900 hover:bg-rose-600 text-slate-400 hover:text-white transition-colors ml-auto"
                      title="Delete"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
