---
name: default-dry-run-when-verifying
description: When verifying a behavior change in a CLI that has both real and dry-run modes, default to --dry-run. Real mode means real money or real side effects.
metadata:
  type: feedback
---

When a CLI tool ships with both a real mode and a `--dry-run` mode (e.g. the variance harness, or any script that calls a paid provider), and you're testing a behavior change to the script itself, **default to `--dry-run`** unless the change you're testing is specifically about the real-spend path.

**Why:** S63 — I edited the cost-guard threshold in the variance harness and re-ran without `--dry-run` to verify the threshold change. Tool happily proceeded to call Kling 3 times against a template with placeholder URLs. Likely no charge (Kling typically no-charges on bad-input failures), but the behavior I was actually verifying (threshold gate) is fully exercised by dry-run; I had no reason to hit the real path.

**How to apply:**
- If the change you made is to flag parsing, cost guard, output formatting, manifest shape, HTML render, dir layout, validation, error handling, or anything that fires BEFORE provider calls → dry-run is sufficient. Use it.
- If the change is specifically to the provider call path, real I/O, or behavior that only manifests under real conditions → real mode is necessary, but plan the run: pick the minimum cells, eyeball the cost estimate, then `--confirm`.
- "I want to be thorough and test both" is not a reason to spend money. The real run can wait for an actual scheduled QA pass.

Related: [[feedback_verify_state_before_recommending_values]] (verify, don't assume) — same family of "pause before the expensive step."
