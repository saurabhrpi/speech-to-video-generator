import { create } from 'zustand';
import * as Haptics from 'expo-haptics';
import { Alert } from 'react-native';
import { activateKeepAwake, deactivateKeepAwake } from 'expo-keep-awake';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { apiPost, resolveVideoUrl } from '@/lib/api-client';
import { streamJob } from '@/lib/streaming';
import { useAuthStore } from '@/store/auth-store';

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
  saved: boolean;
}

/** Module-level AbortControllers — not serialized */
const abortControllers = new Map<string, AbortController>();

interface GalleryStore {
  jobs: GalleryJob[];
  selectedJobId: string | null;

  startGeneration: (formData: FormData, meta: { prompt: string; model: string; duration: number }) => string;
  markSaved: (id: string) => void;
  removeJob: (id: string) => void;
  selectJob: (id: string | null) => void;
  hydrate: () => Promise<void>;
}

function hasGenerating(jobs: GalleryJob[]): boolean {
  return jobs.some((j) => j.status === 'generating');
}

function persist(jobs: GalleryJob[]) {
  // Persist completed + generating (with real job_id, not temp). Skip failed.
  const toSave = jobs.filter((j) =>
    j.status === 'completed' || (j.status === 'generating' && !j.id.startsWith('temp_'))
  );
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
      saved: false,
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

        // Update the job ID from temp to real, and persist so it survives app close
        abortControllers.set(jobId, ac);
        abortControllers.delete(tempId);
        set((s) => {
          const jobs = s.jobs.map((j) => (j.id === tempId ? { ...j, id: jobId } : j));
          persist(jobs);
          return {
            jobs,
            selectedJobId: s.selectedJobId === tempId ? jobId : s.selectedJobId,
          };
        });

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
            const jobs = s.jobs.filter((j) => j.id !== jobId);
            persist(jobs);
            return { jobs, selectedJobId: s.selectedJobId === jobId ? null : s.selectedJobId };
          });
          Alert.alert('Generation failed', errMsg || 'Unknown error');
        }
      } catch (err: any) {
        if (err.message === 'Aborted') return;
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
        set((s) => {
          const jobs = s.jobs.filter((j) => j.id !== jobId && j.id !== tempId);
          persist(jobs);
          return { jobs, selectedJobId: (s.selectedJobId === jobId || s.selectedJobId === tempId) ? null : s.selectedJobId };
        });
        Alert.alert('Generation failed', err.message || 'Network error');
      } finally {
        abortControllers.delete(jobId);
        abortControllers.delete(tempId);
        // Refresh auth so canGenerate() reflects updated usage count
        useAuthStore.getState().fetchSession();
        // Deactivate keep-awake if no more generating jobs
        if (!hasGenerating(get().jobs)) {
          deactivateKeepAwake(KEEP_AWAKE_TAG);
        }
      }
    })();

    return tempId;
  },

  markSaved: (id) => {
    set((s) => {
      const jobs = s.jobs.map((j) => (j.id === id ? { ...j, saved: true } : j));
      persist(jobs);
      return { jobs };
    });
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
      if (!raw) return;
      const saved: GalleryJob[] = JSON.parse(raw);
      const valid = saved.filter((j) => j.status === 'completed' || j.status === 'generating');
      set({ jobs: valid });

      // Reconnect any generating jobs
      const generating = valid.filter((j) => j.status === 'generating');
      for (const job of generating) {
        const ac = new AbortController();
        abortControllers.set(job.id, ac);
        activateKeepAwake(KEEP_AWAKE_TAG);

        (async () => {
          const jobId = job.id;
          try {
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
              set((s) => {
                const jobs = s.jobs.filter((j) => j.id !== jobId);
                persist(jobs);
                return { jobs, selectedJobId: s.selectedJobId === jobId ? null : s.selectedJobId };
              });
              Alert.alert('Generation lost', `"${job.prompt}" could not be recovered — the server may have restarted.`);
            }
          } catch {
            set((s) => {
              const jobs = s.jobs.filter((j) => j.id !== jobId);
              persist(jobs);
              return { jobs, selectedJobId: s.selectedJobId === jobId ? null : s.selectedJobId };
            });
            Alert.alert('Generation lost', `"${job.prompt}" could not be recovered — the server may have restarted.`);
          } finally {
            abortControllers.delete(jobId);
            if (!hasGenerating(get().jobs)) deactivateKeepAwake(KEEP_AWAKE_TAG);
          }
        })();
      }
    } catch {
      // Corrupted storage — start fresh
    }
  },
}));
