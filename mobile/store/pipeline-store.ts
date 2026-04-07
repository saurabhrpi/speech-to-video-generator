import { create } from 'zustand';
import * as Haptics from 'expo-haptics';
import { apiPost } from '@/lib/api-client';
import { resolveVideoUrl } from '@/lib/api-client';
import { streamJob } from '@/lib/streaming';
import { calcProgress, nextStopAfter, detectLastCompletedPhase, extractPartial } from '@/lib/pipeline';
import { NUM_STAGES } from '@/lib/constants';
import type { PipelineState } from '@/lib/types';

interface PipelineStore {
  busy: boolean;
  statusMsg: string;
  progress: number;
  videoUrl: string | null;
  jsonOut: string;
  pipelineState: (PipelineState & Record<string, any>) | null;
  phaseCompleted: string | null;
  pipelineError: string | null;
  formPayload: Record<string, any> | null;
  stepByStep: boolean;
  abortController: AbortController | null;

  setStepByStep: (v: boolean) => void;
  runPipeline: (
    payload: Record<string, any>,
    stopAfter: string | null,
    resumeState: Record<string, any> | null,
  ) => Promise<void>;
  handleContinue: () => void;
  handleResume: () => void;
  handleGenerateRemainingImages: () => void;
  handleGenerateRemainingVideos: () => void;
  handleStop: () => void;
  handleStartOver: () => void;
}

export const usePipelineStore = create<PipelineStore>((set, get) => ({
  busy: false,
  statusMsg: '',
  progress: 0,
  videoUrl: null,
  jsonOut: '',
  pipelineState: null,
  phaseCompleted: null,
  pipelineError: null,
  formPayload: null,
  stepByStep: false,
  abortController: null,

  setStepByStep: (v) => set({ stepByStep: v }),

  runPipeline: async (payload, stopAfter, resumeState) => {
    const ac = new AbortController();
    set({
      busy: true,
      pipelineError: null,
      phaseCompleted: null,
      statusMsg: 'Starting...',
      progress: 0,
      abortController: ac,
      formPayload: payload,
    });

    try {
      const body: Record<string, any> = { ...payload };
      if (stopAfter) body.stop_after = stopAfter;
      if (resumeState) body.resume_state = resumeState;

      const { job_id } = await apiPost<{ job_id: string }>(
        '/api/generate/timelapse',
        body,
      );

      const jobCallbacks = {
        onProgress: (phase: string | null, step: number, total: number, message: string) => {
          set({
            progress: calcProgress(phase, step, total, stopAfter),
            statusMsg: message || `Phase: ${phase}`,
          });
        },
        onPartialResult: (partial: Record<string, any>) => {
          const extracted = extractPartial(partial);
          if (extracted) {
            set({ pipelineState: { ...get().pipelineState, ...extracted } });
          }
        },
      };

      const result = await streamJob(job_id, jobCallbacks, ac.signal);

      if (!result) {
        set({ busy: false, statusMsg: '' });
        return;
      }

      // Extract final state
      const finalPartial = extractPartial(result);
      if (finalPartial) {
        set({ pipelineState: { ...get().pipelineState, ...finalPartial } });
      }

      // Check if pipeline stopped at a phase (step-by-step) or completed
      const lastPhase = detectLastCompletedPhase(result);
      const videoUrl = result.video_url || result.stitched_url;

      if (videoUrl) {
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        set({
          videoUrl: resolveVideoUrl(videoUrl),
          jsonOut: JSON.stringify(result, null, 2),
          progress: 100,
          statusMsg: 'Done!',
        });
      } else if (lastPhase) {
        Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
        set({ phaseCompleted: lastPhase });
      }

      set({ busy: false, progress: videoUrl ? 100 : 0, statusMsg: videoUrl ? 'Done!' : '' });
    } catch (err: any) {
      if (err.message === 'Aborted') {
        set({ busy: false, statusMsg: 'Stopped.' });
        return;
      }
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      const state = get().pipelineState;
      const lastPhase = state ? detectLastCompletedPhase(state) : null;
      set({
        busy: false,
        pipelineError: err.message || 'Pipeline failed',
        phaseCompleted: null,
        statusMsg: '',
      });
    }
  },

  handleContinue: () => {
    const { formPayload, pipelineState, phaseCompleted, stepByStep } = get();
    if (!formPayload || !pipelineState) return;
    const next = nextStopAfter(phaseCompleted);
    const stop = stepByStep ? next : null;
    get().runPipeline(formPayload, stop, pipelineState);
  },

  handleResume: () => {
    const { formPayload, pipelineState, stepByStep } = get();
    if (!formPayload || !pipelineState) return;
    const last = detectLastCompletedPhase(pipelineState);
    const next = nextStopAfter(last);
    const stop = stepByStep ? next : null;
    set({ pipelineError: null });
    get().runPipeline(formPayload, stop, pipelineState);
  },

  handleGenerateRemainingImages: () => {
    const { formPayload, pipelineState } = get();
    if (!formPayload || !pipelineState) return;
    set({ pipelineError: null });
    get().runPipeline(formPayload, `stage_${NUM_STAGES}`, pipelineState);
  },

  handleGenerateRemainingVideos: () => {
    const { formPayload, pipelineState } = get();
    if (!formPayload || !pipelineState) return;
    set({ pipelineError: null });
    get().runPipeline(formPayload, null, pipelineState);
  },

  handleStop: () => {
    const { abortController } = get();
    abortController?.abort();
    set({ busy: false, statusMsg: 'Stopped.', abortController: null });
  },

  handleStartOver: () => {
    const { abortController } = get();
    abortController?.abort();
    set({
      busy: false,
      statusMsg: '',
      progress: 0,
      videoUrl: null,
      jsonOut: '',
      pipelineState: null,
      phaseCompleted: null,
      pipelineError: null,
      formPayload: null,
      abortController: null,
    });
  },
}));
