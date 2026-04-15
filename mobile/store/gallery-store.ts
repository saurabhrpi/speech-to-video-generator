import { create } from 'zustand';
import * as Haptics from 'expo-haptics';
import { Alert } from 'react-native';
import { activateKeepAwake, deactivateKeepAwake } from 'expo-keep-awake';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { apiPost, resolveVideoUrl } from '@/lib/api-client';
import { pollJob, ERR_CONNECTION_LOST, ERR_JOB_NOT_FOUND } from '@/lib/polling';
import { useAuthStore } from '@/store/auth-store';

const STORAGE_KEY = 'gallery_jobs';
const BACKUP_KEY = 'gallery_jobs_backup';
const KEEP_AWAKE_TAG = 'gallery';

export interface GalleryJob {
  id: string;
  prompt: string;
  model: string;
  duration: number;
  status: 'generating' | 'completed' | 'failed' | 'paused';
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
  resumePausedJobs: () => void;
}

function hasGenerating(jobs: GalleryJob[]): boolean {
  return jobs.some((j) => j.status === 'generating');
}

function isRecoverable(status: GalleryJob['status']): boolean {
  return status === 'generating' || status === 'paused';
}

function persist(jobs: GalleryJob[]) {
  // Persist completed + in-flight jobs (generating or paused, both need recovery).
  // Skip failed and temp-id'd jobs (pre-POST, no server counterpart).
  const toSave = jobs.filter((j) =>
    j.status === 'completed' || (isRecoverable(j.status) && !j.id.startsWith('temp_'))
  );
  const json = JSON.stringify(toSave);
  // Rotate: copy current primary → backup, then overwrite both atomically.
  // multiSet is a single SQLite transaction — either both writes commit or neither does.
  // If app crashes mid-transaction, both keys retain their previous values.
  AsyncStorage.getItem(STORAGE_KEY)
    .then((prev) => {
      const writes: [string, string][] = [[STORAGE_KEY, json]];
      if (prev) writes.push([BACKUP_KEY, prev]);
      return AsyncStorage.multiSet(writes);
    })
    .catch((err) => console.error('[Gallery] persist failed:', err));
}

/**
 * Run polling for a job. Shared between startGeneration, hydrate, and resume.
 * Transitions job state on terminal conditions:
 *   - success   → status='completed', videoUrl set
 *   - backend-reported failure (result.success=false) → remove + alert
 *   - CONNECTION_LOST → status='paused' (will resume on foreground)
 *   - JOB_NOT_FOUND → remove + alert "server restarted"
 *   - abort → silent (caller already cleaned state)
 */
