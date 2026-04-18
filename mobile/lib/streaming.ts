import { fetch } from 'expo/fetch';
import { API_BASE } from './constants';
import { getIdToken } from './auth';
import type { PollCallbacks } from './polling';

const MAX_RECONNECTS = 20; // covers ~30+ min of video generation
const RECONNECT_DELAY_MS = 2000;

/**
 * Stream job progress via Server-Sent Events.
 * Auto-reconnects if the connection drops mid-job (proxy/infra timeouts).
 * Returns final result on completion, throws on failure.
 * Falls back to lastPartial if all reconnect attempts are exhausted.
 */
export async function streamJob(
  jobId: string,
  callbacks: PollCallbacks,
  signal?: AbortSignal,
): Promise<Record<string, any> | null> {
  let lastPartial: Record<string, any> | null = null;
  let reconnects = 0;

  while (reconnects <= MAX_RECONNECTS) {
    if (signal?.aborted) throw new Error('Aborted');

    const headers: Record<string, string> = {};
    const token = await getIdToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const res = await fetch(`${API_BASE}/api/jobs/${jobId}/stream`, {
      headers,
      signal,
    });

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

    // Stream ended without terminal event — connection dropped.
    // Reconnect to pick up where we left off.
    reconnects++;
    if (reconnects > MAX_RECONNECTS) break;

    callbacks.onProgress(null, 0, 0, 'Reconnecting...');
    await new Promise<void>((r) => setTimeout(r, RECONNECT_DELAY_MS));
  }

  return lastPartial;
}
