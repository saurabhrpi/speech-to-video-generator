---
name: feedback_zsh_not_bash
description: Shell is zsh, not bash — bash builtins like shopt silently fail; case/glob matching stays case-sensitive
metadata:
  type: feedback
---

This machine's shell is **zsh**, not bash. Bash-only builtins (notably `shopt`) are unavailable: `shopt -s nocasematch` errors with `command not found` and the surrounding `case`/glob match stays **case-sensitive** — a SILENT failure that lets unintended files slip past a filter.

**Why:** S81 — during the `App Templates Prep/Done` cleanup I wrote `shopt -s nocasematch` then `case "$b" in river*|pinky*|madhvi*) continue` to skip decision-bucket files case-insensitively. `shopt` no-op'd, so capitalized names (`Pinky_Up.mp4`, `Madhvi_selfile.JPG`, `River_start_at_1_sec.mov`) dodged the lowercase-only patterns and got swept into Trash with the safe bulk. Caught before any permanent deletion, but it should never have happened — I knew the env said `Shell: zsh`.

**How to apply:**
- For case-insensitive matching in zsh, lowercase the variable first (`b=${b:l}` or `tr 'A-Z' 'a-z'`) and match lowercase patterns, OR write patterns that cover both cases — never reach for `shopt`. Before using any shell builtin in a one-off, confirm it's zsh-compatible.
- zsh globs are case-sensitive by default (CASE_GLOB on); `river_*` matches only lowercase. This is reliable to exploit (it's what made the final guarded delete safe), but it cuts both ways.
- For destructive file ops (rm / mv-to-Trash / bulk moves), do a **dry-run echo pass first** that prints exactly what WOULD be moved/deleted, eyeball it, then execute. A filter bug is invisible until you diff intended-vs-actual. See [[feedback_expo_run_ios]] for the broader "verify the env before acting" pattern.
