---
name: EAS Build TestFlight workflow (local-signing escape hatch)
description: Step-by-step Expo EAS Build + Submit flow for shipping an Expo app to TestFlight without touching the local Mac keychain
type: reference
---

When local Xcode signing is blocked (post-keychain-reset, missing dev device, WWDR chain issues, or any time the rabbit hole is deeper than a few commands), **pivot to EAS Build**. Expo builds and signs on their servers using their own managed credentials; zero local-keychain involvement.

**Prereqs (one-time):**
- Paid Apple Developer account (Individual or Organization).
- Expo account at expo.dev (free).
- `app.json` has `ios.bundleIdentifier` set (e.g., `com.saurabh.interiortimelapse`).

**Flow (tested end-to-end in Session 31, 2026-04-14):**

1. From the Expo app root (`mobile/` in this project):
   ```bash
   npx eas-cli login            # Expo account
   npx eas-cli init             # creates EAS project; writes extra.eas.projectId into app.json
   npx eas-cli build:configure  # creates eas.json with development/preview/production profiles
   ```

2. Build for TestFlight (production profile = store distribution):
   ```bash
   npx eas-cli build --platform ios --profile production
   ```
   First run prompts for Apple ID + 2FA. EAS registers the bundle ID with Apple, generates a Distribution cert and App Store provisioning profile server-side, uploads the project tarball, then builds. ~15-20 min. Prints a live URL: `https://expo.dev/accounts/<owner>/projects/<slug>/builds/<id>`. Export-compliance question: answer Y if the app only uses standard HTTPS/TLS (sets `ITSAppUsesNonExemptEncryption: false`).

3. Submit to App Store Connect:
   ```bash
   npx eas-cli submit --platform ios --profile production --latest
   ```
   Auto-creates the App Store Connect app record on first run (if missing). Uploads the `.ipa`. Apple then processes the binary for 5-30 min before it appears in TestFlight. The account holder gets an auto-invite so they can self-test before inviting others.

4. Internal tester invite (fastest path for one reviewer): App Store Connect → Users and Access → add friend's Apple ID with role **Developer**, restricted to the single app. Then TestFlight → Internal Testing → create group → add tester → enable the build. Instant, no Apple review.

   External testers: just need an email but first build requires ~24h Beta App Review.

**Why this matters:** Completely sidesteps WWDR chain issues, partition-list traps, orphan-key dead-ends, and the "need registered device to archive" block. The iPhone does not need to be connected to the Mac at any point.

**How to apply:** Recommend EAS Build any time local codesigning fails twice in a row, or when the user is on a fresh Apple Dev account without a registered device, or when they just want to ship to TestFlight without learning macOS keychain internals.

**Session 31 artifacts (for reference):** EAS projectId `201c304f-0f16-4a53-a314-5b9b560e9035`, Expo owner `saurabhsvits`, App Store Connect app id `6762175047`, bundle id `com.saurabh.interiortimelapse`, Apple Team id `AP2Q6H2AYH`.
