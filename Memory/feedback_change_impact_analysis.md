---
name: Change Impact Analysis Protocol
description: Every code change must include a structured impact analysis report before implementation — describe change, flow, downstream effects, costs, guardrails
type: feedback
---

Every code change MUST include a structured impact analysis in the response BEFORE implementation. No exceptions.

**Why:** Preventing regressions is more important than shipping fast. The user wants proof that every change has been thought through — not just "it should be fine" but a concrete walkthrough of what happens downstream.

**How to apply:** For every code change, report this analysis in the response:

1. **Change:** What is being added/modified/removed?
2. **Flow:** Where does this change sit in the execution flow? What runs before and after it?
3. **Downstream effects:** Is anything breaking, affected, or changing behavior? Walk through every downstream consumer. If yes, describe exactly what changes.
4. **Costs:** Not just money — also latency, API calls, compute, effort, complexity. If yes, quantify.
5. **Guardrails:** Are there worst-case scenarios (infinite loops, cascading failures, state corruption)? If yes, describe the guardrail needed.

If any of items 3-5 apply, they must be explicitly included in the report. Don't skip them with "no impact" — show the reasoning.
