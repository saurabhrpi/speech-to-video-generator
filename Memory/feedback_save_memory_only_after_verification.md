---
name: Save memory only after verification
description: Don't save a memory about a fix, root cause, or new technical understanding until it has been confirmed working. Speculative memories pollute the index and can lead future sessions astray with unverified claims.
type: feedback
---

When tempted to save a memory about a "lesson learned" or "fix discovered" mid-session, **wait until the fix is verified working** before writing the memory. Speculative memories — especially `reference`-type ones that document technical behavior — risk encoding wrong claims as authoritative.

**Why:** Memories carry weight. A memory like "X causes Y" or "use Z instead of W" is read by future sessions as established fact. If it turns out the fix didn't actually solve the problem (or the root cause was different), the memory misleads — and removing it later is harder than not writing it in the first place.

**S52 burn:** I wrote a memory about "NativeWind + Pressable function-form style silently drops styles" before the user had confirmed the fix worked on rebuild. User pushed back: *"You can create this but I would rather you do it once you're sure the fix you have written here (if any) is working."* — and they were right. The memory had to be deleted.

**How to apply:**
- For `reference` memories about technical behavior: write only AFTER observing the behavior + confirming the workaround on a real run.
- For `feedback` memories about user preferences: usually safe to save immediately since the user just stated the preference (it's not a hypothesis being tested).
- For `project` memories about decisions: safe to save once the user confirms the decision.
- When in doubt, draft the memory mentally + verify the claim, THEN write it. The cost of waiting one round-trip is much lower than the cost of cleaning up wrong-memory pollution later.
