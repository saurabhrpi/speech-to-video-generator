---
name: Index files need hand-merge — never blindly `--ours` or `--theirs`
description: For index/manifest files (MEMORY.md, route registries, __all__ lists, README TOCs) where each side of a conflict adds DIFFERENT entries, both `git checkout --ours` and `--theirs` silently drop the other side's additions. Always hand-merge; check for orphaned referents.
type: feedback
---

When resolving a conflict on an **index/manifest file** (one whose job is to enumerate other files or entities — `MEMORY.md`, README tables-of-contents, package exports, route registries, `__all__` lists), `git checkout --ours <file>` and `git checkout --theirs <file>` are almost never the right move. Both sides usually contain *additive entries* — different new bullets, different new exports — and picking one side silently discards the other. Always open the file, look at the conflict markers, and merge by hand: if both sides added entries, keep both.

**Why:** S58 — during the `git stash pop` after the hotfix-build14→main merge, `Memory/MEMORY.md` had a conflict where HEAD (post-merge) had hotfix-build14's 5 S54 memory bullets added and the stash had 6 S57 memory bullets added. I ran `git checkout --ours Memory/MEMORY.md` reasoning that HEAD's S54 content was more comprehensive. The 6 S57 memory **files** themselves survived (they were untracked, so the checkout didn't touch them) — but their index entries in `MEMORY.md` were silently dropped. The orphan state went undetected for ~3 hours of work; only caught when adding a single S58 bullet revealed the predecessor bullets were missing.

**How to apply:**
- For index files in a merge/rebase/stash-pop conflict: **always read the conflict markers and hand-merge.** Do not run `--ours`/`--theirs` as a shortcut.
- Quick test for "is this an index file?": does the file consist mostly of references (paths, names, identifiers) to OTHER artifacts? If yes, treat it as an index. Examples: `Memory/MEMORY.md`, `mobile/app/_layout.tsx` route registration, `src/.../__init__.py` re-exports, `package.json` dependency list, route maps, `CHANGELOG.md`.
- After resolving an index-file conflict, do a quick orphan check: look at the working tree for any new/untracked files (or recently-added tracked files) the index would normally reference. If those exist but lack index entries, you just orphaned them — fix the index before the conflict is forgotten.
- Cross-reference: `feedback_save_memory_only_after_verification.md` (don't memorialize fixes you haven't proven) and the convention that `MEMORY.md` is the discovery surface for memory files — a memory file without an index bullet is invisible to future sessions.
