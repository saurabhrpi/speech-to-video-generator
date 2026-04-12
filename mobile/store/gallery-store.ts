import { create } from 'zustand';
import * as Haptics from 'expo-haptics';
import { activateKeepAwake, deactivateKeepAwake } from 'expo-keep-awake';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { apiPost, resolveVideoUrl } from '@/lib/api-client';
import { streamJob } from '@/lib/streaming';

const STORAGE_KEY = 'gallery_jobs';
const KEEP_AWAKE_TAG = 'gallery';

export interface GalleryJob {
  id: string;
  prompt: string;
  model: string;
  duration: number;
  status: 'generating' | 'completed' | 'failed';
  statusMsg: string;
  videoUrl: string | null;
  error: string | null;
  createdAt: number;
}

/** Module-level AbortControllers — not serialized */
const abortControllers = new Map<string, AbortController>();

interface GalleryStore {
  jobs: GalleryJob[];
  selectedJobId: string | null;

  startGeneration: (formData: FormData, meta: { prompt: string; model: string; duration: number }) => string;
  removeJob: (id: string) => void;
  selectJob: (id: string | null) => void;
  hydrate: () => Promise<void>;
}

function hasGenerating(jobs: GalleryJob[]): boolean {
  return jobs.some((j) => j.status === 'generating');
}

function persist(jobs: GalleryJob[]) {
  // Only persist completed/failed — generating jobs can't survive a restart
  const toSave = jobs.filter((j) => j.status !== 'generating');
  AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(toSave));
}

export const useGalleryStore = create<GalleryStore>((set, get) => ({
  jobs: [],
  selectedJobId: null,

  startGeneration: (formData, meta) => {
    const tempId = `temp_${Date.now()}`;
    const job: GalleryJob = {
      id: tempId,
      prompt: meta.prompt,
      model: meta.model,
      duration: meta.duration,
      status: 'generating',
      statusMsg: 'Submitting...',
      videoUrl: null,
      error: null,
      createdAt: Date.now(),
    };

    set((s) => ({ jobs: [job, ...s.jobs] }));
    activateKeepAwake(KEEP_AWAKE_TAG);

    // Fire-and-forget async — submit to API, then stream progress
    const ac = new AbortController();
    abortControllers.set(tempId, ac);

    (async () => {
      let jobId = tempId;
      try {
        const { job_id } = await apiPost<{ job_id: string }>(
          '/api/generate/speech-to-video',
          formData,
          true,
        );
        jobId = job_id;

        // Update the job ID from temp to real
        abortControllers.set(jobId, ac);
        abortControllers.delete(tempId);
        set((s) => ({
          jobs: s.jobs.map((j) => (j.id === tempId ? { ...j, id: jobId } : j)),
          selectedJobId: s.selectedJobId === tempId ? jobId : s.selectedJobId,
        }));

        const result = await streamJob(
          jobId,
          {
            onProgress: (_phase, _step, _total, message) => {
              set((s) => ({
                jobs: s.jobs.map((j) =>
                  j.id === jobId ? { ...j, statusMsg: message || 'Generating video...' } : j,
                ),
              }));
            },
            onPartialResult: () => {},
          },
          ac.signal,
        );

        if (result?.video_url) {
          Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
          set((s) => {
            const jobs = s.jobs.map((j) =>
              j.id === jobId
                ? { ...j, status: 'completed' as const, statusMsg: 'Done!', videoUrl: resolveVideoUrl(result.video_url) }
                : j,
            );
            persist(jobs);
            return { jobs };
          });
        } else {
          const err = result?.error;
          const errMsg = typeof err === 'string' ? err : JSON.stringify(err);
          set((s) => {
            const jobs = s.jobs.map((j) =>
              j.id === jobId
                ? { ...j, status: 'failed' as const, statusMsg: '', error: errMsg || 'Generation failed' }
                : j,
            );
            persist(jobs);
            return { jobs };
          });
        }
      } catch (err: any) {
        if (err.message === 'Aborted') return;
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
        set((s) => {
          const jobs = s.jobs.map((j) =>
            j.id === jobId || j.id === tempId
              ? { ...j, status: 'failed' as const, statusMsg: '', error: err.message || 'Network error' }
              : j,
          );
          persist(jobs);
          return { jobs };
        });
      } finally {
        abortControllers.delete(jobId);
        abortControllers.delete(tempId);
        // Deactivate keep-awake if no more generating jobs
        if (!hasGenerating(get().jobs)) {
          deactivateKeepAwake(KEEP_AWAKE_TAG);
        }
      }
    })();

    return tempId;
  },

  removeJob: (id) => {
    const ac = abortControllers.get(id);
    if (ac) {
      ac.abort();
      abortControllers.delete(id);
    }
    set((s) => {
      const jobs = s.jobs.filter((j) => j.id !== id);
      persist(jobs);
      const selectedJobId = s.selectedJobId === id ? null : s.selectedJobId;
      if (!hasGenerating(jobs)) deactivateKeepAwake(KEEP_AWAKE_TAG);
      return { jobs, selectedJobId };
    });
  },

  selectJob: (id) => set({ selectedJobId: id }),

  hydrate: async () => {
    try {
      const raw = await AsyncStorage.getItem(STORAGE_KEY);
      if (raw) {
        const saved: GalleryJob[] = JSON.parse(raw);
        // Only load completed/failed — generating jobs are lost on restart
        const valid = saved.filter((j) => j.status !== 'generating');
        set({ jobs: valid });
      }
    } catch {
      // Corrupted storage — start fresh
    }
  },
}));
