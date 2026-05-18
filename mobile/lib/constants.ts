export const API_BASE = 'https://speech-2-video.ai';

export const REVENUECAT_IOS_APP_STORE_KEY = 'appl_vmQCgcGmPddGaeaDkwiAOvJPaWt';
export const REVENUECAT_TEST_STORE_KEY = 'test_zQWpCAsWrKrLmsEhEVhFzZAUIwi';

export const PACK_SKUS = ['pro_pack_50', 'pro_pack_120', 'pro_pack_250'] as const;
export type PackSku = (typeof PACK_SKUS)[number];

export const PACK_CREDITS: Record<PackSku, number> = {
  pro_pack_50: 50,
  // SKU still reads "120" — ASC SKUs are immutable. The pack now grants 150
  // credits (V2.0.0 resize so the mid tier divides more evenly into 23-cr
  // template gens). ASC IAP display name must read "150 credits" before
  // V2.0.0 ships. Keep in sync with PACK_CREDITS in src/speech_to_video/api/credits.py.
  pro_pack_120: 150,
  pro_pack_250: 250,
};

// Badge target — the pack with the lowest per-credit price (best deal).
// V2.0.0 final pricing: $24.99 / 250 = $0.0999/cr beats $15.99 / 150 = $0.1066/cr
// and $5.99 / 50 = $0.1198/cr. Top pack reclaims the badge.
export const BEST_VALUE_PACK: PackSku = 'pro_pack_250';

// Default-selected radio when the paywall opens. We deliberately do NOT default
// to the badge-bearing pack — defaulting users to the most expensive option
// reads as pushy. Middle pack is the comfortable starting point.
export const DEFAULT_SELECTED_PACK: PackSku = 'pro_pack_120';

export type CostTable = Record<string, Record<string, number>>;

// Mirrors CREDIT_COSTS in src/speech_to_video/api/server.py. Used only when the
// server's cost_table hasn't landed yet (cold start / offline). Keep in sync.
// V1 ships single model + single duration (Session 52).
const FALLBACK_COSTS: CostTable = {
  hailuo: { '10': 10 },
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
