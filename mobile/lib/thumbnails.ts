import * as VideoThumbnails from 'expo-video-thumbnails';

const THUMB_TIME_MS = 2000;
const THUMB_QUALITY = 0.7;

/**
 * Extract a still frame at THUMB_TIME_MS into the clip and return its local
 * cache URI. Returns null on any failure (network, expired URL, decode error)
 * — callers fall back to the play-icon placeholder in that case.
 */
export async function generateThumbnail(videoUrl: string): Promise<string | null> {
  try {
    const { uri } = await VideoThumbnails.getThumbnailAsync(videoUrl, {
      time: THUMB_TIME_MS,
      quality: THUMB_QUALITY,
    });
    return uri;
  } catch (err) {
    console.warn('[thumbnails] generation failed:', err);
    return null;
  }
}
