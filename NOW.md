# Session Log

> **STICKY (do not remove):** Read Motto-and-Mantra.txt. ToDo's live in [ToDo.md](ToDo.md) — do not remove items unless user says. If you're ever unsure about ANYTHING, feel free to do web search, as many time as you like. If you get blocked doing web search by the system, just prompt me and I will approve it.

## Current Session: 53 — 2026-04-26 / 2026-04-30 — main (closing)
**Status:** First App Review came back REJECTED on 3.1.1 (Restore Purchases UI for consumables) + 2.1(b) (Buy Credits unresponsive — root cause: Paid Apps Agreement was "Pending User Info"). Both fixed end-to-end and Build #13 resubmitted with reply explaining each fix. Awaiting Apple's verdict on the resubmission.

## What happened this session

- **Initial "Add for Review" blocker — 13-inch iPad screenshot requirement.** ASC refused to submit because `supportsTablet: true` flagged the app as Universal. Switched to `supportsTablet: false` (matches CLAUDE.md mobile-only vision), prebuild, EAS Build #12, attached, submitted. v1.0 entered "Waiting for Review."
- **Apple rejected v1.0 / Build #12 on two guidelines.**
  - **3.1.1 (Restore for consumables):** Settings + Paywall both surfaced a "Restore Purchases" button. All our IAPs are consumables — Apple's rule is they cannot be restored via Apple Account.
  - **2.1(b) (Buy Credits unresponsive):** root cause was **Paid Apps Agreement = "Pending User Info"** (bank + W-9 not yet completed). When pending, ASC refuses to expose IAP products to StoreKit. RC threw "products empty" red error on the Paywall; tapping pack buttons did nothing → reviewer cited "unresponsive."
