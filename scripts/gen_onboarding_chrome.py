"""Draw the onboarding chrome PNGs (no native deps): a curved 'before -> after'
arrow and a smooth bottom fade gradient. Bundled under mobile/assets/onboarding/.

Avoids react-native-svg / expo-linear-gradient so the screen works in the
current dev client (JS + bundled assets only, no prebuild).
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "mobile" / "assets" / "onboarding"
OUT.mkdir(parents=True, exist_ok=True)

# --- bottom fade: transparent (top) -> ~90% black (bottom) ---
W, H = 16, 1200
fade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
px = fade.load()
for y in range(H):
    a = int((y / (H - 1)) ** 1.45 * 235)
    for x in range(W):
        px[x, y] = (0, 0, 0, a)
fade.save(OUT / "bottom_fade.png")
print("wrote bottom_fade.png", fade.size)

# --- curved arrow (white with a soft dark halo for contrast on any video) ---
S = 280
arr = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(arr)
P0, P1, P2 = (70, 28), (20, 165), (168, 232)


def bez(t: float):
    x = (1 - t) ** 2 * P0[0] + 2 * (1 - t) * t * P1[0] + t ** 2 * P2[0]
    y = (1 - t) ** 2 * P0[1] + 2 * (1 - t) * t * P1[1] + t ** 2 * P2[1]
    return (x, y)


pts = [bez(i / 48) for i in range(49)]
d.line(pts, fill=(0, 0, 0, 90), width=20, joint="curve")     # halo
d.line(pts, fill=(255, 255, 255, 240), width=12, joint="curve")
# arrowhead at P2, oriented along the final tangent
pen = bez(0.95)
ang = math.atan2(P2[1] - pen[1], P2[0] - pen[0])
L, spread = 40, 0.55
tip = P2
a_l = (tip[0] - L * math.cos(ang - spread), tip[1] - L * math.sin(ang - spread))
a_r = (tip[0] - L * math.cos(ang + spread), tip[1] - L * math.sin(ang + spread))
d.polygon([tip, a_l, a_r], fill=(0, 0, 0, 90))               # halo
inset = 4
tip2 = (tip[0] - inset * math.cos(ang), tip[1] - inset * math.sin(ang))
a_l2 = (tip2[0] - (L - 7) * math.cos(ang - spread), tip2[1] - (L - 7) * math.sin(ang - spread))
a_r2 = (tip2[0] - (L - 7) * math.cos(ang + spread), tip2[1] - (L - 7) * math.sin(ang + spread))
d.polygon([tip2, a_l2, a_r2], fill=(255, 255, 255, 240))
arr.save(OUT / "arrow.png")
print("wrote arrow.png", arr.size)
