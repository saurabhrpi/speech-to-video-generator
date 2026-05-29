/**
 * UX state machine for an in-flight generation job. Drives both the gallery
 * thumbnail card and the global floating status pill.
 *
 * Timeline (single attempt):
 *   0:00 — 5:00   "counting"        "Ready in X min(s)" + "Creating your video…"
 *   5:00 — 7:00   "almost_ready"    "Almost ready"      + "Creating your video…"
 *   7:00 — 12:00  "awaiting_retry"  "Retrying in X min" + "First attempt timed out"
 *  12:00          retry fires (resets createdAt, retryAttempts++)
 *
 * After one retry attempt is in flight, the same window plays again:
 *   0:00 — 7:00   counting → almost_ready
 *   7:00          "failed" (no further retries)
 *
 * The "phase" is a pure function of `(createdAt, retryAttempts)` — the
 * gallery store's actual polling is independent and continues regardless.
 * If the backend returns success at any point, the job transitions to
 * "completed" through the existing pollJob path and this state machine
 * stops being consulted.
 */

export type GenerationPhase =
  | 'counting'
  | 'almost_ready'
  | 'awaiting_retry'
  | 'failed';

export interface PhaseResult {
  phase: GenerationPhase;
  /** Main one-line label, e.g. "Ready in 4 mins" or "Almost ready". */
  label: string;
  /** Smaller subtitle line, e.g. "Creating your video…". */
  subtitle: string;
  /** Optional integer minute count, useful for the floating pill's compact form. */
  minsRemaining?: number;
}

export const READY_PHASE_MINS = 5;
export const ALMOST_READY_PHASE_MINS = 2;
export const RETRY_WAIT_MINS = 5;
export const MAX_RETRIES = 1;

const SUBTITLE_CREATING = 'Creating your video…';

function pluralMin(n: number): string {
  return n === 1 ? 'min' : 'mins';
}

export function computePhase(
  job: { createdAt: number; retryAttempts?: number },
  now: number = Date.now(),
): PhaseResult {
  const elapsedMin = (now - job.createdAt) / 60_000;
  const retries = job.retryAttempts ?? 0;

  if (elapsedMin < READY_PHASE_MINS) {
    const minsRemaining = Math.max(1, Math.ceil(READY_PHASE_MINS - elapsedMin));
    return {
      phase: 'counting',
      label: `Ready in ${minsRemaining} ${pluralMin(minsRemaining)}`,
      subtitle: SUBTITLE_CREATING,
      minsRemaining,
    };
  }

  if (elapsedMin < READY_PHASE_MINS + ALMOST_READY_PHASE_MINS) {
    return {
      phase: 'almost_ready',
      label: 'Almost ready',
      subtitle: SUBTITLE_CREATING,
    };
  }

  if (retries < MAX_RETRIES) {
    const retryAtMin = READY_PHASE_MINS + ALMOST_READY_PHASE_MINS + RETRY_WAIT_MINS;
    if (elapsedMin < retryAtMin) {
      const minsToRetry = Math.max(1, Math.ceil(retryAtMin - elapsedMin));
      return {
        phase: 'awaiting_retry',
        label: `Retrying in ${minsToRetry} ${pluralMin(minsToRetry)}`,
        subtitle: 'First attempt timed out',
        minsRemaining: minsToRetry,
      };
    }
    // elapsedMin >= retryAtMin: a retry should be fired by the gallery store
    // watcher; if it hasn't happened yet (e.g. between ticks), fall through
    // to a transient "Retrying now…" presentation.
    return {
      phase: 'awaiting_retry',
      label: 'Retrying now…',
      subtitle: 'First attempt timed out',
    };
  }

  return {
    phase: 'failed',
    label: 'Generation failed',
    subtitle: 'Tap to dismiss',
  };
}

/** True when the elapsed time on this attempt has passed the retry threshold
 *  AND we still have retries available — the gallery store should fire one. */
export function shouldFireRetry(
  job: { createdAt: number; retryAttempts?: number },
  now: number = Date.now(),
): boolean {
  const elapsedMin = (now - job.createdAt) / 60_000;
  const retries = job.retryAttempts ?? 0;
  const retryAtMin = READY_PHASE_MINS + ALMOST_READY_PHASE_MINS + RETRY_WAIT_MINS;
  return retries < MAX_RETRIES && elapsedMin >= retryAtMin;
}
