---
name: replit-ahead-of-origin
description: Replit's "Publish" workflow auto-commits 2 commits per redeploy (a merge from GitHub origin + a "Published your App" marker) that never push back. The resulting "N commits ahead of origin/v2" warning is harmless tracking, not lost work — ignore it.
metadata:
  type: reference
---

**Rule:** When `git status` on the Replit shell says "Your branch is ahead of 'origin/v2' by N commits," **ignore the warning.** Do not `git reset --hard` to clean it up — those commits are Replit's own deployment bookkeeping.

**Why it happens:** Every Replit "Publish" / redeploy creates two commits that never push back to GitHub:

```
abc1234 Published your App                                   ← Replit-auto: publish marker
def5678 Merge branch 'v2' of https://github.com/.../v2       ← Replit-auto: merge from GitHub
0123abc <our actual commit from local dev>     (origin/v2)
```

So N redeploys ≈ 2N commits ahead. S74 saw ~24 ahead after ~12 redeploys.

**How to apply:**

- The "N commits ahead" is cosmetic. The deployed code is what's reachable from Replit's HEAD as ancestors — usually our latest commit IS in there because Replit fetched + merged on the most recent Publish.
- To verify what's actually deployed, look at where `(origin/v2)` is in `git log --oneline -30` on Replit. That's the last GitHub commit Replit knows about. If our recent push isn't above it, Replit's `origin/v2` reference is stale — `git fetch && git pull origin v2`, then re-Publish.
- **NEVER `git reset --hard origin/v2` on Replit** to clean up the divergence — you'd wipe Replit's `Published your App` tracking commits and potentially break its own bookkeeping. If you really want to reset, do it AFTER understanding what's there via `git log origin/v2..HEAD --oneline`.

**Diagnostic recipe** (paste output here next session if confused):

```bash
git log --oneline -30                       # see Replit HEAD vs (origin/v2) marker
git log origin/v2..HEAD --oneline           # the N divergent commits
git fetch origin && git log -1 origin/v2    # what GitHub actually has
```

**Source:** S74 — user noticed "24 commits ahead" on Replit and asked if anything was wrong. Verified via the SHA pattern that all 24 were auto-generated `Published your App` / `Merge` commits from Replit's own publish workflow.

See related: [[replit-workspace-vs-deployment-secrets]], [[replit-republish]], [[verify-deploy-before-integration-test]].
