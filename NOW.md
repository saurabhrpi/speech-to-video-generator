# Session Log

> **STICKY (do not remove):** Read Motto-and-Mantra.txt and [REQUIREMENTS.md](REQUIREMENTS.md). ToDo's live in [ToDo.md](ToDo.md) — do not remove items unless user says. If you're ever unsure about ANYTHING, feel free to do web search, as many time as you like. If you get blocked doing web search by the system, just prompt me and I will approve it.

## Current Session: 75 — 2026-05-23 / 2026-05-24 — branch `v2`

**Status:** Built the Iconic Dances row (Rasputin + Boot Stop Working published; Cotton Eye Joe + Don't Play With Me + Twist and Shine have Klings ready but unseeded). Bombale (Extended) renamed to Bombale. Bad-chef + Bad-open variants attempted then killed by a Kling depth-axis-moonwalk-inversion failure (AIV-103). Beat It preview given a +0.5s audio shift (hypothesis fix, unverified). Total Kling spend ~$15.

## What happened this session

**Verified the S2/S74 NBP aspect fix in prod.** First real iPhone gen on Smooth Criminal came back square. Bad-chef + Boot Stop spot-checks also clean.

**Iconic Dances row created.** New category `iconic_dances` (mechanical title-case, no `CATEGORY_LABEL_OVERRIDES` entry needed). Rasputin + Boot Stop Working seeded, published, preview-as-driver aligned.

**3 more Iconic Dances Klings done, not yet seeded:** Cotton Eye Joe, Don't Play With Me, Twist and Shine. DPWM was re-generated after first attempt was 15s-trim-chopped + had ~0.5s audio lead; the recovered 16.87s version still has slight residual lag in early half + lips don't quite match driver — borderline ship-worthy.

**Bad template killed.** 6 Kling configs tried on the HubX moonwalk source (v2.6+pro, v3+pro, prompt-steer, compound time-flip, combos). All produced depth-axis-inverted body translation (forward instead of backward). Tracked in [AIV-103](https://linear.app/speech-to-video/issue/AIV-103/bad-template-depth-axis-moonwalk-inversion-kling-mc-limitation) with 4 ranked fix paths.

**Audio sync investigation.** Diagnosed Kling MC outputs at 30fps regardless of driver framerate (verified N=3). The +0.5s ffmpeg-itsoffset shift fixed DPWM's lead per user. Applied same shift speculatively to Beat It preview; propagation through preview-as-driver to runtime user gens is the working hypothesis but **NOT verified** — Beat It is the test case.

**AIV-102 comment posted** documenting the requirement that the future generic builder must support multiple variants per source (slug as row key, source sharing by reference, slot-filled prompts + override escape hatch). Surfaced by today's Bad-chef + Bad-open chained off the same Bad.mov.

## Live state at session close

- **Code:** `origin/v2 = 18fc600`. Uncommitted: 7 new chain scripts (rasputin, boot_stop_working, bad_chef, bad_open, cotton_eye_joe, dont_play_with_me, twist_and_shine), 2 new seed scripts (rasputin, boot_stop_working), 2 new memory files + MEMORY.md index updates, NOW.md.
- **Spend:** ~$15 Kling-side, mostly on Bad-variant experiments.

## Next step — Session 76

1. **Verify Beat It preview audio fix.** User runs a real selfie gen on Beat It and checks A/V sync. If clean → batch the +0.5s shift across the other 8 shipped templates. If still off → adjust offset OR conclude the propagation hypothesis is wrong (don't batch).

2. **Seed + publish Cotton Eye Joe + Twist and Shine** under Iconic Dances. (Decide DPWM publish/hold based on user's tolerance for the residual lip-sync drift.)

3. **Commit uncommitted work** — 7 chain scripts + 2 seed scripts + 2 memory files + NOW.md.

4. **V2.0.1 ship work** (S74 carryover) — AIV-97 credit refresh, AIV-98 Show My ID, revert AIV-94 UID logging, version bump, EAS build + TestFlight.

## Open questions

1. **(NEW S75)** Beat It audio-shift hypothesis — does preview-side `-itsoffset` propagate through Kling's runtime audio handling? Verify before batching.

2. **(NEW S75)** DPWM lip-sync drift — Kling MC isn't a lipsync product; this may be a fundamental limitation.

3. **(NEW S75)** Bad moonwalk (AIV-103) — first retry would be Kling I2V with text prompt, ~$2 ceiling.

4. **(NEW S75)** Kling client 600s timeout vs pro-mode + long drivers. User REJECTED bumping client cap ("can't have >10min runtime wait"). If pro+v2.6 keeps timing out at 580-612s on 16s+ drivers, flip runtime to v3 instead (AIV-101 one-line config change).

5. **(S74 carryover)** Preview-as-driver monitoring across the now-11 templates. Mechanism to revert: `scripts/set_preview_template_driving_video.py --all --revert`.

6. **(S74 carryover)** AIMLAPI `nano-banana-pro-edit` for NBP-edit-driven repositioning — worth investigating.

7. **(S74 carryover)** UX risk: users see pro-mode previews (1440×1440) and get std-mode runtime output (~960×960). Accepted; revisit if real users complain.

8. **(S74 carryover)** Future: bump preview chain scripts `kling-v2-6` → `kling-v3` for facial-consistency. Spike A/B before flipping.

9. **(S74 carryover)** Auto-bump `updated_at` on Firestore template writes (write-through hook in `template_registry.py`) so partial updates can't desync `/api/templates` ETag.
