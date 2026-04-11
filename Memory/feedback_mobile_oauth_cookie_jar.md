---
name: Mobile OAuth cookie jar mismatch
description: ASWebAuthenticationSession has a separate cookie jar from the app's fetch() — session cookies don't transfer. Use one-time token exchange pattern.
type: feedback
---

On iOS, `WebBrowser.openAuthSessionAsync` (ASWebAuthenticationSession) runs in a separate browser context. Session cookies set by the backend during OAuth do NOT transfer to the app's `fetch()` requests (which use manual cookie management via SecureStore).

**Why:** The browser's cookie jar and the app's network layer are completely isolated. After OAuth completes and the browser redirects back to the app, the app has no access to the session cookie that was just set.

**How to apply:** For any OAuth flow on mobile (Expo/React Native), use a one-time token exchange pattern:
1. Backend generates a short-lived token, stores it mapped to the user data
2. Backend appends the token to the deep link redirect URL (`interiortimelapse://auth-callback?token=abc`)
3. App extracts token from `result.url`, calls a `/api/auth/exchange` endpoint
4. Exchange endpoint validates the token, sets the session, returns `set-cookie` header
5. App's `apiPost` captures the cookie via `extractAndStoreCookie` into SecureStore

Files: `mobile/lib/auth.ts`, `server.py` (`/api/auth/callback`, `/api/auth/exchange`)
