"""Build abacadaba favicon derivatives: an outlined "A+" mark (an A built
from strokes, a plus badge at its upper right), no background tile. Mirrors
favicon.svg's geometry - same viewBox, same strokes. The raster mark is
always drawn in the light-mode colour; favicon.svg additionally carries a
prefers-color-scheme: dark variant that these PNG/ICO outputs cannot, since
none of {ico, png} supports a media query.

Requires `pip install pillow`.
"""

import math
import pathlib

from PIL import Image, ImageDraw

MARK = (200, 67, 46, 255)  # --bead  #C8432E

OUT = pathlib.Path(__file__).resolve().parent / "out"

# Geometry in the 32-unit viewBox, matching favicon.svg exactly.
A_LEGS = [(2, 26), (11, 6), (20, 26)]
A_CROSSBAR = [(5.6, 18), (16.4, 18)]
PLUS_V = [(26, 6), (26, 14)]
PLUS_H = [(22, 10), (30, 10)]
A_STROKE = 3
PLUS_STROKE = 2.2

VIEWBOX = 32
CENTER = (VIEWBOX / 2, VIEWBOX / 2)

# Android/W3C maskable-icon safe zone: content must sit inside a circle
# whose diameter is 80% of the icon (radius 40%), since the OS may crop
# anything outside it under an arbitrary mask shape. The A+ mark isn't
# naturally that compact - its widest point (the A's lower-left leg) sits
# further from centre than that radius - so the maskable render scales the
# whole mark down and centres it, rather than assuming the artwork already
# clears it the way the old, narrower checkmark-and-plus happened to.
SAFE_ZONE_RADIUS = 0.4 * VIEWBOX
_stroked_points = [
    (A_LEGS, A_STROKE),
    (A_CROSSBAR, A_STROKE),
    (PLUS_V, PLUS_STROKE),
    (PLUS_H, PLUS_STROKE),
]
# Round caps/joins push visible ink up to half a stroke-width past the
# nominal point, so pad every point by its own half-width rather than
# measuring the bare polyline - that bare measurement is what the old
# "the inset carries over" assumption would have gotten wrong.
_farthest = max(
    math.hypot(x - CENTER[0], y - CENTER[1]) + width / 2
    for points, width in _stroked_points
    for x, y in points
)
MASKABLE_SCALE = SAFE_ZONE_RADIUS / _farthest


def _stroke(d: ImageDraw.ImageDraw, points, width: float, fill) -> None:
    """Round-capped, round-jointed polyline, to match the SVG's
    stroke-linecap/stroke-linejoin: round."""
    d.line(points, fill=fill, width=round(width), joint="curve")
    r = width / 2
    for x, y in points:
        d.ellipse([x - r, y - r, x + r, y + r], fill=fill)


def mark(px: int, mark_fill=MARK) -> Image.Image:
    S = px * 8
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    u = S / VIEWBOX

    _stroke(d, [(x * u, y * u) for x, y in A_LEGS], A_STROKE * u, mark_fill)
    _stroke(d, [(x * u, y * u) for x, y in A_CROSSBAR], A_STROKE * u, mark_fill)
    _stroke(d, [(x * u, y * u) for x, y in PLUS_V], PLUS_STROKE * u, mark_fill)
    _stroke(d, [(x * u, y * u) for x, y in PLUS_H], PLUS_STROKE * u, mark_fill)

    return img.resize((px, px), Image.LANCZOS)


def maskable_mark(px: int, mark_fill=MARK) -> Image.Image:
    """Same mark, scaled and centred to clear the maskable safe zone."""
    inset_px = round(px * MASKABLE_SCALE)
    inset = mark(inset_px, mark_fill)
    canvas = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    offset = (px - inset_px) // 2
    canvas.paste(inset, (offset, offset), inset)
    return canvas


OUT.mkdir(exist_ok=True)
for n in (16, 32, 48, 180, 192, 512):
    mark(n).save(OUT / f"icon-{n}.png")
mark(180).save(OUT / "apple-touch-icon.png")
maskable_mark(512).save(OUT / "icon-maskable-512.png")
mark(48).save(OUT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
print("built", sorted(p.name for p in OUT.iterdir()))
print(f"maskable safe-zone scale: {MASKABLE_SCALE:.4f} (farthest point at {_farthest:.2f} of {SAFE_ZONE_RADIUS} radius)")
