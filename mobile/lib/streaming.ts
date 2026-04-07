import { fetch } from 'expo/fetch';
import * as SecureStore from 'expo-secure-store';
import { API_BASE, SESSION_COOKIE_KEY } from './constants';
import type { PollCallbacks } from './polling';

/**
 * Stream job progress via Server-Sent Events.
 * Returns final result on completion, throws on failure.
 * Falls back to null if the stream ends without a terminal event.
 */
export async function streamJob(
  jobId: string,
  callbacks: PollCallbacks,
  signal?: AbortSignal,
): Promise<Record<string, any> | null> {
  let lastPartial: Record<string, any> | null = null;

  const headers: Record<string, string> = {};
  const cookie = await SecureStore.getItemAsync(SESSION_COOKIE_KEY);
  if (cookie) headers['Cookie'] = cookie;

  const res = await fetch(`${API_BASE}/api/jobs/${jobId}/stream`, {
    headers,
    signal,
  });

  // Extract cookie once from the SSE connection response
  const setCookie = res.headers.get('set-cookie');
  if (setCookie) {
    const v = setCookie.split(';')[0];
    if (v) SecureStore.setItemAsync(SESSION_COOKIE_KEY, v);
  }

  if (!res.ok) {
    throw new Error(`SSE connect failed (${res.status})`);
  }

  const reader = res.body?.getReader();
  if (!reader) throw new Error('Streaming not supported');

  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // SSE events are separated by double newlines
      const parts = buffer.split('\n\n');
      buffer = parts.pop() || '';

      for (const part of parts) {
        for (const line of part.split('\n')) {
          if (!line.startsWith('data: ')) continue;

          const data = JSON.parse(line.slice(6));

          callbacks.onProgress(
            data.phase ?? null,
            data.step ?? 0,
            data.total_steps ?? 0,
            data.message ?? '',
          );

          if (data.partial_result) {
            lastPartial = data.partial_result;
            callbacks.onPartialResult(data.partial_result);
          }

          if (data.status === 'completed') {
            return data.result ?? lastPartial;
          }

          if (data.status === 'failed') {
            throw new Error(data.error ?? data.message ?? 'Job failed');
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }

  return lastPartial;
}
