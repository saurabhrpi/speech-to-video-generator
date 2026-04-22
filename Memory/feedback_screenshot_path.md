---
name: Screenshot path is debug/
description: When the user says "screenshot" without attaching one, look in the debug/ folder (filenames vary by context)
type: feedback
---

When the user mentions a screenshot in conversation but no image is attached, read it from the `debug/` folder at the project root. Filenames vary by context (e.g., `Screenshot.png`, `screenshot.png`, or task-specific names like `firestore.png`). Other debug artifacts also live there (`logs.txt`, `output.json`, etc.).

**Why:** The user saves screenshots and other debug artifacts to that folder instead of attaching them inline.

**How to apply:** When the user references "the screenshot" / "this screenshot" / "the debug" / similar without an attachment, run `ls debug/` to find the relevant file (most-recent or context-named), then Read it. Don't ask for clarification before checking the folder.
