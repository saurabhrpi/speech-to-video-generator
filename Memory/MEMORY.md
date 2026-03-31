# Project Memory

## User Preferences
- Prefers Claude Opus 4.6 (set permanently in global settings)
- Dislikes Sonnet
- Don't evaluate or reassure on answers. Be a sharp interviewer and precise scribe, not a startup mentor.
- Obsessed with the vision — internalize it or miss the mark
- Values deep analysis over surface-level summaries

## Product Vision (captured 2026-03-22)
- Mission: Automate hyper-realistic interior renovation timelapse videos (15-25s) for UGC makers
- Target users: TikTok/Instagram freelancers, marketing agencies for interior designers
- They currently create this content MANUALLY — the app replaces that workflow
- Architecture borrowed from a freelancer's viral AI video course (iterative I2I -> I2V -> stitch)
- Interior Timelapse tab is the ONLY core product. Video Studio and Speech-to-Video are secondary.
- UX: Almost hands-off one-click. Room type, style, features = the 3 key inputs.
- Not attached to any model. Will switch if better ones emerge.
- Quality bar: hyper-realistic, as if filmed by a crew on-site
- 6-month goal: $10K/month net profit
- Current cost: ~$7/generation, ~20-25 min. Betting on model price drops for big wins.

## Known Problems (Priority Order)
1. ~~Transition video quality~~ — ROOT CAUSE FOUND (2026-03-24): Kling param was `last_image_url` instead of `tail_image_url`. End-frame was silently ignored. Fixed. Hailuo still garbage.
2. Visual delta between stages sometimes too small
3. Can't reliably handle >2 features
4. Prompts for indoor vs outdoor spaces don't transfer well

## Key Technical Facts
- Config is a plain dataclass with os.environ.get(), NOT pydantic-settings
- GPT model is gpt-5.2 (set in .env), not gpt-4 (code default)
- Job manager is ephemeral (in-memory, lost on restart)
- App.tsx is ~1240 lines — all state via hooks, no state library
- dzine.ai integration configured but not actively used

## Feedback
- [Don't micro-manage prompt wording for I2I quirks](feedback_prompt_fixes.md) — rare model variance != systematic defect; wordsmithing has low ROI and risks regressions
- [AIMLAPI providers use different param names](feedback_api_params.md) — silent failures when wrong names used; check API docs before investigating prompts
- [Never fill gaps with assumptions](feedback_no_assumptions.md) — REPEATED VIOLATION; confidence without verification is the failure mode; trace end-to-end or say "I don't know"
- [ALWAYS complete all 5 steps of Data Flow Verification](feedback_data_flow_verification.md) — never stop at the function return; verify the call site consumes it and the downstream code accesses it
- [Sync Memory folders](feedback_memory_sync.md) — every memory update must be written to both locations
- [Change summary format](feedback_summary_format.md) — ~6 word heading + body (max 800 chars) with each change as a separate paragraph
- [Change Impact Analysis Protocol](feedback_change_impact_analysis.md) — every code change must include structured impact report: change, flow, downstream effects, costs, guardrails
- [Use MEMORY.md one-liners as pre-change checklist](feedback_memory_checklist.md) — scan Feedback section before every code change; only read full files when one-liner isn't enough
- [Never edit files without explicit permission](feedback_no_edits_without_permission.md) — do not write/edit/create ANY file unless user explicitly says to; propose and wait
- [Use gh CLI for PR history](feedback_pr_lookup.md) — squash merges break git ancestry; use gh pr list, not git merge-base

## CLAUDE.md
- Fully rewritten 2026-03-22 with technical analysis + product vision interview
- Includes: vision/mission, target users, architecture origin, known problems, dev standards, API reference
