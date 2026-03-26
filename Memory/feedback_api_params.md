---
name: AIMLAPI providers use different parameter names — always verify against API docs
description: Each video model provider behind AIMLAPI has its own parameter names. Silent failures when wrong names are used — parameters are ignored, not rejected.
type: feedback
---

AIMLAPI proxies multiple providers (Kling, Hailuo, Seedance) and each has its own API schema. Parameter names differ across providers — e.g. Kling uses `tail_image_url` for end-frame control, not `last_image_url`. AIMLAPI silently ignores unrecognized parameters, so the request "succeeds" but the feature doesn't work.

**Why:** The Kling `last_image_url` bug went undetected for the entire development of the timelapse pipeline. Kling was generating every transition video without end-frame control, freestyling from the first frame + prompt. The wrong parameter name was the root cause of problem #1 (transition video quality), not prompt wording.

**How to apply:** When a model feature isn't working as expected (especially with AIMLAPI), check the provider's actual API schema for correct parameter names BEFORE investigating prompt engineering. Silent parameter ignoring is a likely failure mode. Never assume parameter names are consistent across providers.