function runPoll(
  jobId: string,
  prompt: string,
  ac: AbortController,
  opts: { tempId?: string; refreshAuth?: boolean } = {},
) {
  activateKeepAwake(KEEP_AWAKE_TAG);
  (async () => {
    try {
      const result = await pollJob(
        jobId,
        {
          onProgress: (_phase, _step, _total, message) => {
            useGalleryStore.setState((s) => ({
              jobs: s.jobs.map((j) =>
                j.id === jobId
                  ? { ...j, status: 'generating' as const, statusMsg: message || 'Generating video...' }
                  : j,
              ),
            }));
          },
          onPartialResult: () => {},
        },
        ac.signal,
      );

      if (ac.signal.aborted) return;

      if (result?.video_url) {
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
        useGalleryStore.setState((s) => {
          const jobs = s.jobs.map((j) =>
            j.id === jobId
              ? { ...j, status: 'completed' as const, statusMsg: 'Done!', videoUrl: resolveVideoUrl(result.video_url) }
              : j,
          );
          persist(jobs);
          return { jobs };
        });
      } else {
        // Backend finished the job but returned no video_url (e.g. result.success=false).
        const err = result?.error;
        const errMsg = typeof err === 'string' ? err : (err ? JSON.stringify(err) : 'Unknown error');
        useGalleryStore.setState((s) => {
          const jobs = s.jobs.filter((j) => j.id !== jobId);
          persist(jobs);
          return { jobs, selectedJobId: s.selectedJobId === jobId ? null : s.selectedJobId };
        });
        Alert.alert('Generation failed', errMsg);
      }
    } catch (err: any) {
      if (err?.message === 'Aborted' || ac.signal.aborted) return;

      if (err?.code === ERR_CONNECTION_LOST) {
        // Transient: keep the job, mark paused. AppState listener will resume.
        useGalleryStore.setState((s) => {
          const jobs = s.jobs.map((j) =>
            j.id === jobId
              ? { ...j, status: 'paused' as const, statusMsg: 'Paused — will resume when back online' }
              : j,
          );
          persist(jobs);
          return { jobs };
        });
        return;
      }

      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
      useGalleryStore.setState((s) => {
        const jobs = s.jobs.filter((j) => j.id !== jobId && (opts.tempId ? j.id !== opts.tempId : true));
        persist(jobs);
        return {
          jobs,
          selectedJobId: (s.selectedJobId === jobId || s.selectedJobId === opts.tempId) ? null : s.selectedJobId,
        };
      });
      const isLost = err?.code === ERR_JOB_NOT_FOUND;
      Alert.alert(
        'Generation failed',
        isLost
          ? `"${prompt}" could not be recovered — the server may have restarted.`
          : (err.message || 'Network error'),
      );
    } finally {
      abortControllers.delete(jobId);
      if (opts.tempId) abortControllers.delete(opts.tempId);
      if (opts.refreshAuth) {
        useAuthStore.getState().fetchSession();
      }
      if (!hasGenerating(useGalleryStore.getState().jobs)) {
        deactivateKeepAwake(KEEP_AWAKE_TAG);
      }
    }
  })();
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

    // Fire-and-forget async — submit to API, then poll for progress.
    const ac = new AbortController();
    abortControllers.set(tempId, ac);

    (async () => {
      try {
        const { job_id } = await apiPost<{ job_id: string }>(
          '/api/generate/speech-to-video',
          formData,
          true,
        );

        // Swap temp ID → real ID, persist so it survives app close
        abortControllers.set(job_id, ac);
        abortControllers.delete(tempId);
        set((s) => {
          const jobs = s.jobs.map((j) => (j.id === tempId ? { ...j, id: job_id } : j));
          persist(jobs);
          return {
            jobs,
            selectedJobId: s.selectedJobId === tempId ? job_id : s.selectedJobId,
          };
        });

        runPoll(job_id, meta.prompt, ac, { tempId, refreshAuth: true });
      } catch (err: any) {
        if (err?.message === 'Aborted') return;
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
        set((s) => {
          const jobs = s.jobs.filter((j) => j.id !== tempId);
          persist(jobs);
          return { jobs, selectedJobId: s.selectedJobId === tempId ? null : s.selectedJobId };
        });
        abortControllers.delete(tempId);
        if (!hasGenerating(get().jobs)) {
          deactivateKeepAwake(KEEP_AWAKE_TAG);
        }
        Alert.alert('Generation failed', err.message || 'Network error');
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
    let valid: GalleryJob[] = [];
    let source = 'primary';

    // Try primary key, fall back to backup
    try {
      const raw = await AsyncStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed)) {
          valid = parsed.filter(
            (j: any) => j && (j.status === 'completed' || isRecoverable(j.status)),
          );
        }
      }
    } catch (err) {
      console.error('[Gallery] primary storage corrupted:', err);
    }

    if (valid.length === 0) {
      try {
        const backup = await AsyncStorage.getItem(BACKUP_KEY);
        if (backup) {
          const parsed = JSON.parse(backup);
          if (Array.isArray(parsed)) {
            valid = parsed.filter(
              (j: any) => j && (j.status === 'completed' || isRecoverable(j.status)),
            );
            source = 'backup';
            console.warn('[Gallery] recovered', valid.length, 'jobs from backup');
          }
        }
      } catch (err) {
        console.error('[Gallery] backup also corrupted:', err);
      }
    }

    if (valid.length === 0) return;
    set({ jobs: valid });

    // Successful load — save backup so next crash has a fallback
    try {
      const json = JSON.stringify(valid);
      const writes: [string, string][] = [[BACKUP_KEY, json]];
      if (source === 'backup') writes.push([STORAGE_KEY, json]);
      await AsyncStorage.multiSet(writes);
    } catch (err) {
      console.error('[Gallery] backup write failed:', err);
    }

    // Resume polling for any in-flight (generating or paused) jobs
    for (const job of valid.filter((j) => isRecoverable(j.status))) {
      if (abortControllers.has(job.id)) continue;
      const ac = new AbortController();
      abortControllers.set(job.id, ac);
      runPoll(job.id, job.prompt, ac);
    }
  },

  resumePausedJobs: () => {
    const paused = get().jobs.filter((j) => j.status === 'paused');
    for (const job of paused) {
      if (abortControllers.has(job.id)) continue;
      const ac = new AbortController();
      abortControllers.set(job.id, ac);
      runPoll(job.id, job.prompt, ac);
    }
  },
}));
