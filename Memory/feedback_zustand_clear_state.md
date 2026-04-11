---
name: Zustand stores must clear state on new runs
description: Zustand pipeline store leaks old videoUrl/pipelineState/jsonOut into new runs if not explicitly cleared at start
type: feedback
---

Zustand stores persist in memory across user actions. When starting a new pipeline run, ALL result-related state must be explicitly cleared at the top of `runPipeline`, or old results bleed into the new run.

**Why:** User triggered a new pipeline run and saw a stale video from the previous run, plus a 401 error card appearing alongside a PipelineReview screen because `phaseCompleted` wasn't cleared when `videoUrl` was set.

**How to apply:** At the start of any "run" function in a Zustand store, clear all output state: `videoUrl`, `pipelineState`, `jsonOut`, `phaseCompleted`, `pipelineError`. Don't assume React re-renders will handle it — Zustand state is independent of component lifecycle.
