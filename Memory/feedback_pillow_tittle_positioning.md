---
name: pillow-tittle-positioning
description: For precise icon/logo layout, draw primitives from scratch — don't render glyphs and try to retrofit decorations on them.
metadata:
  type: feedback
---

If you need to place a dot/mark/decoration **precisely on top of a specific glyph feature** (e.g. an i-tittle), don't render the text with `draw.text()` and then try to compute where the feature is. Pillow's font metrics + draw conventions don't give you reliable enough positioning. Approaches that all failed S67 when trying to recolor an i-tittle to red:

1. `textbbox((0, 0), text)` + offset math → way off, dot floated above text.
2. `textbbox((x, y), text)` (canvas coords) + `top_of_text + dot_r` → dot center landed below tittle.
3. `f.getlength("a")` to find i-column + pixel-scan for opaque pixels in that column → recoloring missed parts of the white tittle, looked dual-dot.

The dot stayed visibly misaligned across three iterations.

**Why:** Pillow's text rendering hides the relationship between the requested draw coordinate and the actual ink. The ink-bbox top isn't necessarily the i-tittle top; the i-tittle isn't necessarily at the bbox top; lowercase tittles vary in shape and weight across fonts.

**How to apply:**
- For precise composition (icons, logos), **either** render shapes entirely with PIL primitives (`draw.ellipse`, `draw.polygon`) so you control every pixel position, **or** redraw the glyph from scratch (e.g. `draw.line` for an i-stem + `draw.ellipse` for the tittle).
- If you DO render text-as-text, accept that decorations sitting next to it will be approximate, not pixel-aligned.
- For the AIVO icon, we ended up at a minimalist Bodoni "a" with a separate `draw.ellipse` dot ABOVE the letter (not over a specific feature) — clean separation, no positioning math required.
