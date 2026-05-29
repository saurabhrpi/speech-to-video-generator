---
name: project_reliability_target_and_telemetry
description: V2 runtime-gen reliability target (99.99% within 5-6 min), why the S84 4-point timeout redesign was rejected, and the telemetry-first path to the real fix
metadata:
  type: project
---

User's hard target for V2 runtime template-video generation: **99.99% of prod gens succeed within 5 min (6 min absolute outer edge). An SLA breach (>5 min) is itself a failure**, not just an outright error. Sim anecdote that triggered this: ~1 of 3 gens failed with "Generation failed" — unacceptable.

**The S84 4-point Kling-timeout redesign was REJECTED at S85** (rip out client retry · stretch backend max_wait 600→900s · progress-stuck detection · auto credit-refund). Reason: those are symptom-management — they reduce the *pain* of a failure (longer wait, friendlier message, refund), not the *rate* of failure or SLA breach. (Note: NOW.md "Next step" may still describe this rejected plan — it's stale; fix at close.)

**Why the target can't be hit by waiting/retrying smarter:** the dominant bottleneck is Kling Motion Control — a third party with 3-12 min latency variance (S83), no cancel endpoint, and intrinsic moderation/hang failures. A *single* Kling call structurally cannot be 99.99%-reliable-within-5-min; even successful calls breach 5 min a large fraction of the time.

**Path:**
- **Step 0 (shipped S85, commit `a016a8a`):** durable per-stage telemetry → Firestore collection `gen_events` (`utils/gen_telemetry.py`, read via `scripts/gen_telemetry_report.py`). Kling client now labels `failure_kind` (timeout | kling_failed | submit_error | empty_result) + `last_task_status` (timeout discriminator: `submitted`=true hang vs `processing`=slow). Get a real baseline + failure taxonomy before choosing the fix — no fabricated root causes.
- **Then the real architectural fix** (choose from telemetry data, not guesses): staggered hedged/redundant Kling submission to crush tail latency + raise success via `1−(1−p)^k`; provider redundancy (Higgsfield, AIV-109) to kill the single-point-of-failure; fastest-reliable Kling mode (config-driven, `set_kling_runtime.py`); hard per-stage budgets; cheap base-reliability wins (fast-failure retries, selfie input gating).

**Cost tension:** hedging multiplies COGS (~$1.50/gen Kling vs 25-coin retail), so any redundancy must be tail-gated (escalate only when slow), and base reliability raised first so escalation rarely fires. There's a reliability-vs-margin dial to set once data lands.

Related: [[feedback_no_client_retry_for_uncancellable_jobs]] (don't auto-retry uncancellable jobs — still valid even though the wider 4-point plan was dropped).
