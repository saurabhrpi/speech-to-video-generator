---
name: TestFlight Beta App Review approval — source of truth
description: ASC web UI's yellow warning and public-link page reflect approval state inconsistently; the live testflight.apple.com URL served to a browser is the authoritative signal
---

To verify whether a TestFlight External Testing build has actually cleared **Beta App Review**, do NOT trust ASC web UI signals alone — they cache and update inconsistently across sections. Authoritative sources, in order of reliability:

1. **Apple's approval email** ("Your beta app build is approved" / "Your beta build is now available for testing") — sent to the developer email on the Apple Developer account when Beta App Review approves.
2. **Tap the public link in a mobile browser** (e.g., `https://testflight.apple.com/join/XXXXXXX` in Chrome on iPhone). The served page is the backend truth:
   - **"This beta isn't accepting any new testers right now"** = NOT yet approved (still in or pending review). Same message also covers tester-cap-reached and link-disabled, but for a fresh group with 0 testers and the link enabled, this means review.
   - **App name + "Open in TestFlight" / "View in TestFlight" / "Install" button** = approved, link is live, share away.
3. **TestFlight Builds tab status** in ASC ("Waiting for Review" / "In Review" / "Ready to Test" or "Approved") — usually correct, but can lag.

Unreliable signal: the **yellow warning banner** ("Testers cannot join public link until this group has an approved build") on the External group's Testers tab. Observed S53 to disappear *before* actual approval — likely a caching/state issue in ASC web UI. Don't share the link based on this banner disappearing alone.

**State transitions and timing:** "Waiting for Review" → "In Review" → "Ready to Test" (= approved). "In Review" means a reviewer is actively processing it; transition to approved is usually within a few more hours once it hits "In Review." First-time Beta App Review submissions take ~24h typical, sometimes much faster. Subsequent builds (minor changes) often near-instant auto-approval.
