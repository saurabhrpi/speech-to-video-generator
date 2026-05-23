---
name: template-preview-crf
description: When temporal-trimming a Kling preview video output before R2 upload, use `-crf 15` or lower (not 18). Visual difference imperceptible on iPhone today, but lower CRF leaves more quality headroom for catalog parity with native Kling 17-30 Mbps outputs.
metadata:
  type: feedback
---

**Rule:** Re-encoding ffmpeg trims of Kling preview outputs (the `-ss 0 -t N` step before upload to R2) should use `-crf 15` or lower for libx264 — not 18.

**Why:**
- S73 Thriller redo + No Batidão launches used `-crf 18` → ~9 Mbps and ~6.9 Mbps at 1440×1440. User checked on iPhone and saw no visible difference vs the native Kling outputs (17-30 Mbps), so crf-18 is safe for today's hardware.
- But the bitrate gap is real — catalog templates that didn't need a trim (Smooth Criminal, Bad, Beat It, Baby Dance, Gangsta, Bombale) shipped at native ~20-30 Mbps. Lower CRF narrows that gap, giving more quality cushion if Apple ever bumps up the home-tile rendering scale or users move to bigger screens.
- crf 15 ≈ "transparent" quality on libx264; lower values give larger files but more headroom; still well under native Kling rates.

**How to apply:**
- Every future template preview trim before upload — `-c:v libx264 -preset medium -crf 15 -c:a aac -b:a 128k` (or lower CRF if file size isn't a concern).
- Don't bother re-doing the S73 Thriller/No Batidão previews; user confirmed they look fine on iPhone — sunk cost, leave them.
- Doesn't apply to runtime user gens; those go through std-mode Kling and don't get a trim step.

See related: [[kling-mode-split]], [[regen-vs-preserve-prompts]].
