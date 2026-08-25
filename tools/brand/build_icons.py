"""Build abacadaba favicon derivatives: a single lowercase `a` (Jost) on a
rounded tile. Mirrors favicon.svg's geometry - same font, same tile radius.

Requires `pip install pillow fonttools`.
"""

import io
import pathlib

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

INK    = (12, 34, 51, 255)    # --ink   #0C2233
LETTER = (167, 139, 250, 255) # --color-accent (dark-mode value #a78bfa -
                               # chosen for the raster icons because it's
                               # the one that reads against the ink tile;
                               # PNGs can't do the SVG's prefers-color-scheme
                               # swap, so one fixed combo has to work alone.

JOST_SUBSET = pathlib.Path(__file__).resolve().parent.parent.parent / "frontend" / "public" / "fonts" / "jost-abcd.woff2"


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    font = TTFont(str(JOST_SUBSET))
    font.flavor = None
    buf = io.BytesIO()
    font.save(buf)
    buf.seek(0)
    return ImageFont.truetype(buf, size)


def mark(px: int, tile_fill=INK, letter_fill=LETTER) -> Image.Image:
    S = px * 8
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    u = S / 32.0
    d.rounded_rectangle([0, 0, S, S], radius=7.5 * u, fill=tile_fill)

    font = _load_font(int(20 * u))
    bbox = d.textbbox((0, 0), "a", font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (S - w) / 2 - bbox[0]
    y = (S - h) / 2 - bbox[1]
    d.text((x, y), "a", font=font, fill=letter_fill)
    return img.resize((px, px), Image.LANCZOS)


for n in (16, 32, 48, 180, 192, 512):
    mark(n).save(f"out/icon-{n}.png")
mark(180).save("out/apple-touch-icon.png")
mark(512).save("out/icon-maskable-512.png")
mark(48).save("out/favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
print("built", sorted(__import__("os").listdir("out")))
