import { apiGet, HttpError } from './api-client';
import { POLL_INTERVALS, DEFAULT_POLL_INTERVAL, MAX_NETWORK_FAILS } from './constants';
import type { JobStatus } from './types';

export const ERR_JOB_NOT_FOUND = 'JOB_NOT_FOUND';
export const ERR_CONNECTION_LOST = 'CONNECTION_LOST';

export class PollError extends Error {
  code: string;
  constructor(code: string, message: string) {
    super(message);
    this.name = 'PollError';
    this.code = code;
  }
}

export interface PollCallbacks {
  onProgress: (phase: string | null, step: number, total: number, message: string) => void;
  onPartialResult: (partial: Record<string, any>) => void;
}

function getInterval(phase: string | null): number {
  if (!phase) return DEFAULT_POLL_INTERVAL;
  const key = phase.replace(/_\d+$/, '');
  return POLL_INTERVALS[key] ?? DEFAULT_POLL_INTERVAL;
}

function abortableDelay(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise<void>((resolve, reject) => {
    if (signal?.aborted) { reject(new Error('Aborted')); return; }
    const timer = setTimeout(resolve, ms);
    signal?.addEventListener('abort', () => {
      clearTimeout(timer);
      reject(new Error('Aborted'));
    }, { once: true });
  });
}

/**
 * Poll a job until completion or failure.
 * Returns the final result on success, throws on failure.
 * Supports cancellation via AbortSignal.
 */
export async function pollJob(
  jobId: string,
  callbacks: PollCallbacks,
  signal?: AbortSignal,
): Promise<Record<string, any> | null> {
  let networkFailCount = 0;
  let lastPartial: Record<string, any> | null = null;
  let lastPhase: string | null = null;

  while (!signal?.aborted) {
    await abortableDelay(getInterval(lastPhase), signal);

    let jobData: JobStatus;
    try {
      jobData = await apiGet<JobStatus>(`/api/jobs/${jobId}`);
      networkFailCount = 0;
    } catch (err: any) {
      if (signal?.aborted) break;
      if (err instanceof HttpError && err.status === 404) {
        throw new PollError(ERR_JOB_NOT_FOUND, 'Job not found on server (likely evicted or server restarted)');
      }
      networkFailCount++;
      if (networkFailCount >= MAX_NETWORK_FAILS) {
        throw new PollError(
          ERR_CONNECTION_LOST,
          `Lost connection after ${MAX_NETWORK_FAILS} attempts`,
        );
      }
      continue;
    }

    lastPhase = jobData.phase;

    callbacks.onProgress(
      jobData.phase,
      jobData.step ?? 0,
      jobData.total_steps ?? 0,
      jobData.message ?? '',
    );

    if (jobData.partial_result) {
      lastPartial = jobData.partial_result;
      callbacks.onPartialResult(lastPartial);
    }

    if (jobData.status === 'completed') {
      return jobData.result ?? lastPartial;
    }

    if (jobData.status === 'failed') {
      throw new Error(jobData.error ?? jobData.message ?? 'Job failed');
    }
  }

  return lastPartial;
}
