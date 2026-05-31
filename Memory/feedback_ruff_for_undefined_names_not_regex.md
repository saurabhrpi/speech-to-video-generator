---
name: feedback_ruff_for_undefined_names_not_regex
description: To find missing-import / undefined-name bugs, use ruff F821 (scope-aware), NOT a hand-rolled grep/regex — the regex gives false positives on inline imports
metadata:
  type: feedback
---

**The triggering issue (S87):** a template gen on device died with
`Generation failed: name 'time' is not defined` (~/Downloads/Error_Screenshot.png)
— it dispatched, showed "Video ready in 5 min" for a few seconds, then the worker
crashed. Root cause: `video_service._dispatch_motion_transfer` (the shipping
motion-transfer path) calls `time.time()` in 6+ places for gen telemetry
(prep_ms/kling_ms/total_ms) but `video_service.py` had NO top-level `import time`.
The only `time` imports were `import time as _t` inside *other* functions and an
inline `import time` at L1170 — all AFTER the dispatch block at L952-1048. So the
name was unresolved exactly where it ran. Fix = one top-level `import time`
(commit 42b6372). Pre-existing, present in HEAD — it had been latent because that
telemetry block (added later) was **never exercised end-to-end before deploy**.

**Why it shipped (and the avoid-it lesson):** the file uses scattered **inline
imports** (`import os`/`import uuid`/`import time as _t` inside individual
functions). That style makes a module look "imported somewhere" while leaving
other functions referencing it with nothing in scope — and it's invisible to a
top-level-only grep. Two prevention levers:
1. **Lint the name-resolution class on every backend change, before commit/deploay:**
   `.venv/bin/python -m ruff check <changed files> --select F821,F811,F405,F822,F823`.
   ruff 0.15 is already in the venv. F821 would have caught this `time` use directly.
   Treat a non-empty result as a blocker, same as a failing test.
2. **Prefer top-level imports over inline ones** for stdlib in a module — inline
   imports localize a name to one function and breed exactly this "imported in
   func A, used unguarded in func B" trap. (Inline is only worth it for genuinely
   optional/heavy deps.)
3. **Smoke-test the real path after a backend deploy** — this crashed on the FIRST
   real gen; one end-to-end gen on the deployed build surfaces a whole class of
   "never actually ran" bugs that static checks can miss.

**The lesson is about HOW I looked for siblings, not the bug itself.** My first
instinct was a hand-rolled regex audit: grep `module.attr(` usages vs `^import`
lines. It printed `MISSING IMPORTS: ['os','random','re','tempfile','time','uuid']`
— **5 of 6 were FALSE POSITIVES.** Those five WERE imported, just **inline inside
the functions** (`import os` mid-function, `import uuid` at point of use), which a
top-level-only `^import` regex can't see. Only `time` was real. If I'd trusted
that list I'd have added six needless top-level imports and learned nothing.

**Why regex is the wrong tool here:** undefined-name detection requires a real
scope tree — module scope, per-function scope, inline imports, `import x as y`
aliases, conditional imports. Text matching can't model scope, so it both
false-positives (inline imports it can't see) and false-negatives (a name used
before its inline import; an `as`-alias).

**How to apply:**
1. **Use `ruff check --select F821` (or pyflakes/flake8) for undefined names**, not
   grep. It's scope-aware: `F821` fires only when a name is genuinely unresolvable
   at that point. Also useful: `F811` (redef/shadowed import), `F822` (undefined in
   `__all__`), `F405` (may-be-undefined from star import), `F823` (use before
   assignment). Command used S87:
   `.venv/bin/python -m ruff check src/ scripts/ --select F821,F811,F405,F822,F823`
   (ruff 0.15 was already in the venv; no install needed).
2. **TS/mobile equivalent is `tsc --noEmit`** — it resolves names/scopes properly;
   grep is just as wrong there.
3. **When a use-without-import bug appears, sweep the whole class with the proper
   linter** (gen path first, then all paths), don't eyeball — but report only what
   the scope-aware tool flags, never the raw regex list.
4. If you ever DO show a regex-based audit, label it as heuristic + verify each hit
   by reading the file (inline imports!) before acting. S87: the verify-by-reading
   step is the only reason I caught that 5/6 were false.

Sibling lessons: [[feedback_one_clean_verification_not_flailing]],
[[feedback_verify_tool_output_before_chaining]] — same theme: don't trust a crude
signal; use the right tool and confirm before acting.
