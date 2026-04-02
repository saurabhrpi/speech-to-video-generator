---
name: Expo Migration
description: Frontend migrated from React+Vite+Capacitor to Expo (React Native) in mobile/ directory. Web/ kept for desktop access.
type: project
---

Migrated frontend from React+Vite+Capacitor to Expo (React Native) in session 13 (2026-03-31).

**Why:** Friend with successful iOS app ($M revenue) recommended Expo. Capacitor had black screen issues. Rewrite cost is low (~2,200 lines). Native iOS experience matters for App Store distribution and the $10K/month revenue goal.

**How to apply:** The `mobile/` directory is the Expo app. `web/` is kept for desktop browser access. Backend (Python FastAPI) is unchanged. Auth uses manual cookie injection via expo-secure-store since native fetch doesn't reliably handle session cookies. CORS is irrelevant on native iOS.
