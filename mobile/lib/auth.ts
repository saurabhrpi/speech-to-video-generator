import * as WebBrowser from 'expo-web-browser';
import * as SecureStore from 'expo-secure-store';
import { API_BASE, SESSION_COOKIE_KEY } from './constants';
import { apiGet, apiPost } from './api-client';
import type { AuthState } from './types';

/**
 * Open the Google OAuth login flow in the system browser.
 * The backend redirects back to our app scheme after auth completes.
 */
export async function login(): Promise<AuthState | null> {
  const redirectUrl = 'interiortimelapse://auth-callback';
  const loginUrl = `${API_BASE}/api/auth/login?next=${encodeURIComponent(redirectUrl)}`;

  const result = await WebBrowser.openAuthSessionAsync(loginUrl, redirectUrl);

  if (result.type === 'success') {
    // After OAuth completes and we're redirected back, fetch the session
    // to verify auth and get the cookie.
    return fetchSession();
  }

  return null;
}

/**
 * Log out: call the backend then clear stored cookie.
 */
export async function logout(): Promise<void> {
  try {
    await apiPost('/api/auth/logout');
  } catch {
    // Best-effort — clear local state even if the request fails
  }
  await SecureStore.deleteItemAsync(SESSION_COOKIE_KEY);
}

/**
 * Check current session state with the backend.
 */
export async function fetchSession(): Promise<AuthState | null> {
  try {
    const j = await apiGet<Record<string, any>>('/api/auth/session');
    return {
      authenticated: !!j?.authenticated,
      user: j?.user,
      usage_count: Number(j?.usage_count || 0),
      limit: Number(j?.limit || 0),
    };
  } catch {
    return null;
  }
}
