---
name: EAS local autoIncrement collides when building from an older commit
description: With `appVersionSource: "local"` + `autoIncrement: true`, EAS bumps app.json's buildNumber locally during build. Hotfix branches cut from an older commit (with a stale buildNumber) will collide with builds already in App Store Connect.
type: reference
---

`mobile/eas.json` is configured `appVersionSource: "local"` and `production.autoIncrement: true`. EAS reads `expo.ios.buildNumber` from app.json, bumps it by 1, **writes the bumped value back to your local app.json**, and stamps the artifact with the bumped value.

**The footgun:** when you create a hotfix branch from an older commit (e.g., the SHA of a rejected build) and build from it, your local app.json resets to that older commit's buildNumber. EAS bumps it from there, producing the SAME buildNumber as the previously-rejected build. App Store Connect rejects the upload as a duplicate.

**Concrete S54 incident (2026-05-02):**
- Build #13 (rejected): cut from commit `6971eda` where app.json had buildNumber=12. EAS bumped 12→13, produced Build #13.
- Hotfix branch `hotfix-build14` was cut from `6971eda` to keep diff minimal.
- Local app.json on hotfix branch: 12 (matching the commit).
- Fired `eas build` → EAS bumped 12→13 → produced ANOTHER Build #13. Collision.
- Wasted one build credit.

**The recovery (no manual edit needed):** local app.json is now at 13 (EAS wrote the bump to disk during the wasted build). Run `eas build` AGAIN — EAS will bump 13→14 and produce Build #14, no collision. The wasted Build #13 just sits in EAS history; `eas submit --latest` will pick the newer #14.

**Long-term mitigations** (consider before the next hotfix):

1. **Commit the EAS-bumped app.json back to git after each successful build.** Keeps your branches' app.json in sync with EAS reality. Annoying but accurate.

2. **Switch eas.json to `appVersionSource: "remote"`.** EAS tracks the build number on its server, ignoring local app.json. Hotfix branches from older commits don't collide because EAS server remembers the highest. Trade-off: app.json's buildNumber becomes meaningless / stale.

3. **Before firing a hotfix build, manually verify** local `mobile/app.json` `buildNumber` is `>` than the latest in ASC. If not, edit it once (skipping numbers is OK; collisions are not). Per `feedback_eas_autoincrement_buildnumber.md`, manual edits cause skipped numbers — but skipping #13 was the goal in this case anyway.

**Symptom in EAS output to watch for:** `Bumping expo.ios.buildNumber from N to N+1` where N+1 is already in ASC. If you see this, abort: don't run `eas submit` on that artifact. Re-run `eas build` to get N+2.
