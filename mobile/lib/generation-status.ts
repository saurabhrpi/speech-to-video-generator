/**
 * UX state machine for an in-flight generation job. Drives both the gallery
 * thumbnail card and the global floating status pill.
 *
 * Timeline (client-side display ONLY — purely cosmetic, no side effects):
 *   0:00 — 5:00   "counting"      "Ready in X min(s)" + "Creating your video…"
 *   5:00 — 7:00   "almost_ready"  "Almost ready"      + "Creating your video…"
 *   7:00+         "extended"      "Almost ready"      + "Hang tight, almost there…"
 *
 * The phase is a pure function of `createdAt`. It NEVER declares success or
 * failure: the gallery store's polling owns the terminal state — a backend
 * success flips the job to "completed", a backend failure removes it + alerts.
 *
 * S85: the client-side auto-retry was removed. Kling Motion Control jobs can't
 * be cancelled, so resubmitting a "stuck" job didn't replace it — it spawned a
 * duplicate and doubled the cost for zero speed gain. The friendly countdown
 * stays; the resubmit (and the "Retrying…" / client-declared "failed" states)
 * are gone. See Memory/project_reliability_target_and_telemetry.md.
 */

export type GenerationPhase = 'counting' | 'almost_ready' | 'extended';

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

const SUBTITLE_CREATING = 'Creating your video…';

function pluralMin(n: number): string {
  return n === 1 ? 'min' : 'mins';
}

export function computePhase(
  job: { createdAt: number },
  now: number = Date.now(),
): PhaseResult {
  const elapsedMin = (now - job.createdAt) / 60_000;

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

  // Past the expected window but the backend is still working. Stay reassuring
  // and never claim failure — the poll will resolve it (success or backend-
  // declared failure) on its own.
  return {
    phase: 'extended',
    label: 'Almost ready',
    subtitle: 'Hang tight, almost there…',
  };
}
