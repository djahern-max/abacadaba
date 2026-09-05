"""Run with: cd backend && source .venv/bin/activate && python -m pytest ../tools/brand/

Not wired into `cd backend && pytest` (backend/CLAUDE.md's test command) since
this checks tools/brand/, not the app - it's a standalone script with its own
test, run by hand like check_palette.py itself is.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_palette  # noqa: E402


def test_palette_agrees_as_shipped():
    assert check_palette.check() == []


def test_fails_on_mismatched_mark(monkeypatch):
    real_parse_mark = check_palette._parse_mark
    monkeypatch.setattr(check_palette, "_parse_mark", lambda text: (1, 2, 3))
    try:
        problems = check_palette.check()
    finally:
        check_palette._parse_mark = real_parse_mark
    assert any("MARK" in p for p in problems)


def test_fails_on_below_floor_accent(monkeypatch):
    real_parse_accent = check_palette._parse_accent
    monkeypatch.setattr(check_palette, "_parse_accent", lambda text: {**real_parse_accent(text), "d": (60, 60, 60)})
    problems = check_palette.check()
    assert any("ACCENT['d']" in p and "below the 4.5:1 floor" in p for p in problems)


def test_fails_on_missing_accent_key(monkeypatch):
    real_parse_accent = check_palette._parse_accent
    monkeypatch.setattr(
        check_palette,
        "_parse_accent",
        lambda text: {k: v for k, v in real_parse_accent(text).items() if k != "d"},
    )
    problems = check_palette.check()
    assert any("exactly keys b, c, d" in p for p in problems)
