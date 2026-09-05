"""Verify the brand palette agrees across the four places it's written down:

    frontend/src/styles/global.css   --bead-b/-c/-d (CSS custom properties)
    frontend/public/favicon.svg      light + dark stroke colours
    tools/brand/build_icons.py       MARK
    tools/brand/build_og_default.py  INK, ACCENT

Nothing enforces this automatically - each file hardcodes its own copy in its
own language, kept in step so far by a docstring promise and human attention
(see current-feature.md, 030b, "The actual problem underneath"). This script
is that check, run by hand:

    python tools/brand/check_palette.py

Exits 1 and prints every problem found if any of the following don't hold:

  - favicon.svg's light-mode stroke == build_icons.py's MARK
    (both are "the favicon mark's colour"; a mismatch means the SVG and the
    raster icons it's supposed to mirror have drifted apart)
  - favicon.svg's dark-mode stroke == build_og_default.py's ACCENT["b"]
    (030b's deliberate choice - see build_og_default.py's comment - rather
    than a fresh, nearly-identical value)
  - build_og_default.py's ACCENT has exactly the keys b/c/d, keyed by
    letter, and every value clears 4.5:1 against build_og_default.py's own
    INK tile
  - global.css's --bead-b/-c/-d each still clear 4.5:1 against --wash, the
    header background they're held to (030a's floor, guarded against
    regressing silently)

Deliberately not checked: --bead-b/-c/-d against ACCENT's values. They're
supposed to differ - one is a light-surface palette, the other a
dark-surface variant raised in lightness for a dark tile - so equality
there would be the bug, not the fix.
"""

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GLOBAL_CSS = REPO_ROOT / "frontend/src/styles/global.css"
FAVICON_SVG = REPO_ROOT / "frontend/public/favicon.svg"
BUILD_ICONS = REPO_ROOT / "tools/brand/build_icons.py"
BUILD_OG = REPO_ROOT / "tools/brand/build_og_default.py"

CONTRAST_FLOOR = 4.5


def _srgb_to_linear(c: float) -> float:
    c /= 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def _relative_luminance(rgb: tuple[int, int, int]) -> float:
    r, g, b = rgb
    return 0.2126 * _srgb_to_linear(r) + 0.7152 * _srgb_to_linear(g) + 0.0722 * _srgb_to_linear(b)


def contrast_ratio(rgb_a: tuple[int, int, int], rgb_b: tuple[int, int, int]) -> float:
    l1, l2 = sorted((_relative_luminance(rgb_a), _relative_luminance(rgb_b)), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def _parse_global_css(text: str) -> dict[str, str]:
    return {m.group(1): m.group(2).upper() for m in re.finditer(r"--bead-([bcd]):\s*(#[0-9A-Fa-f]{6})", text)}


def _parse_favicon_svg(text: str) -> tuple[str, str]:
    media_split = re.split(r"@media\s*\(prefers-color-scheme:\s*dark\)", text)
    if len(media_split) != 2:
        raise ValueError("favicon.svg: expected exactly one prefers-color-scheme: dark block")
    light_matches = re.findall(r"stroke:\s*(#[0-9A-Fa-f]{6})", media_split[0])
    dark_matches = re.findall(r"stroke:\s*(#[0-9A-Fa-f]{6})", media_split[1])
    if len(light_matches) != 1 or len(dark_matches) != 1:
        raise ValueError("favicon.svg: expected exactly one stroke colour outside and one inside the dark block")
    return light_matches[0].upper(), dark_matches[0].upper()


def _parse_mark(text: str) -> tuple[int, int, int]:
    m = re.search(r"MARK\s*=\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", text)
    if not m:
        raise ValueError("build_icons.py: could not find MARK = (r, g, b, ...)")
    return tuple(int(g) for g in m.groups())


def _parse_ink(text: str) -> tuple[int, int, int]:
    m = re.search(r"INK\s*=\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)", text)
    if not m:
        raise ValueError("build_og_default.py: could not find INK = (r, g, b)")
    return tuple(int(g) for g in m.groups())


def _parse_accent(text: str) -> dict[str, tuple[int, int, int]]:
    m = re.search(r"ACCENT\s*=\s*\{(.*?)\}", text, re.DOTALL)
    if not m:
        raise ValueError("build_og_default.py: could not find ACCENT = { ... }")
    entries = re.findall(r'"([bcd])"\s*:\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', m.group(1))
    return {letter: (int(r), int(g), int(b)) for letter, r, g, b in entries}


def check() -> list[str]:
    problems: list[str] = []

    global_css = _parse_global_css(GLOBAL_CSS.read_text())
    favicon_light, favicon_dark = _parse_favicon_svg(FAVICON_SVG.read_text())
    mark = _parse_mark(BUILD_ICONS.read_text())
    ink = _parse_ink(BUILD_OG.read_text())
    accent = _parse_accent(BUILD_OG.read_text())

    mark_hex = rgb_to_hex(mark)
    if favicon_light != mark_hex:
        problems.append(
            f"favicon.svg light-mode stroke ({favicon_light}) != build_icons.py MARK ({mark_hex})"
        )

    if set(accent) != {"b", "c", "d"}:
        problems.append(f"build_og_default.py ACCENT must have exactly keys b, c, d - found {sorted(accent)}")
        return problems  # further checks assume all three keys exist

    accent_b_hex = rgb_to_hex(accent["b"])
    if favicon_dark != accent_b_hex:
        problems.append(
            f"favicon.svg dark-mode stroke ({favicon_dark}) != build_og_default.py ACCENT['b'] ({accent_b_hex})"
        )

    for letter, rgb in accent.items():
        ratio = contrast_ratio(rgb, ink)
        if ratio < CONTRAST_FLOOR:
            problems.append(
                f"build_og_default.py ACCENT['{letter}'] ({rgb_to_hex(rgb)}) measures {ratio:.2f}:1 "
                f"against INK ({rgb_to_hex(ink)}), below the {CONTRAST_FLOOR}:1 floor"
            )

    wash = (0xF2, 0xF5, 0xF7)
    for letter in ("b", "c", "d"):
        hex_value = global_css.get(letter)
        if hex_value is None:
            problems.append(f"global.css: --bead-{letter} not found")
            continue
        ratio = contrast_ratio(hex_to_rgb(hex_value), wash)
        if ratio < CONTRAST_FLOOR:
            problems.append(
                f"global.css --bead-{letter} ({hex_value}) measures {ratio:.2f}:1 against --wash ({rgb_to_hex(wash)}), "
                f"below the {CONTRAST_FLOOR}:1 floor"
            )

    return problems


def main() -> int:
    problems = check()
    if not problems:
        print("brand palette OK: all files agree, all values clear 4.5:1 on their own surface")
        return 0
    print(f"brand palette check FAILED ({len(problems)} problem{'s' if len(problems) != 1 else ''}):")
    for problem in problems:
        print(f"  - {problem}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
