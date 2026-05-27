---
name: Incremental change + test (1 before n)
description: When a change affects n items, apply it to ONE first and test; only proceed to the rest if that test passes
type: feedback
---

When implementing a change that will affect **n items** (n templates, files,
records, components, rows…), do NOT batch-apply it to all n at once. First make
the change for exactly **ONE** of those items and **test it**. Only if and when
that test passes do you proceed to apply it to the rest.

**Why:** A flawed change applied to all n at once means n× the rework and
cleanup, and the failure is harder to isolate. Validating on a single item
catches the bug while it's cheap to fix, and the single-item run often surfaces
edge cases the batch would silently spread (S80: testing the first-frame poster
on ONE tile, `viral-dances-bad`, before the 26-template batch confirmed the
mechanism — and the subsequent batch then exposed 2 pre-existing stale/placeholder
thumbnails we could fix in isolation rather than chase across the whole grid).

**How to apply:**
- Build a single-item path into batch tooling so this is trivial — e.g. a
  `--template-id <one>` / `--dry-run` flag alongside the `--all` mode
  (`scripts/generate_template_thumbnails.py` is the pattern).
- Make the one change, run it for ONE, verify end-to-end (visually on device /
  via test), and get explicit confirmation before fanning out.
- If the user says "test for only 1 first," that's this rule — never run the
  full batch until the single case is signed off.

Related: [[feedback_default_dry_run_when_verifying]], [[feedback_elephants_first]].
