import { API_BASE } from './constants';
import { getIdToken } from './auth';

export class HttpError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.name = 'HttpError';
    this.status = status;
  }
}

async function getHeaders(extra?: Record<string, string>): Promise<Record<string, string>> {
  const headers: Record<string, string> = { ...extra };
  const token = await getIdToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

export async function apiGet<T = any>(path: string): Promise<T> {
  const headers = await getHeaders();
  const res = await fetch(`${API_BASE}${path}`, { headers });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new HttpError(res.status, `GET ${path} failed (${res.status}): ${text}`);
  }
  return res.json();
}

export async function apiPost<T = any>(
  path: string,
  body?: Record<string, any> | FormData,
  isFormData = false,
): Promise<T> {
  const contentHeaders: Record<string, string> = {};
  if (!isFormData) {
    contentHeaders['Content-Type'] = 'application/json';
  }
  const headers = await getHeaders(contentHeaders);

  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers,
    body: isFormData ? (body as FormData) : JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new HttpError(res.status, `POST ${path} failed (${res.status}): ${text}`);
  }
  return res.json();
}

export async function apiDelete<T = any>(path: string): Promise<T> {
  const headers = await getHeaders();
  const res = await fetch(`${API_BASE}${path}`, { method: 'DELETE', headers });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new HttpError(res.status, `DELETE ${path} failed (${res.status}): ${text}`);
  }
  return res.json();
}

/** Resolve relative video URLs to absolute URLs with cache-buster */
export function resolveVideoUrl(raw: string): string {
  if (raw.startsWith('http://') || raw.startsWith('https://')) {
    return raw;
  }
  const sep = raw.includes('?') ? '&' : '?';
  return `${API_BASE}${raw}${sep}t=${Date.now()}`;
}
