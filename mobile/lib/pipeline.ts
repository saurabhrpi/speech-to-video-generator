import { NUM_STAGES, PHASE_ORDER } from './constants';

/**
 * Calculate progress percentage (0-99.5) based on current phase and step.
 * Ported directly from App.tsx calcProgress().
 */
export function calcProgress(
  phase: string | null,
  step: number,
  total: number,
  stopAfter: string | null,
): number {
  if (!phase || total <= 0) return 0;
  const phaseRatio = step / total;

  if (stopAfter) return Math.min(phaseRatio * 100, 99.5);

  const stageMatch = phase.match(/^stage_(\d+)$/);
  if (stageMatch) {
    const stageNum = parseInt(stageMatch[1], 10);
    const stageStart = 3 + ((stageNum - 1) / NUM_STAGES) * 47;
    const stageEnd = 3 + (stageNum / NUM_STAGES) * 47;
    return Math.min(stageStart + (stageEnd - stageStart) * phaseRatio, 99.5);
  }

  const videoMatch = phase.match(/^video_(\d+)$/);
  if (videoMatch) {
    const videoNum = parseInt(videoMatch[1], 10);
    const totalVids = NUM_STAGES - 1;
    const videoStart = 50 + ((videoNum - 1) / totalVids) * 45;
    const videoEnd = 50 + (videoNum / totalVids) * 45;
    return Math.min(videoStart + (videoEnd - videoStart) * phaseRatio, 99.5);
  }

  const ranges: Record<string, [number, number]> = {
    plan: [0, 3],
    stitch: [95, 100],
  };
  const range = ranges[phase];
  if (!range) return 0;
  const [start, end] = range;
  return Math.min(start + (end - start) * phaseRatio, 99.5);
}

/**
 * Get the next phase in the pipeline sequence.
 */
export function nextStopAfter(currentPhase: string | null): string | null {
  if (!currentPhase) return 'plan';
  const idx = (PHASE_ORDER as readonly string[]).indexOf(currentPhase);
  if (idx < 0 || idx >= PHASE_ORDER.length - 1) return null;
  return PHASE_ORDER[idx + 1];
}

/**
 * Infer the last completed phase from pipeline state.
 * Prefers explicit phase_completed from backend (handles early exit when
 * all elements are renovated before NUM_STAGES images are generated).
 */
export function detectLastCompletedPhase(state: Record<string, any>): string | null {
  if (state.phase_completed) return state.phase_completed;
  const nVideos = state.transition_videos?.length ?? 0;
  if (nVideos > 0) return `video_${nVideos}`;
  const nImages = state.keyframe_images?.length ?? 0;
  if (nImages > 0) return `stage_${nImages}`;
  if (state.scene_bible) return 'plan';
  return null;
}

/**
 * Extract the relevant partial state fields for resume.
 */
export function extractPartial(data: Record<string, any>): Record<string, any> | null {
  if (!data.scene_bible && !data.keyframe_images && !data.transition_videos) return null;
  const p: Record<string, any> = {};
  if (data.scene_bible) p.scene_bible = data.scene_bible;
  if (data.elements) p.elements = data.elements;
  if (data.renovated_elements) p.renovated_elements = data.renovated_elements;
  if (data.stages) p.stages = data.stages;
  if (data.seed) p.seed = data.seed;
  if (data.keyframe_images) p.keyframe_images = data.keyframe_images;
  if (data.transition_videos) p.transition_videos = data.transition_videos;
  if (data.phase_completed) p.phase_completed = data.phase_completed;
  if (data.all_images_done) p.all_images_done = data.all_images_done;
  return p;
}
