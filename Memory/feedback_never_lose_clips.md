---
name: Never lose user clips
description: Cross-cutting rule — no auth, migration, or account flow may orphan user clips, free tier or paid. Factor this into every design that touches user identity.
type: feedback
---

User clips must NEVER be lost — regardless of whether the user is anonymous, signed-in, free-tier, or paid.

**Why:** User stated this explicitly in Session 38 while evaluating Apple Sign In fallback options. It is a hard product constraint, not a nice-to-have. The product's value proposition depends on generated clips being preserved for the user — losing them even once breaks trust, and the cost of a clip to re-generate is real (~$7, ~20 min per Interior Timelapse).

**How to apply:**
- Any auth flow that changes the active Firebase UID (sign-in, link fallback, sign-out + sign-in) MUST preserve the clips from all UIDs involved. Default options are:
  - Link-in-place (same UID survives) — preferred, automatic preservation.
  - Cross-UID merge on the backend — required whenever the active UID changes. Copy clips from the abandoned UID's namespace into the new UID's namespace.
- The Session 38 double-sheet fix in `mobile/lib/auth.ts` is a short-term patch for the standalone-banner path that's being replaced by RevenueCat. It does NOT preserve clips in the collision case. The proper single-sheet + merge architecture must land as part of RevenueCat paywall sign-in (tracked in `LAUNCH_CHECKLIST.md`).
- Any feature that deletes, reassigns, or migrates user data must have "does this lose any clip?" as a top-line review question. If the answer is yes or maybe, flag it and propose a merge path before implementing.
- Clip storage is namespaced per-UID (`{CLIPS_NAMESPACE}/{firebase_uid}/` — see `clip_store.py`), so migration means moving or copying files across namespaces on the server.
