import { useState, useEffect, useRef } from 'react';
import { Navbar } from './components/Navbar';
import { VideoPreview } from './components/VideoPreview';
import { PromptSection } from './components/PromptSection';
import { ControlsSection } from './components/ControlsSection';
import { GenerateButton } from './components/GenerateButton';
import { MyVideosGrid } from './components/MyVideosGrid';
import { HardwareModal } from './components/HardwareModal';
import { SettingsModal } from './components/SettingsModal';
import { PromptTemplatesModal } from './components/PromptTemplatesModal';
import { VariationModal } from './components/VariationModal';
import { GenerationDetailsModal } from './components/GenerationDetailsModal';
import {
  MOCK_MODELS,
  MOCK_TEMPLATES,
  MOCK_HARDWARE,
  MOCK_GENERATIONS,
} from './data/mockData';
import type {
  GenerationJob,
  GenerationMode,
  AspectRatio,
  Resolution,
  PromptTemplate,
  SystemHardware,
} from './types/cineforge';
import {
  fetchSystemHardware,
  fetchHealth,
  fetchGenerations,
  generateVideoApi,
  enhancePromptApi,
  subscribeProgress,
  deleteGenerationApi,
  toggleFavoriteApi,
} from './services/api';

export function App() {
  // Navigation & Modals state
  const [isHardwareOpen, setIsHardwareOpen] = useState(false);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isTemplatesOpen, setIsTemplatesOpen] = useState(false);
  const [isVariationOpen, setIsVariationOpen] = useState(false);
  const [variationBaseJob, setVariationBaseJob] = useState<GenerationJob | null>(null);

  // Details Modal
  const [isDetailsOpen, setIsDetailsOpen] = useState(false);
  const [detailsJob, setDetailsJob] = useState<GenerationJob | null>(null);

  // Form Parameters
  const [prompt, setPrompt] = useState('Cinematic drone shot of a futuristic cyberpunk city alley bathed in rain and vibrant magenta neon reflections, 8k resolution, volumetric fog, high detail motion.');
  const [negativePrompt, setNegativePrompt] = useState(
    'blurry, low quality, static, distorted faces, compression artifacts'
  );
  const [mode, setMode] = useState<GenerationMode>('text-to-video');
  const [referenceImage, setReferenceImage] = useState<string | null>(null);
  const [selectedModelId, setSelectedModelId] = useState('ltx-video');
  const [duration, setDuration] = useState<number>(5);
  const [aspectRatio, setAspectRatio] = useState<AspectRatio>('16:9');
  const [resolution, setResolution] = useState<Resolution>('512p');
  const [fps, setFps] = useState<number>(24);
  const [seed, setSeed] = useState<number>(Math.floor(Math.random() * 9000000) + 1000000);
  const [isFixedSeed, setIsFixedSeed] = useState(false);
  const [steps, setSteps] = useState<number>(25);
  const [guidance, setGuidance] = useState<number>(6.5);

  // Enhancer & Throttle state
  const [isEnhancing, setIsEnhancing] = useState(false);
  const [enhanceNotice, setEnhanceNotice] = useState<string | null>(null);
  const enhanceCountRef = useRef<number>(0);
  const lastEnhanceTimeRef = useRef<number>(Date.now());

  // Generations History & Current Job State
  const [generations, setGenerations] = useState<GenerationJob[]>(MOCK_GENERATIONS);
  const [currentJob, setCurrentJob] = useState<GenerationJob | null>(MOCK_GENERATIONS[0]);
  const [isGenerating, setIsGenerating] = useState(false);

  // Hardware State
  const [hardware, setHardware] = useState<SystemHardware>(MOCK_HARDWARE);
  const [ffmpegInstalled, setFfmpegInstalled] = useState<boolean>(true);

  // Load hardware & past generations on mount
  useEffect(() => {
    async function loadData() {
      const health = await fetchHealth();
      if (health) {
        setFfmpegInstalled(health.ffmpeg);
      }

      const hw = await fetchSystemHardware();
      if (hw) setHardware(hw);

      const dbGenerations = await fetchGenerations();
      if (dbGenerations && dbGenerations.length > 0) {
        setGenerations(dbGenerations);
        setCurrentJob(dbGenerations[0]);
      }
    }
    loadData();
  }, []);

  const handleEnhancePrompt = async () => {
    if (!prompt.trim()) return;

    const now = Date.now();
    if (now - lastEnhanceTimeRef.current < 60000) {
      enhanceCountRef.current += 1;
    } else {
      enhanceCountRef.current = 1;
      lastEnhanceTimeRef.current = now;
    }

    if (enhanceCountRef.current > 10) {
      setEnhanceNotice('Rate limit hit (max 10 enhancements/min). Falling back to original prompt.');
      setTimeout(() => setEnhanceNotice(null), 4000);
      return;
    }

    setIsEnhancing(true);
    setEnhanceNotice(null);

    try {
      const res = await enhancePromptApi(prompt);
      setPrompt(res.enhanced_prompt);
      if (res.notice) setEnhanceNotice(res.notice);
    } catch {
      setPrompt(`Masterpiece 8k cinematic video shot, volumetric lighting, hyper-detailed motion: ${prompt.trim()}`);
    } finally {
      setIsEnhancing(false);
    }
  };

  const handleGenerateVideo = async () => {
    if (!prompt.trim() && mode === 'text-to-video') return;

    const effectiveSeed = isFixedSeed ? seed : Math.floor(Math.random() * 9000000) + 1000000;
    setIsGenerating(true);

    try {
      const newJob = await generateVideoApi({
        prompt: prompt.trim() || 'Reference motion video',
        negative_prompt: negativePrompt,
        mode,
        reference_image_url: referenceImage || undefined,
        model_id: selectedModelId,
        duration,
        aspect_ratio: aspectRatio,
        resolution,
        fps,
        seed: effectiveSeed,
        is_fixed_seed: isFixedSeed,
        steps,
        guidance,
      });

      setCurrentJob(newJob);
      setGenerations((prev) => [newJob, ...prev.filter((j) => j.id !== newJob.id)]);

      subscribeProgress(newJob.id, (event) => {
        setCurrentJob((prev) => {
          if (!prev) return null;
          return {
            ...prev,
            status: event.status || prev.status,
            progress: event.progress !== undefined ? event.progress : prev.progress,
            currentStep: event.current_step !== undefined ? event.current_step : prev.currentStep,
            etaSeconds: event.eta_seconds !== undefined ? event.eta_seconds : prev.etaSeconds,
            videoUrl: event.video_url || prev.videoUrl,
            thumbnailUrl: event.thumbnail_url || prev.thumbnailUrl,
          };
        });

        setGenerations((prev) =>
          prev.map((j) =>
            j.id === newJob.id
              ? {
                  ...j,
                  status: event.status || j.status,
                  progress: event.progress !== undefined ? event.progress : j.progress,
                  currentStep: event.current_step !== undefined ? event.current_step : j.currentStep,
                  etaSeconds: event.eta_seconds !== undefined ? event.eta_seconds : j.etaSeconds,
                  videoUrl: event.video_url || j.videoUrl,
                  thumbnailUrl: event.thumbnail_url || j.thumbnailUrl,
                }
              : j
          )
        );

        if (event.status === 'completed' || event.status === 'failed') {
          setIsGenerating(false);
        }
      });
    } catch {
      const jobId = `gen-${Date.now()}`;
      const fallbackJob: GenerationJob = {
        id: jobId,
        prompt: prompt.trim() || 'Reference motion video',
        negativePrompt,
        mode,
        referenceImageUrl: referenceImage || undefined,
        modelId: selectedModelId,
        duration,
        aspectRatio,
        resolution,
        fps,
        seed: effectiveSeed,
        isFixedSeed,
        steps,
        guidance,
        status: 'processing',
        progress: 0,
        currentStep: 0,
        totalSteps: steps,
        etaSeconds: Math.round(steps * 0.4),
        createdAt: new Date().toISOString(),
      };

      setCurrentJob(fallbackJob);
      setGenerations((prev) => [fallbackJob, ...prev]);

      let stepCount = 0;
      const interval = setInterval(() => {
        stepCount += 1;
        const pct = Math.min(100, Math.round((stepCount / steps) * 100));

        if (stepCount >= steps) {
          clearInterval(interval);
          const completedJob: GenerationJob = {
            ...fallbackJob,
            status: 'completed',
            progress: 100,
            currentStep: steps,
            etaSeconds: 0,
            videoUrl: '/generated/projects/default/videos/sample.mp4',
            thumbnailUrl:
              referenceImage ||
              'https://images.unsplash.com/photo-1519501025264-65ba15a82390?auto=format&fit=crop&w=800&q=80',
          };
          setCurrentJob(completedJob);
          setGenerations((prev) => prev.map((j) => (j.id === jobId ? completedJob : j)));
          setIsGenerating(false);
        } else {
          setCurrentJob((prev) => (prev ? { ...prev, progress: pct, currentStep: stepCount } : null));
        }
      }, 200);
    }
  };

  const handleDownload = (job: GenerationJob) => {
    if (!job.videoUrl) return;
    const a = document.createElement('a');
    a.href = `/api/generations/${job.id}/download`;
    a.download = `cineforge-${job.id}.mp4`;
    a.click();
  };

  const handleRegenerate = (job: GenerationJob) => {
    setPrompt(job.prompt);
    setNegativePrompt(job.negativePrompt);
    setMode(job.mode);
    if (job.referenceImageUrl) setReferenceImage(job.referenceImageUrl);
    setSelectedModelId(job.modelId);
    setDuration(job.duration);
    setAspectRatio(job.aspectRatio);
    setResolution(job.resolution);
    setFps(job.fps);
    setSteps(job.steps);
    setGuidance(job.guidance);
  };

  const handleCreateVariation = (job: GenerationJob) => {
    setVariationBaseJob(job);
    setIsVariationOpen(true);
  };

  const handleSelectVariationSeed = (varSeed: number) => {
    if (!variationBaseJob) return;
    setPrompt(variationBaseJob.prompt);
    setIsFixedSeed(true);
    setSeed(varSeed);
    setTimeout(() => {
      handleGenerateVideo();
    }, 100);
  };

  const handleExtend = (job: GenerationJob) => {
    const extendedPrompt = `${job.prompt} - continuing motion into second sequence (+5s)`;
    setPrompt(extendedPrompt);
    setDuration(10);
    setTimeout(() => {
      handleGenerateVideo();
    }, 100);
  };

  const handleDelete = async (jobId: string) => {
    setGenerations((prev) => prev.filter((j) => j.id !== jobId));
    if (currentJob?.id === jobId) {
      setCurrentJob(generations.find((j) => j.id !== jobId) || null);
    }
    await deleteGenerationApi(jobId).catch(() => {});
  };

  const handleToggleFavorite = async (jobId: string) => {
    const newFavState = await toggleFavoriteApi(jobId);
    setGenerations((prev) =>
      prev.map((j) => (j.id === jobId ? { ...j, isFavorite: newFavState } : j))
    );
    if (currentJob?.id === jobId) {
      setCurrentJob((prev) => (prev ? { ...prev, isFavorite: newFavState } : null));
    }
  };

  const handleOpenDetails = (job: GenerationJob) => {
    setDetailsJob(job);
    setIsDetailsOpen(true);
  };

  const handleSelectTemplate = (tpl: PromptTemplate) => {
    setPrompt(tpl.prompt);
    if (tpl.negativePrompt) {
      setNegativePrompt(tpl.negativePrompt);
    }
  };

  return (
    <div className="min-h-screen bg-[#090a0f] text-slate-100 flex flex-col font-sans selection:bg-purple-500 selection:text-white">
      <Navbar
        hardware={hardware}
        ffmpegInstalled={ffmpegInstalled}
        onOpenHardware={() => setIsHardwareOpen(true)}
        onOpenSettings={() => setIsSettingsOpen(true)}
        onOpenTemplates={() => setIsTemplatesOpen(true)}
      />

      <main className="flex-1 w-full max-w-7xl mx-auto px-4 lg:px-8 py-6 space-y-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          <div className="lg:col-span-5 space-y-5">
            <PromptSection
              prompt={prompt}
              onChangePrompt={setPrompt}
              mode={mode}
              onChangeMode={setMode}
              referenceImage={referenceImage}
              onUploadImage={setReferenceImage}
              onEnhancePrompt={handleEnhancePrompt}
              isEnhancing={isEnhancing}
              enhanceNotice={enhanceNotice}
            />

            <ControlsSection
              models={MOCK_MODELS}
              selectedModelId={selectedModelId}
              onChangeModel={setSelectedModelId}
              duration={duration}
              onChangeDuration={setDuration}
              aspectRatio={aspectRatio}
              onChangeAspectRatio={setAspectRatio}
              resolution={resolution}
              onChangeResolution={setResolution}
              fps={fps}
              onChangeFps={setFps}
              seed={seed}
              onChangeSeed={setSeed}
              isFixedSeed={isFixedSeed}
              onChangeIsFixedSeed={setIsFixedSeed}
              steps={steps}
              onChangeSteps={setSteps}
              guidance={guidance}
              onChangeGuidance={setGuidance}
              negativePrompt={negativePrompt}
              onChangeNegativePrompt={setNegativePrompt}
              hardwareVramGb={hardware.vramTotalGb}
            />

            <GenerateButton
              onGenerate={handleGenerateVideo}
              isGenerating={isGenerating}
              progress={currentJob?.progress || 0}
              currentStep={currentJob?.currentStep || 0}
              totalSteps={steps}
              disabled={(!prompt.trim() && mode === 'text-to-video') || prompt.length > 2000}
            />
          </div>

          <div className="lg:col-span-7">
            <VideoPreview
              currentJob={currentJob}
              onDownload={handleDownload}
              onRegenerate={handleRegenerate}
              onCreateVariation={handleCreateVariation}
              onExtend={handleExtend}
              onDelete={handleDelete}
            />
          </div>
        </div>

        <section className="pt-4 border-t border-slate-800/80">
          <MyVideosGrid
            generations={generations}
            currentJobId={currentJob?.id}
            onSelectJob={setCurrentJob}
            onOpenDetails={handleOpenDetails}
            onDownload={handleDownload}
            onRegenerate={handleRegenerate}
            onCreateVariation={handleCreateVariation}
            onExtend={handleExtend}
            onDelete={handleDelete}
            onToggleFavorite={handleToggleFavorite}
          />
        </section>
      </main>

      <HardwareModal
        isOpen={isHardwareOpen}
        onClose={() => setIsHardwareOpen(false)}
        hardware={hardware}
      />

      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
      />

      <PromptTemplatesModal
        isOpen={isTemplatesOpen}
        onClose={() => setIsTemplatesOpen(false)}
        templates={MOCK_TEMPLATES}
        onSelectTemplate={handleSelectTemplate}
      />

      <VariationModal
        isOpen={isVariationOpen}
        onClose={() => setIsVariationOpen(false)}
        baseJob={variationBaseJob}
        onSelectVariation={handleSelectVariationSeed}
      />

      <GenerationDetailsModal
        isOpen={isDetailsOpen}
        onClose={() => setIsDetailsOpen(false)}
        job={detailsJob}
        onDownload={handleDownload}
        onRegenerate={handleRegenerate}
        onCreateVariation={handleCreateVariation}
        onExtend={handleExtend}
        onDelete={handleDelete}
      />
    </div>
  );
}
