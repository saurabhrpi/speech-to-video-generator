export const API_BASE = 'https://speech-2-video.ai';

export const NUM_STAGES = 7;

export const STAGE_PHASES = Array.from({ length: NUM_STAGES }, (_, i) => `stage_${i + 1}`);
export const VIDEO_PHASES = Array.from({ length: NUM_STAGES - 1 }, (_, i) => `video_${i + 1}`);
export const PHASE_ORDER = ['plan', ...STAGE_PHASES, ...VIDEO_PHASES] as const;

export const PHASE_LABELS: Record<string, string> = {
  plan: 'Scene Bible + Stage 1 Plan',
  ...Object.fromEntries(STAGE_PHASES.map((p, i) => [p, `Stage ${i + 1} Image`])),
  ...Object.fromEntries(VIDEO_PHASES.map((p, i) => [p, `Transition Video ${i + 1}\u2192${i + 2}`])),
  stitch: 'Stitching',
  done: 'Stitching',
};

export const POLL_INTERVALS: Record<string, number> = {
  plan: 2000,
  stage: 3000,
  video: 5000,
  stitch: 30000,
};

export const DEFAULT_POLL_INTERVAL = 3000;
export const MAX_NETWORK_FAILS = 10;
