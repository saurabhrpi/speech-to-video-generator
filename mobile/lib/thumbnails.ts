import * as VideoThumbnails from 'expo-video-thumbnails';

const THUMB_TIME_MS = 2000;
const THUMB_QUALITY = 0.7;

export interface ThumbnailResult {
  uri: string | null;
  err?: string;
}

/**
 * Extract a still frame at THUMB_TIME_MS into the clip.
 *
 * S66 diag: return shape changed from `string|null` to `{uri, err?}` so
 * callers can record the failure reason on the job state and render it
 * on the gallery card. Strip the diag once the thumbnail bug is fixed.
 */
export async function generateThumbnail(videoUrl: string): Promise<ThumbnailResult> {
  try {
    const { uri } = await VideoThumbnails.getThumbnailAsync(videoUrl, {
      time: THUMB_TIME_MS,
      quality: THUMB_QUALITY,
    });
    return { uri };
  } catch (err: any) {
    const msg = `${err?.name ?? 'Error'}: ${err?.message ?? String(err)}`;
    console.warn('[thumbnails] generation failed:', msg);
    return { uri: null, err: msg };
  }
}
