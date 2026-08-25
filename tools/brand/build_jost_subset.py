"""Rebuild the header's Jost subset: glyphs a/b/c/d only, ~2KB, one file.

Requires `pip install fonttools brotli`.

    python tools/brand/build_jost_subset.py

Downloads the variable Jost latin file Google Fonts serves for weights
500/700 (both weights already point at the same variable file - that's how
Google Fonts serves a variable font's named instances), subsets it to the
four glyphs the wordmark uses, and keeps fvar/gvar so both font-weight: 500
and font-weight: 700 still resolve correctly from the one file. Keeps the
OFL copyright and license-URL name records - the subset is still a
redistribution of Jost and the license requires them.

Output: frontend/public/fonts/jost-abcd.woff2
"""

import pathlib
import urllib.request

from fontTools.subset import Subsetter, Options
from fontTools.ttLib import TTFont

JOST_LATIN_URL = "https://fonts.gstatic.com/s/jost/v20/92zatBhPNqw73oTd4jQmfxI.woff2"
OUT = pathlib.Path(__file__).resolve().parent.parent.parent / "frontend" / "public" / "fonts" / "jost-abcd.woff2"

RAW = pathlib.Path("/tmp/jost-latin.woff2")
urllib.request.urlretrieve(JOST_LATIN_URL, RAW)

font = TTFont(RAW)
options = Options()
options.flavor = "woff2"
options.layout_features = []
options.hinting = False
options.desubroutinize = True
options.name_IDs = [0, 1, 2, 3, 4, 6, 13, 14]  # keep copyright + OFL URL
options.name_legacy = True
options.drop_tables += ["DSIG"]

subsetter = Subsetter(options)
subsetter.populate(text="abcd")
subsetter.subset(font)

OUT.parent.mkdir(parents=True, exist_ok=True)
font.save(OUT)
print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")
