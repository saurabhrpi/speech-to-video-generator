---
name: reference_macos_screenshot_filename_nbsp
description: macOS screenshot filenames use a narrow no-break space (U+202F) before AM/PM, not a regular space — hardcoding the name with a normal space fails to match the file
metadata:
  type: reference
---

macOS screenshot filenames look like `Screenshot 2026-05-31 at 12.56.51 PM.png`, but the space **before "PM"/"AM" is a narrow no-break space (U+202F)**, NOT a regular ASCII space. (This is a locale/time-format detail in recent macOS.)

**Symptom:** when you hardcode the filename in code with a normal space, `os.path.isfile()` / `open()` / a quoted shell path **silently misses the file** even though it visibly exists and the Read tool opens it fine. S88: a Python script bailed with "NOT FOUND" on a path the Read tool had just displayed.

**Fix — never hardcode the filename. Match by a stable substring:**
- Python: `glob.glob(os.path.join(dir, "*12.56.51*.png"))` or filter `os.listdir(dir)` by the timestamp substring (reads the real on-disk bytes).
- Shell: glob with `*` straddling the gap — `"*12.56.51*PM.png"` — so the space char doesn't matter.

The earlier batch step worked precisely because it used `os.listdir()` (real bytes); the failure only appeared when a single new file was referenced by a typed-out name. Relevant because submission/screenshot-prep sessions process many macOS screenshots by name.

Sibling: [[reference_app_store_screenshot_cleanup.md]] (the alpha-strip + exact-resolution recipe these screenshots also need).
