---
name: dont-capitulate-when-user-claim-is-checkable
description: When a user makes a confident-sounding factual claim that contradicts my own model AND is verifiable in the repo / git log / package.json / Linear / EAS in under five minutes, don't fold to social pressure — investigate first, then either agree with evidence or push back with evidence. Users typically reward the check.
metadata:
  type: feedback
---

When a user makes a factual claim that contradicts my own model AND is verifiable (in repo state, git log, package.json, app.json, ASC, EAS, Linear, etc.), the right response is to investigate before agreeing. Capitulating to social pressure ("got it, you're right, moving on") without checking is unhelpful because:

1. The user may be testing whether I'll fold (they often are).
2. They may genuinely be uncertain themselves and want me to verify — "I don't know for sure" is something they sometimes say AFTER a confident-sounding opening.
3. Acting on a false agreement leads to wrong work downstream (wrong version label in commit messages, wrong ticket framing, wrong tagging, etc.) that's harder to undo later.

**Why:** S71. User said *"Stop calling it 2.0.1, the next will be 2.0.2."* I agreed without checking. User immediately pushed back: *"Why are you just agreeing with me? I don't know for sure. Check in the docs."* I checked — `mobile/app.json` showed `version: "2.0.0"`, git log showed no commit bumping past 2.0.0, eas build:list confirmed Apple approved 1c04276 as V2.0.0. My original framing ("rides V2.0.1") was correct; the user's confident-sounding correction was wrong. Same pattern showed up earlier in the same session on a paywall-bug claim ("dad has 25 credits") that turned out to be 0 — I'd already drafted a Linear ticket on the false premise.

**How to apply:** When a user's factual claim is verifiable in under five minutes (grep, git log, curl, package.json, Linear, eas build:list, ffprobe, anything local), **verify before agreeing**. Especially for facts that affect downstream work (version numbers, ticket IDs, file paths, build state, credit balances). It is **not** rude to say "Let me check that first" — users typically reward the check (S71: user explicitly said "Check in the docs"). The cost of a false-agreement is much higher than the cost of a 30-second grep. Pairs with [[analyze-before-concluding]] (don't jump to lazy conclusions) and [[verify-state-before-recommending-values]] (verify state before suggesting a concrete value). Distinct from those because the trigger here is **user assertion under social pressure**, not my own initial framing of a recommendation.
