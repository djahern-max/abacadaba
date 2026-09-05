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

# Dark-surface variants of global.css's --bead-b/-c/-d (feature 030a's header
# palette). Those tokens are held to 4.5:1 against --wash, the light header
# background - against this card's dark INK tile they drop to 3.10/2.97/3.24,
# so this card needs its own values raised in HLS lightness (same hue) until
# each clears 4.5:1 against INK. Keyed by letter, not position - see
# Wordmark.jsx/current-feature.md (030a) - so both b's in "abacadaba" share
# one value.
#
# 'b' deliberately reuses favicon.svg's dark-mode stroke (#DE6C52) rather
# than a freshly-raised value close to it (~#D76452, which only clears
# 4.51:1) - one fewer near-duplicate hardcoded colour, and better margin
# (4.93:1 vs 4.51:1). 'c' and 'd' have no other consumer to reuse, so they're
# new values. See tools/brand/check_palette.py, which checks ACCENT["b"]
# against favicon.svg so the two can't drift apart silently, and current-
# feature.md (030b) for the measured numbers this comment states.
ACCENT = {
    "b": (222, 108, 82),   # #DE6C52 - 4.93:1 on INK
    "c": (20, 154, 144),   # #149A90 - 4.69:1 on INK
    "d": (219, 101, 11),   # #DB650B - 4.55:1 on INK
}
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
    d.text((x, y), ch, font=f, fill=PAPER if ch == "a" else ACCENT[ch])
    x += f.getlength(ch) - 3

footer_font = _load_jost(26, weight=500)
d.text((96, H - 70), "abacadaba.com", font=footer_font, fill=(90, 116, 135))

img.save("out/og-default.png", optimize=True)
print(img.size)
