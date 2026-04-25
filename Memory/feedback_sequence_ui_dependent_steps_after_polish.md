---
name: Sequence UI-dependent submission steps AFTER UI polish
description: When walking through App Store / metadata submission steps, proactively identify sub-steps that depend on the final UI (screenshots, UI-referencing copy, demo notes) and defer them until after polish. Surface the dependency at the START, not after the user catches it.
type: feedback
---

When the launch checklist has both UI polish and metadata submission as parallel work streams, sub-steps within metadata that depend on the final UI must happen AFTER polish:

- App Store **screenshots** — must show the polished UI users will actually see
- App Store **app preview videos** — same dependency as screenshots
- Marketing copy that references **specific UI elements** (button labels, screen names, model picker names) — must match shipping UI
- App Review **demo flow notes** — must match the actual UX

**Why:** ASC locks screenshots and metadata into a submission cycle once "Add for Review" is clicked. Updating screenshots mid-review or post-rejection costs another 1-3 day review loop. Pre-capturing burns time AND risks reviewer flagging inconsistency between marketing screenshots and actual UI.

**How to apply:**
- At the START of any submission walkthrough, scan the remaining checklist for UI-dependent sub-steps and explicitly defer them — *before* walking the user into them.
- For App Store metadata, the correct sequence is: text-only metadata first (description, keywords, pricing, privacy, age rating, support URL, copyright, app review notes) → UI polish pass → screenshots + app preview → final review submit.
- Don't wait for the user to point out the dependency. Even when they say "let's do step X," check whether step X has a downstream blocker first and surface it.

**S52 burn:** Started walking the user through capturing App Store marketing screenshots for Red #5 while Red #4 (UI polish, including "remove '· N credits' suffix" + a broader audit) was still pending. User caught it: *"You should have been alert/aware of the fact that adding screenshots now means locking the UI when we still have Polish UI step left."*
