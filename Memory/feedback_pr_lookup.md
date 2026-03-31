---
name: Use gh CLI to look up PR history, not git merge-base
description: Squash merges break git ancestry — always use gh pr list to find merged PRs instead of inferring from git merge-base.
type: feedback
---

Use `gh pr list --state closed/merged` to find merged PRs, not `git merge-base`. Squash merges break the ancestry chain — commits on main don't share history with branch commits, so merge-base gives wrong results.

**Why:** Session 9 (2026-03-29): Used `git merge-base` to find the last PR merge point, concluded there were no prior merges from interior-timelapse into main, and confidently told the user all 37 commits were new. User had actually merged 3 PRs. The data was available via `gh pr list --state closed` but I used the wrong tool and presented the wrong answer as fact.

**How to apply:** When asked about PR history, merged changes, or "what changed since last PR" — always use `gh pr list`, `gh pr view`, or `gh api` to find the actual PRs. Never infer merge history from git ancestry alone.
