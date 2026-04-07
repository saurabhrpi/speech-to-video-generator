import { apiGet, apiPost, apiDelete } from './api-client';
import type { Clip } from './types';

export async function fetchClips(): Promise<Clip[]> {
  return apiGet<Clip[]>('/api/clips');
}

export async function saveClip(url: string, note?: string, jsonResponse?: string): Promise<void> {
  const formData = new FormData();
  formData.append('url', url);
  if (note) formData.append('note', note);
  if (jsonResponse) formData.append('json_response', jsonResponse);
  await apiPost('/api/clips', formData as any, true);
}

export async function deleteClip(ts: number): Promise<void> {
  await apiDelete(`/api/clips/${ts}`);
}

export async function clearClips(): Promise<void> {
  await apiDelete('/api/clips');
}

export async function reorderClips(order: number[]): Promise<void> {
  const formData = new FormData();
  formData.append('order', order.join(','));
  await apiPost('/api/clips/reorder', formData as any, true);
}

export async function stitchSavedClips(): Promise<{ success: boolean; stitched_url?: string }> {
  const formData = new FormData();
  formData.append('use_saved', 'true');
  return apiPost('/api/stitch', formData as any, true);
}

export async function getClipResponse(ts: number): Promise<any> {
  return apiGet(`/api/clips/${ts}/response`);
}
