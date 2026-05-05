---
name: Find the git commit SHA behind a specific EAS build
description: Use `eas build:list` to map version + build number → git commit SHA. Essential for creating hotfix branches from the exact code Apple reviewed.
type: reference
---

EAS records the source commit at build time. To find which commit a specific build was cut from (e.g., to create a hotfix branch from the exact code Apple reviewed):

```bash
cd /Users/saurabhsmacbookair/POCs/speech-to-video-generator/mobile
eas build:list --platform=ios --status=finished --limit=5
```

Each entry includes a **Commit** field (full SHA), Version, Build number, Started/Finished timestamps, and the build's `Logs` URL. Find the row matching the version + build number you care about and copy the Commit SHA.

**Why this matters for App Store hotfixes:** when Apple rejects a build, the cleanest resubmit strategy is a hotfix branch cut from the EXACT commit they reviewed — not from current `main` (which has unrelated work piled on). A minimal-diff resubmit is far less likely to attract new review issues.

```bash
# After identifying the SHA, branch from it:
git stash push -u -m "wip"               # save in-progress work first
git checkout -b hotfix-buildN <SHA>      # create hotfix branch
# apply ONLY the rejection-targeted fixes
# eas build → submit as build N+1
# after approval, merge hotfix branch back into main, pop stash
```

**Verified S54 (2026-05-02):** Build #13 was at `6971edaf7bf1c730bfeac7038c15b8b942e71beb`. Hotfix branch `hotfix-build14` was cut from that SHA, fixes applied, Build #14 shipped. Strategy kept the diff to ~5 files vs. the 20+ files of unrelated S54 work on main.

**Caveat:** the `eas build:list` output has no JSON flag in older `eas-cli` (v18.9 confirmed plain text). Either grep manually or pipe to `awk` if scripting.
