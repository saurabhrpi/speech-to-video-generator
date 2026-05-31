---
name: feedback_verify_tool_output_before_chaining
description: Don't form conclusions from batched tool output before confirming each query's real exit code + output; a crashed run's empty output hides in the flush
metadata:
  type: feedback
---

During the S87 prep-folder cleanup, my first ~6 R2 audit scripts ALL crashed with `AttributeError: module 'r2_client' has no attribute '_bucket'` — I'd guessed a private helper name instead of reading the module. The real API is `r2_client.list_objects(prefix)` (public, paginates internally) and `get_settings().r2_bucket` / `_resolve_bucket(bucket)` — there is no `_bucket()`.

**Why it was dangerous:** I fired many interdependent verification calls in parallel batches. The crashed runs produced empty/garbage output that interleaved with display noise while results buffered, and I started forming load-bearing conclusions from it — "47 templates on R2", "river absent", "KEEP 42 / DELETE 103" — that were never real outputs. For a DESTRUCTIVE task (`rm` 2 GB), I nearly proceeded on fabricated numbers. Caught it only when the batch finally flushed and I saw every result was an `AttributeError`.

**Why:** Pattern-matching a plausible private-API name (`_bucket()`) without reading the module, then chaining many dependent calls so individual failures hid in the aggregate flush. Violated CLAUDE.md's "no hallucination — every diagnosis grounded in evidence from the current run" + the verify-before-destructive rule. Same skepticism as [[feedback_explore_agent_trust]] but applied to my OWN tool output.

**How to apply:**
1. Before calling a private/underscore helper, READ the module's actual signatures — don't guess `_name()`. Prefer the documented public function (here `list_objects`).
2. For verification that gates a destructive/irreversible step, run ONE query, confirm its **real exit code + non-empty output written to a file**, THEN build the next step on it. Don't batch many interdependent verification calls whose failures can vanish in the flush.
3. If a number will justify a delete/overwrite, it must trace to a confirmed-successful run — never to output seen mid-buffer. When unsure whether output is real, re-run the single query and read the file.

Related: [[feedback_default_dry_run_when_verifying]], [[feedback_save_memory_only_after_verification]], [[feedback_analysis_depth]].
