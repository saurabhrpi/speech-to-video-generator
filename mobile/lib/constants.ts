export const API_BASE = 'https://speech-2-video.ai';

export const REVENUECAT_IOS_APP_STORE_KEY = 'appl_vmQCgcGmPddGaeaDkwiAOvJPaWt';
export const REVENUECAT_TEST_STORE_KEY = 'test_zQWpCAsWrKrLmsEhEVhFzZAUIwi';

export const PACK_SKUS = ['pro_pack_50', 'pro_pack_120', 'pro_pack_250'] as const;
export type PackSku = (typeof PACK_SKUS)[number];

export const PACK_CREDITS: Record<PackSku, number> = {
  pro_pack_50: 50,
  pro_pack_120: 120,
  pro_pack_250: 250,
};

export const BEST_VALUE_PACK: PackSku = 'pro_pack_120';

export type CostTable = Record<string, Record<string, number>>;

// Mirrors CREDIT_COSTS in src/speech_to_video/api/server.py. Used only when the
// server's cost_table hasn't landed yet (cold start / offline). Keep in sync.
const FALLBACK_COSTS: CostTable = {
  hailuo: { '6': 5, '10': 9 },
  kling: { '3': 5, '10': 15, '15': 23 },
};

export function creditCostFor(
  modelKey: string,
  duration: number,
  costTable?: CostTable | null,
): number | null {
  const table = costTable ?? FALLBACK_COSTS;
  const cost = table[modelKey]?.[String(duration)];
  return typeof cost === 'number' ? cost : null;
}

export const TERMS_URL = 'https://speech-2-video.ai/terms';
export const PRIVACY_URL = 'https://speech-2-video.ai/privacy';

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
