---
name: Same code, different speed → environment first
description: When identical code is fast on one host and slow on another, inspect environment differences (fs transport, RAM, CPU throttling) before theorizing about code or library internals
type: feedback
---

When diagnosing a "same code, different speed across machines" bug, investigate environment differences FIRST — `mount` output, `/tmp` backing, `free -h`, CPU quota, `/dev/shm` availability — before theorizing about the code or library internals. This is narrower than and complementary to `feedback_analysis_depth.md` (which warns against blaming infra as a lazy default). That rule still holds; the refinement is: when the code is provably identical across hosts, the environment IS the variable, so start there.

**Why:** On the Replit stitching investigation, I spent multiple turns theorizing that moviepy's compose-mode was doing per-frame seeks and proposing a raw-ffmpeg rewrite. The moviepy theory was disproven the moment I read its actual source (forward access uses `skip_frames`, no reinit). The real cause was `/tmp` being on a network block device — discoverable in ONE shell command (`mount | grep /tmp`). The fix was a one-line `tempfile.mkdtemp(dir="/dev/shm")` override. ~150× speedup, zero code rewrite. I also ignored the `debug/` folder entirely until the user explicitly pointed me there — it had per-frame wall-clock progress that pinpointed the slowness exactly. All of this was sitting there before I opened my mouth.

**How to apply:**

1. If a `debug/`, `logs/`, or similar directory is mentioned or visible, read it FULLY and FIRST — before forming any hypothesis. The user leaves logs for a reason.

2. For "slow on prod, fast locally" bugs, the first diagnostic questions are environmental:
   - What's `/tmp` backed by on the slow host? (`mount | grep /tmp`)
   - Is `/dev/shm` available? How big? (`df -h /dev/shm`)
   - Is RAM/CPU throttled? (`free -h`, cgroup limits)
   - Only then: is the code doing something weird?

3. When claiming a library does X internally, **read the library's source** from the project's venv to verify. Don't pattern-match on names from docs, blog posts, or CLAUDE.md descriptions. I twice theorized about moviepy compose-mode internals; when I finally read the source, I was wrong.

4. Never promise a speedup multiplier ("30–90 seconds", "sub-minute") without grounding in a measurement. Commit to ranges only when measured; otherwise say "probably much better, need to measure" and propose the measurement.

5. If the user is running the slow environment and you aren't, you CANNOT verify environmental claims from your end. Ask them to run the specific shell commands — don't pretend to "verify" by guessing or Googling docs.
