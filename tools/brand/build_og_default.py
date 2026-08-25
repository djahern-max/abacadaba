"""Build the site-default Open Graph card, 1200x630.

Requires `pip install pillow fonttools`. Downloads the full-latin Jost
variable font Google Fonts serves (same source as build_jost_subset.py) so
the card uses the same face as the header wordmark without depending on any
font installed on the machine running this script.
"""

import io
import urllib.request

from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

INK    = (12, 34, 51)      # --ink   #0C2233
PAPER  = (242, 245, 247)   # --wash  #F2F5F7
ACCENT = (167, 139, 250)   # --color-accent (dark-mode value #a78bfa - reads
                            # against the ink background here)
W, H = 1200, 630

JOST_LATIN_URL = "https://fonts.gstatic.com/s/jost/v20/92zatBhPNqw73oTd4jQmfxI.woff2"


def _load_jost(size: int, weight: int = 500) -> ImageFont.FreeTypeFont:
    raw = urllib.request.urlopen(JOST_LATIN_URL).read()
    font = TTFont(io.BytesIO(raw))
    if "fvar" in font:
        from fontTools.varLib.instancer import instantiateVariableFont

        font = instantiateVariableFont(font, {"wght": weight})
    font.flavor = None
    buf = io.BytesIO()
    font.save(buf)
    buf.seek(0)
    return ImageFont.truetype(buf, size)


img = Image.new("RGB", (W, H), INK)
d = ImageDraw.Draw(img)

d.line([(0, H - 96), (W, H - 96)], fill=(26, 52, 74), width=2)

word = "abacadaba"
f = _load_jost(160, weight=600)
x = 96
y = (H - 160) / 2 - 20
for ch in word:
    d.text((x, y), ch, font=f, fill=PAPER if ch == "a" else ACCENT)
    x += f.getlength(ch) - 3

footer_font = _load_jost(26, weight=500)
d.text((96, H - 70), "abacadaba.com", font=footer_font, fill=(90, 116, 135))

img.save("out/og-default.png", optimize=True)
print(img.size)
