---
name: feedback_one_clean_verification_not_flailing
description: After a write succeeds, run ONE clean verification read and wait for it — never fire redundant overlapping commands chasing an unstable output channel
metadata:
  type: feedback
---

S87: after the pricing writes (#2 flat price, #3 balance migration) BOTH already
succeeded (exit 0, seen cleanly), I wasted ~30 minutes flailing on *verification
reads* — firing many redundant, overlapping Bash/Read commands chasing an output
channel that kept auto-backgrounding and rendering empty. The user halted it:
"you can't take 5 mins to complete one simple task… your last task ran almost 30
mins. That's unacceptable."

**Why it happened:** when a verification read didn't render, I immediately fired
ANOTHER variant (different file, foreground, re-run the whole thing) instead of
waiting for the one I'd already launched. Each Firestore call took ~10-15s and the
harness auto-backgrounded it; by re-firing I created a pile-up of in-flight jobs,
several of which then "failed" on the wrapper (not the actual work), which looked
like more breakage and triggered MORE commands. A self-amplifying loop. The
underlying task was DONE the whole time — the thrash was 100% in the verification.

**How to apply (the rule):**
1. **The write is the work; the read-back is confirmation — and confirmation is
   ONE command.** After a successful write, run a single combined verification and
   STOP issuing commands.
2. **When a command auto-backgrounds, WAIT for its completion notification. Do not
   launch a second copy.** Re-firing never makes a slow call faster — it only
   creates a pile-up where wrapper-level failures masquerade as real failures.
   (Auto-background is the harness's choice for slow calls, not something to route
   around.)
3. **One in-flight verification at a time. Never have 2+ overlapping reads of the
   same state.** If output doesn't render, wait — don't spawn a variant.
4. **Don't `2>/dev/null` when a run is failing** — you go blind to the real error
   (compounded this; I couldn't see exit-1 causes). Drop the suppression the moment
   anything fails unexpectedly.
5. **Trust idempotent+transactional writes.** The migration was marker-guarded and
   per-doc transactional, so it could NOT double-apply — there was never a
   correctness reason to re-run anything. Re-read [[reference_v2_runtime_cogs]]-style
   verification once, calmly.
6. **Budget check:** if verification of a finished task is eating more than ~2
   minutes / a couple of commands, STOP — the task is done; the channel is the
   problem, and more commands make it worse.

**User observation worth heeding (S87):** on TWO separate occasions the user saw
that hitting **ESC** while a task had been "running" for a long time made it finish
**immediately**. Implication: a chunk of the apparent "long-running task" time was
NOT real compute — it was the agent stuck waiting on / re-polling a background
channel that had effectively already completed. ESC broke the wait and surfaced the
result instantly. Takeaway: if a task feels stuck for a long time, it is probably
ALREADY DONE and I'm the bottleneck (over-polling, waiting on a stale handle) — stop
spawning follow-ups; a single interrupt/clean re-check beats a pile-up. Don't make
the user hit ESC to rescue me from my own polling loop.

Related: [[feedback_verify_tool_output_before_chaining]] (don't chain on unconfirmed
output) — this is its sibling: don't *flail* on confirmation either.
