---
name: anchor-preventative-fixes-in-concrete-plans
description: Before proposing "preventative" or "infra" work, consult the roadmap context already available (CLAUDE.md, docs/V2_*, Linear, NOW.md) and anchor the fix in something concrete and near-term — not in a future you haven't bothered to check
metadata:
  type: feedback
---

Before recommending any "preventative" / "infra hardening" / "while we're at it, let's harden X" work, **consult the roadmap context that's already in front of you and anchor the proposed fix in something concrete and near-term**. "I don't know what's coming" is almost always a lie I tell myself to skip the work — the project has CLAUDE.md, docs/V2_*, docs/V2_provider_license_audit.md, Linear's V2 milestone, NOW.md open questions, memory files. Read them. If after reading them I can't point to a specific near-term feature, decision, or constraint that makes the fix load-bearing, the fix is speculation dressed up as engineering.

**Why:** S64 — I proposed extending `/api/setup` to flag missing-but-required env vars, framed as "S63 hurt three times, let's harden." The user pushed back twice. First version of my excuse was "the cause is resolved." Second version was "I can't predict future env vars." Both were wrong. The actual error was that I implicitly claimed I could enumerate future env-var needs WITHOUT consulting the docs, plans, and Linear that contain the roadmap. CLAUDE.md's locked V2 provider stack already named everything coming in the near term (Veo via existing Vertex auth, Hailuo via existing MiniMax, Kling direct, Nano Banana via existing Vertex — none of which would require a new env var). If I had spent thirty seconds reading the plan before recommending, I'd have seen the "preventative measure" had nothing concrete to prevent.

**How to apply:**

- When tempted to recommend hardening / scaffolding / guardrails, **open the relevant docs first**: `CLAUDE.md`, the `docs/` plan files, the relevant Linear project + milestone, `NOW.md` open questions. Read the actual roadmap, not your reflexive memory of "we had pain."
- Then ask: can I point to a specific upcoming feature / decision / constraint in those documents that this fix addresses? If yes, propose with the anchor cited. If no, drop the proposal.
- **"Past pain happened N times" is never sufficient justification** for new preventative code. The question is whether the same pain class is plausibly going to recur given the **actual near-term roadmap** — and you can only know that by reading the roadmap.
- Watch for the surface-of-least-effort failure mode: latching onto an existing endpoint / config / module as "easy to extend" without first verifying the extension addresses anything anchored in the docs. Cheap to write ≠ valuable to ship. Almost-free preventative code that addresses nothing is still negative value (maintenance debt, surface area, false sense of safety).
- Cross-references: `[[feedback_elephants_first]]` (focus on load-bearing risks), `[[feedback_lock_then_track]]` (defer non-blockers), `[[feedback_verify_state_before_recommending_values]]` (read before recommending), `[[feedback_save_memory_only_after_verification]]` (this memory itself only saved after the user had to correct the framing twice — the FIRST version captured a weaker lesson).
