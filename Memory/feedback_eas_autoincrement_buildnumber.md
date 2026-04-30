---
name: EAS auto-increments buildNumber — don't manually bump
description: Don't edit buildNumber in mobile/app.json before eas build --profile production; EAS auto-increments and manual bumps cause skipped numbers
type: feedback
---

Don't manually edit `buildNumber` in `mobile/app.json` before running `eas build --profile production`. EAS auto-increments it.

**Why:** `mobile/eas.json` has `"autoIncrement": true` in the `production` profile and `"appVersionSource": "local"` at the CLI level. EAS reads `buildNumber` from `app.json`, increments by 1, builds with the incremented value, and writes the new value back to `app.json`. Manually bumping double-bumps: e.g., S52 left app.json at 10, S53 manually bumped to 11, EAS then built #12 — Build #11 was skipped. ASC still accepts it (build numbers only need to monotonically increase) but the manual edit was redundant work and confusing.

**How to apply:** When prepping a production iOS EAS build, leave `buildNumber` alone in `app.json`. The number that lands in TestFlight will be one higher than the current `app.json` value. Other `app.json` fields (`version`, `supportsTablet`, plugins, infoPlist, etc.) still need manual edits as usual — only `buildNumber` is auto-managed. Also: this means ToDo.md item #25's "MUST DO BEFORE NEXT BUILD" framing on bumping buildNumber is obsolete — that item was wrong.
