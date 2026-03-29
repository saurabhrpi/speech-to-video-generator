---
name: Don't micro-manage prompt wording for I2I model quirks
description: Avoid fragile prompt wordsmithing to work around I2I model interpretation issues — low ROI, high risk of regressing other prompts
type: feedback
---

Don't try to fix rare I2I model interpretation issues by micro-managing GPT's prompt wording. Example: Nano Banana Pro Edit interpreted "keep exposed brick untouched" too broadly (preserved surrounding wall area too), but trying to tell GPT to say "preserve only the [feature] surface itself" instead is a razor-thin distinction the I2I model likely won't parse differently.

**Why:** A 1-in-7 image quality variance is model-level noise, not a systematic prompt defect. Wordsmithing around it risks making other prompts worse for marginal gain. Also tends toward hardcoding (listing specific "surrounding surfaces") which violates project standards.

**How to apply:** Before proposing a prompt fix, ask: (1) Is this a systematic defect or rare variance? (2) Is the difference between current and proposed wording meaningful enough for the model to behave differently? (3) What's the risk of regressing other cases? If the answers are "rare / probably not / real risk," don't pursue it.
