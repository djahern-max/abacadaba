"""Build abacadaba favicon derivatives: a checkmark with a small plus badge
on a rounded tile. Mirrors favicon.svg's geometry - same viewBox, same
strokes, same tile radius.

Requires `pip install pillow`.
"""

import pathlib

from PIL import Image, ImageDraw

TILE = (12, 34, 51, 255)   # --ink   #0C2233
MARK = (200, 135, 27, 255) # --bead  #C8871B

OUT = pathlib.Path(__file__).resolve().parent / "out"


def _stroke(d: ImageDraw.ImageDraw, points, width: float, fill) -> None:
    """Round-capped, round-jointed polyline, to match the SVG's
    stroke-linecap/stroke-linejoin: round."""
    d.line(points, fill=fill, width=round(width), joint="curve")
    r = width / 2
    for x, y in points:
        d.ellipse([x - r, y - r, x + r, y + r], fill=fill)


def mark(px: int, tile_fill=TILE, mark_fill=MARK) -> Image.Image:
    S = px * 8
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    u = S / 32.0
    d.rounded_rectangle([0, 0, S, S], radius=7.5 * u, fill=tile_fill)

    check = [(8 * u, 17.5 * u), (13.5 * u, 23 * u), (24.5 * u, 9.5 * u)]
    _stroke(d, check, 3 * u, mark_fill)

    plus_v = [(10 * u, 7.5 * u), (10 * u, 12.5 * u)]
    plus_h = [(7.5 * u, 10 * u), (12.5 * u, 10 * u)]
    _stroke(d, plus_v, 2.2 * u, mark_fill)
    _stroke(d, plus_h, 2.2 * u, mark_fill)

    return img.resize((px, px), Image.LANCZOS)


OUT.mkdir(exist_ok=True)
for n in (16, 32, 48, 180, 192, 512):
    mark(n).save(OUT / f"icon-{n}.png")
mark(180).save(OUT / "apple-touch-icon.png")
mark(512).save(OUT / "icon-maskable-512.png")
mark(48).save(OUT / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
print("built", sorted(p.name for p in OUT.iterdir()))
