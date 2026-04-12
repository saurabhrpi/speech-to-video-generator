---
name: Frontend means mobile app
description: When user says "frontend", always means the Expo/React Native mobile app (mobile/), not the web app (web/)
type: feedback
---

"Frontend" = the mobile app (`mobile/`), not the web app (`web/`).

**Why:** User is focused on the mobile app as the primary frontend. Web frontend changes were made by mistake when the intent was mobile.

**How to apply:** Unless the user explicitly says "web frontend" or "web app", all UI/frontend work should target `mobile/`. If a change seems like it should go in both, ask first — don't assume web.
