---
name: Verify actual state before recommending a specific concrete value
description: Before recommending a specific value (version number, URL, build config, ASC field input), verify the current actual state — file contents, deployed config, ASC page header, etc. Don't recommend from general/cached knowledge when verification takes one bash/read.
type: feedback
---

When recommending a CONCRETE value to set (version=1.0.2, URL=https://X, buildNumber=N, etc.), verify the surrounding state first. General/cached knowledge is dangerous because the user's actual configuration may not match what I remember or assume.

**S52 cluster of misses, all the same pattern:**
1. Recommended `mailto:support@speech-2-video.ai` for ASC's Support URL field. ASC rejected — the field requires `http(s)://`. Should have known the field's specific validation, OR proactively flagged the risk and verified before suggesting.
2. Walked the user into capturing App Store screenshots while Red #4 (UI polish) was still pending. Screenshots locked into a submission cycle = wasted work after polish. Should have checked LAUNCH_CHECKLIST + scanned for UI-dependent sub-steps before walking into the step.
3. Said "bump version to 1.0.2" without checking that the existing ASC version page was titled "Version 1.0" — the build/upload would have been rejected as a version mismatch.

User feedback: *"Stop making such silly mistakes."*

**Why this happens:** Confidence + general knowledge feels efficient. But a one-step verification (read app.json, curl the URL field's validator, scan LAUNCH_CHECKLIST.md, check the screenshot for the ASC page's existing version header) takes <30 seconds and prevents an entire round-trip of bad recommendation → user catches → correction.

**How to apply:**
- Before suggesting a CONCRETE value (number, URL, file path, identifier), do a one-step verification of the surrounding state. Examples:
  - Recommending a version bump? Read `app.json` AND check what version ASC is on first.
  - Recommending a URL? Confirm the field accepts the scheme (mailto, http, https, custom) — if uncertain, ask user to confirm or verify by other means.
  - Recommending a sub-step order? Scan the active checklist for blocking dependencies first.
- When in doubt, ASK rather than assume. *"What does ASC's page header say for version?"* is cheaper than a wrong recommendation.
- The Defensible Responses standard from CLAUDE.md applies: every suggestion must withstand 3 follow-up questions. If a follow-up question would reveal "you didn't check X," go check X first.
