---
name: Explicit handoff instructions
description: When asking the user to take an action between turns (curl an endpoint, click something, run a command), spell out the exact invocation — don't assume they'll infer the mechanism
type: feedback
---

When I ask the user to take an action between conversation turns, I must spell out the exact mechanism: the full command to run, the exact click path, the precise env var to set. Don't assume they'll infer *how* to do the thing from a high-level description.

**Why:** I wrote a diagnostic endpoint `/api/debug/time-image-edit` and told the user "push + hit the endpoint on the deployed URL." They interpreted "hit the endpoint" as "deploy and rerun the app in the normal way" — they thought running the app would produce diagnostic output. It didn't, because the endpoint was a standalone GET that required an explicit `curl`. I had never said "open a terminal and run `curl <url>`" plainly. The user wasted a full deploy + pipeline-run cycle (~25 min + credits) before discovering the gap, then asked "why wasn't I told about this?" — fair, because the handoff sentence was too abstract. The actual fix was to wire the diagnostic to auto-run on startup so no manual step was needed at all.

**How to apply:** At any handoff moment where the user needs to do something between turns, include one of: (a) the literal shell command, (b) the exact click path (e.g., "Replit → Tools → Secrets → trash icon"), (c) the env var name and value. If the mechanism isn't obvious from the ambient context, name it. Also ask yourself: does this *need* to be a manual step at all? If you can automate it with a one-line startup hook or a config flag, prefer automation over instructions.
