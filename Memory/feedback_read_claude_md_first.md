---
name: Read CLAUDE.md before diagnosing
description: Before debugging user-reported symptoms, scan CLAUDE.md for design facts that explain the symptom before hypothesizing bugs
type: feedback
---

Before forming hypotheses about a user-reported symptom, check CLAUDE.md for design decisions that explain the behavior. Many symptoms that look like bugs are actually documented design choices.

**Why:** Session 33 — user reported "sign in required on second Generate click." I spent time speculating about cookie bugs before the user pointed out `UNAUTH_GEN_LIMIT=1` is in CLAUDE.md ("Usage limiting: IP+UA hash for unauth, `UNAUTH_GEN_LIMIT` (default 1)"). The "one free trial, then sign-in" flow is baked into the design — not a bug to diagnose. I should have connected the symptom to that design fact immediately.

**How to apply:** When the user reports a behavior, first ask: "is this documented as intentional in CLAUDE.md?" If yes, the investigation is about why the *intended* behavior is triggering for the user (e.g. why the server sees them as unauth), not about whether the behavior itself is wrong. Internalize the app's design before proposing bugs.
