import * as SecureStore from 'expo-secure-store';
import { API_BASE, SESSION_COOKIE_KEY } from './constants';

async function getHeaders(extra?: Record<string, string>): Promise<Record<string, string>> {
  const headers: Record<string, string> = { ...extra };
  const cookie = await SecureStore.getItemAsync(SESSION_COOKIE_KEY);
  if (cookie) {
    headers['Cookie'] = cookie;
  }
  return headers;
}

function extractAndStoreCookie(response: Response): void {
  const setCookie = response.headers.get('set-cookie');
  if (setCookie) {
    // Store the raw set-cookie value for future requests.
    // On native, we just need the cookie key=value pair.
    const cookieValue = setCookie.split(';')[0];
    if (cookieValue) {
      SecureStore.setItemAsync(SESSION_COOKIE_KEY, cookieValue);
    }
  }
}

export async function apiGet<T = any>(path: string): Promise<T> {
  const headers = await getHeaders();
  const res = await fetch(`${API_BASE}${path}`, { headers });
  extractAndStoreCookie(res);
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`GET ${path} failed (${res.status}): ${text}`);
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
  extractAndStoreCookie(res);
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`POST ${path} failed (${res.status}): ${text}`);
  }
  return res.json();
}

export async function apiDelete<T = any>(path: string): Promise<T> {
  const headers = await getHeaders();
  const res = await fetch(`${API_BASE}${path}`, { method: 'DELETE', headers });
  extractAndStoreCookie(res);
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`DELETE ${path} failed (${res.status}): ${text}`);
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