- **Code fix shipped** in `mobile/app/settings.tsx` + `mobile/components/Paywall.tsx`: removed user-facing Restore UI (Settings button + Paywall link), rewrote 2 edge-case error messages from "tap Restore" → "email support@speech-2-video.ai." Underlying `restoreAndGrant` helper kept in `lib/purchases.ts` for future internal recovery (e.g., ToDo #19 CustomerInfo listener). Verified: tsc clean (only pre-existing Button.tsx error, ToDo #10), simulator end-to-end smoke test passed.
- **iOS modal-on-modal bug surfaced + fixed.** Settings is a modal route (`presentation: 'modal'`); Paywall is a root-level `Animated.View` overlay. Tapping Buy Credits in Settings made Paywall open *behind* the Settings modal — symptom: button flash, no visible response. Fix: `router.back()` before `openPaywall()` in Settings's Buy Credits handler. Apple's reviewer didn't catch this because they tested on iPad-scaled mode where modal stacking differs.
- **ASC config completed: bank + W-9 + Paid Apps Agreement Active.** US bank account (selected branch matching account-opening city), W-9 as individual non-exempt payee not subject to backup withholding. All three Business-page rows now Active.
- **Build #13 shipped + resubmitted.** EAS autoIncrement produced #13 (per `feedback_eas_autoincrement_buildnumber.md`). Attached to v1.0 (replaced #12), replied to rejection thread with 2-section explanation (3.1.1 UI removed + 2.1(b) Paid Apps Agreement now Active), clicked Add for Review. Now in "Waiting for Review."
- **Side conversations memorialized or deferred:**
  - **Friend's app-transfer-to-dad** plan extensively discussed: individual vs C-Corp vs Indian Pvt Ltd ownership; US-India treaty Article 12 (15% royalty withholding); PE risk, visa restrictions on friend continuing US-based dev work, sham-transfer evidence trail via Apple login IPs. **App Transfer criteria verified verbatim against Apple docs** — App Store release required, NO 60-day cooldown (corrected my earlier wrong claim). Saved as `reference_app_transfer_criteria.md`.
  - **Apple ID creation issues for dad in India:** diagnosed as corporate-WiFi IP/proxy fingerprint trip. Recommended retry from home WiFi after 24-48h via iPhone-native flow.
  - **M365 / Entra tenant** for `support@speech-2-video.ai`: discovered registrar-bundled (likely GoDaddy) Microsoft 365 subscription. Applied "do not allow user consent" recommendation; deferred keep-vs-migrate decision as ToDo #26.
- **10 new memories saved this session** (8 from S52 carryover that were untracked + 2 new from S53): EAS auto-increment, iOS encryption flag auto-clear, no EAS build emails, TestFlight approval source of truth, App Transfer criteria, Paid Apps Agreement Active before submit, no Restore UI for consumable-only apps, plus S52 ones (verify-state-before-recommending, save-memory-only-after-verification, Pressable+NativeWind).

## Next step — Session 54 (on resume)

**Wait for Apple's verdict on the resubmission.** Three branches:

1. **Approved** → app moves to "Pending Developer Release." Decide release timing. **Important:** actual App Store release is the prerequisite for any future App Transfer to dad. After release, the friend-to-dad transfer plan can resume — but dad still needs his Apple Developer Program enrollment (blocked on the corporate-WiFi creation issue; recommend he retry from home WiFi).
2. **Rejected on something new** → fix and resubmit. Landmines we haven't been hit by yet: 5.1.1(v) (account deletion — we have it), 2.1 (device crash — TestFlight on physical device never happened, deliberate bet).
3. **Long delay (>72h)** → check ASC for reviewer messages; reply if needed.

**While waiting, optional non-blocking work:**
- **ToDo #1** (server-side TOCTOU credit gate, Yellow) — should land before any wider TestFlight release.
- **ToDo cleanup pass**: #15 (S52 done), #23 (S52 done), #24 (S52 done), #7 + #22b (Kling, OBSOLETE) all need striking.
- **ToDo #19** (CustomerInfo listener) — closes the edge cases that currently route to support email after we removed user-facing Restore.

## Open questions (carryover + new)

- **(S53 result) Apple's resubmit verdict.** Awaiting. If approved + released, App Transfer to dad becomes possible.
- **(S53 new) Dad's Apple Developer enrollment blocked** on "Your account cannot be created at this time" — diagnosed as corporate-WiFi fingerprint trip. Retry after 24-48h from home WiFi via iPhone-native flow recommended.
- **(S53 new) M365/Entra tenant decision (ToDo #26)** — keep paying ~$6/mo for `support@speech-2-video.ai` mailbox, or migrate to free forwarder (Cloudflare Email Routing / Zoho / iCloud+ Custom Domain). Not urgent.
- **(S52 carryover from #6)** TestFlight smoke test on a physical device never happened. iOS sim + EAS build was the bet. If Apple rejects on a device-specific issue, this is the obvious next step.
- **(S48 follow-up B, still open) UX hole: home button shows action label only, balance only in Settings.** Decision needed post-launch: chip above button, badge on gear icon, or status pill in tab bar.
- **(ToDo #1, S50 origin)** Server-side TOCTOU credit gate. Client mitigation shipped, server still vulnerable to concurrent submits. Yellow — must land before wider TestFlight.
- **(ToDo #19, S49+S48)** CustomerInfo listener for offline-replay + RC ingestion-lag. With user-facing Restore now removed (3.1.1 fix), edge cases (no txId returned, server grant fails after StoreKit success) currently route to support email. Pre-launch this is fine; post-launch should land before scale.
- **Backend Apple precheck + clip-merge (Yellow #10).** Haven't verified `/api/auth/apple/precheck` + `/api/clips/merge` exist in `server.py`. Clip-orphan risk on anon→Apple collision.
- **(S43-era, future trigger)** RC `default` offering "Current" is implicit today. Day a second offering is added, if `Purchases.getOfferings().current` returns null, check RC dashboard for explicit "Current" toggle.
- **(ToDo #10, post-launch)** Gallery cards still use prompt text + play icon — no image thumbnails. Reasonable V2 polish.
