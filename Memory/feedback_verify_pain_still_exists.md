---
name: verify-pain-still-exists-before-preventative-fix
description: Before recommending preventative code for a past-session pain, verify the underlying conditions still hold — "S63 hurt three times" is not a reason to fix it in S64 if the cause is already resolved
metadata:
  type: feedback
---

When a prior-session pain pattern surfaces as a "fix idea" in the current session, **verify the underlying conditions still hold before recommending preventative work**. If the pain was "X was missing/broken", check whether X is still missing/broken right now.

**Why:** S64 recommended extending `/api/setup` to flag missing env vars because S63 ate three redeploys over R2 / Kling / MiniMax. But by S64 those vars were all set — AIV-80 Stage 2 had just verified prod was healthy at the 8-minute mark. The S63 pain was a one-time cost of LEARNING the Replit Workspace-vs-Deployment Secret split (already memorialized in `[[reference_replit_workspace_vs_deployment_secrets]]`). It wasn't a recurring issue. Building preventative code for a resolved problem is gold-plating — same anti-pattern called out in `[[feedback_elephants_first]]`.

**How to apply:**
- When a past pain appears in `NOW.md` "Open questions" or in memory as something to "address", re-check the current state FIRST. If the cause is gone, close the item with "no longer applicable" instead of building defenses.
- The right preventative trigger is *recurring* pain (same class of bug hit 3+ times across separate sessions). One-time learning costs don't qualify.
- Watch for self-inconsistency: applying `lock-then-track` correctly to one item (e.g. AIV-81 deferred until AIV-59 ships) and then immediately violating it on the next item is a tell that I'm pattern-matching on "past pain → fix" without verifying current state.
- Cross-references: `[[feedback_lock_then_track]]`, `[[feedback_elephants_first]]`.
