# Session Log

## Current Session: 5
**Date:** 2026-03-25
**Branch:** interior-timelapse
**Status:** Problem #1 root cause found and fixed. Kling end-frame control was never working.

## What Happened This Session
- **Root cause of problem #1**: Kling expects `tail_image_url`, we were sending `last_image_url`. Silently ignored — Kling was freestyling every transition video.
- **Added MOTION_PROMPT**: GPT now generates process-only transition prompts (no materials/styles). Had to fix a bug where it was produced but never stored in the stage dict.
- **PROTECT rule updated**: Clarified that only the feature's own texture is preserved, not surrounding surfaces.
- **Changes not yet committed.**

## Next Step
Test a full end-to-end generation with all three fixes active (tail_image_url + MOTION_PROMPT wired through + updated PROTECT rule). Evaluate transition video quality with real end-frame control.

## Open Questions
- Does Kling actually honor `tail_image_url` well, or will there still be quality issues now that it's wired correctly?
- The ceiling flicker in the 3rd video — was it caused by the missing end-frame, or is it a separate Kling limitation?
