---
name: reference_asc_age_rating_edit_needs_version
description: In ASC's 2026 age-rating system the questionnaire's Edit button only appears once an app version is in progress; App Information alone shows read-only View/View Details
metadata:
  type: reference
---

In the post-2025 App Store Connect age-rating system, the age-rating **questionnaire is only editable when there is an app version in an editable state** (a version created / "Prepare for Submission").

On the **App Information** page with NO in-progress version, the Age Ratings section shows only:
- **"View"** — a read-only walkthrough of the current answers (radios look greyed, pageable via Next), and
- **"View Details"** — the per-region rating summary.

**Neither exposes an Edit affordance.** This is not a permissions/role problem and not a bug — there is simply nothing editable until a version exists.

**To edit the age rating:** first **create the new app version** (the version you're about to submit — e.g. `2.0.1`) under the iOS app. Once a version exists, an **"Edit"** link appears next to **Age Ratings**, opening the editable 7-step questionnaire (Step 1 "Features" → content categories → … → 7).

**How to apply:** when someone needs to change the age rating and only sees View / View Details, tell them **up front to create the target app version first** — don't send them clicking around for an Edit button that can't exist yet. (S88: cost the user two dead-end click-throughs because I didn't surface this dependency.)

Sibling: [[feedback_sequence_ui_dependent_steps_after_polish]] — ASC submission steps have ordering dependencies; surface the dependency at the START of the step, not after the user hits the wall.
