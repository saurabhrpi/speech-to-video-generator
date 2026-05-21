---
name: App Store marketing screenshot prep — alpha strip + resample
description: ASC rejects PNG screenshots with alpha channels (even when alpha=255 everywhere) and won't accept screenshots whose native resolution doesn't match the target display-class slot. Two-step prep recipe.
type: reference
---

iOS screenshots saved by the system (`xcrun simctl io booted screenshot`, or hardware Vol-Up + Side on a real device) come out as PNG **RGBA**, even when the visible content is fully opaque. ASC rejects with `"Images can't contain alpha channels or transparencies."` Discovered S69 uploading the v2.0.0 paywall screenshot.

**Strip the alpha channel** (PIL, lossless when all alpha = 255 — the iOS case):

```bash
python3 -c "
from PIL import Image
img = Image.open('path/to/shot.png').convert('RGB')
img.save('path/to/shot.png', 'PNG')
"
```

`sips` alone cannot strip alpha on PNG — `-s format png` is a no-op when the input is already PNG. Use PIL (always present on macOS Python3), or accept a JPEG round-trip via `sips -s format jpeg` (lossy on crisp UI text).

**Match the ASC display-class slot resolution.** The 6.9" required slot accepts only 1320×2868 (iPhone 17 Pro Max) or 1290×2796 (iPhone 16 Pro Max, 15 Pro Max). A capture from iPhone 13 Pro Max (1284×2778, 6.7" class) is rejected from the 6.9" slot. Resample with sips:

```bash
sips -z 2868 1320 in.png --out out.png
```

(`-z H W`, height first.) The 6.7"→6.9" upscale is 2.8% wide / 3.2% tall — imperceptible at App Store preview sizes. Slight aspect-ratio shift (0.4622 → 0.4614) is below detection threshold.

**Apply both steps to any real-device capture before uploading.** Sim captures from a 6.9" device sim (default project UDID per `reference_simulator_udid.md`) are already the right size; only the alpha-strip step is needed.

Companion: `reference_asc_iap_screenshots.md` (about IAP review screenshots specifically — different slot, different rules, but same alpha-strip step applies).
