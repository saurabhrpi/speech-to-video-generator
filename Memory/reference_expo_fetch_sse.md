---
name: React Native SSE requires expo/fetch
description: Built-in fetch in React Native does not expose response.body as a stream; must use expo/fetch for SSE
type: reference
---

React Native's built-in `fetch` does NOT support `response.body.getReader()` — `response.body` is undefined. Any attempt to consume an SSE stream with the global `fetch` will silently fail (or throw "Streaming not supported" if you check for `body`).

**Fix:** `import { fetch } from 'expo/fetch'` (available in Expo SDK 52+). The Expo fetch implementation exposes a real `ReadableStream` body that supports `getReader()`.

**Why:** Burned an entire pipeline run ($7) discovering this. The frontend connected to the SSE endpoint but immediately failed silently because the global fetch returned a body-less response. Backend logs showed the polling endpoint being hit (fallback) instead of `/stream` requests.

**How to apply:** Whenever doing any kind of streaming response in React Native (SSE, chunked transfer, etc.), import fetch from `expo/fetch` explicitly. Do NOT trust the global. Used in `mobile/lib/streaming.ts` for the job progress SSE connection.
