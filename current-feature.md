# Current Feature

## Feature 030a, The mark and the wordmark palette

## Numbering note
A letter suffix means corrective work against the base feature's surface area.
Both changes here are entirely inside what 030 shipped — the favicon set and the
`Wordmark` component — so this is `030a`, not `032`. If you would rather treat
the palette as new capability and take a fresh number, say so in the changelog
entry; do not leave it ambiguous.

**This waits for 031.** `current-feature.md` holds one feature at a time. Ship
the catalog ordering, write its CHANGELOG entry, then overwrite this file in.

## Before anything else: the CHANGELOG no longer describes the code
Feature 030's entry (2026-08-25) says three things that are not true of the
repo as it stands:

- It says the mark was cut and the icon set became "a single Jost `a` glyph on
  the `--ink` tile." `frontend/public/favicon.svg` is a stroked checkmark with a
  small plus badge on a transparent ground, and `tools/brand/build_icons.py`'s
  docstring says so too.
- It says there is "no separate `--bead` token now that the accent role is
  `--color-accent` directly." `global.css` defines `--bead: #C8432E` with a
  comment explaining that it is deliberately *not* `--color-accent`, and
  `Wordmark.module.css`'s `.accent` reads `--bead`.
- 030's spec called for `favicon.svg` to carry a `prefers-color-scheme` dark
  variant. The shipped file has one hardcoded `#C8432E` and no media query.

So something landed after 030 with no entry. **Find out what** — `git log` on
`frontend/public/favicon.svg`, `tools/brand/build_icons.py`, and `global.css`
will say — and write a correcting CHANGELOG entry as part of this feature.

CHANGELOG.md is append-only. Do not edit 030's entry. Write a new one that says
what 030's entry got wrong and what actually shipped, the way the `video/`
repo's entry 12 corrected entry 06's locator citation. This feature then
supersedes that state on top of an accurate record rather than a fictional one.

## Goal
The tab icon is one deliberate mark instead of two shapes competing in a 16px
box, and the wordmark's counting letters carry a palette instead of a single
colour — so the abacus idea 030 was built on is visible rather than described.

## In scope
- One redrawn mark, across every generated icon size
- A letter-keyed colour palette for `b`, `c`, `d`
- The token shape that lets the icon and the wordmark disagree on purpose
- The correcting CHANGELOG entry described above

## Out of scope
- The header's three-zone structure, `AccountMenu`, the active-nav indicator,
  the skip link, the focus ring. 030 built all of it and none of it is what you
  reported.
- The settle animation. It keys off `.accent` and `--i` and keeps working
  unchanged. Do not add a per-colour stagger; one motion moment per session was
  a deliberate limit.
- The Jost subset. See the constraint below — it changes what the mark can be,
  but the subset itself does not change.
- The `--ink`/`--rod`/`--wash`/`--rule`/`--paper` tokens.
- The descriptor copy ("Get Wicked Smart!"). Separate argument, not this one.
- Anything in superCPE. See "Before this crosses over" at the end.

## Part 1 — The mark

### What is wrong with it
The plus sits at (10, 10) in a 32-unit box. The checkmark's left leg starts at
(8, 17.5). At 16px in a tab strip those are roughly four pixels apart, so the
plus does not read as a badge beside the check — it reads as debris on top of
it, which is exactly what you saw.

### The constraint that decides this
`favicon.svg` cannot use `<text>`. An SVG favicon renders in the browser's own
font context; a glyph referenced by name will silently fall back to whatever is
installed and the mark will differ per machine. Whatever the mark becomes, it
ships as **outlined paths** in the SVG and as **drawn geometry** in
`build_icons.py`.

That rules out the easy version of "A+". The Jost subset is `U+61`–`U+64`,
lowercase `a b c d` only — no uppercase `A`, no `+`. An `A+` mark means either
outlining an `A` from the full Jost source at build time (the file
`build_jost_subset.py` already consumes) and committing the resulting path, or
constructing the `A` from strokes the way the check already is.

### The two options, and a recommendation

**A. The check alone.** Delete the plus, keep the checkmark, re-centre it in the
box and let it grow into the freed space. One shape, unmistakable at 16px, and
the geometry already exists and is already mirrored between the SVG and the
Python. Roughly a ten-line change.

The cost: a bare checkmark is the single most common mark on the internet, and
it says "done" rather than "abacadaba."

**B. `A+`.** Better idea, harder execution. The lockup you described — plus to
the right of the `A`, never over it — is the correct typographic form, and at
display sizes it will look good.

At 16px it is two shapes sharing a box roughly seven pixels wide each. Make it
work by refusing to treat them as equals: the `A` takes the full cap height and
sits left of centre; the plus is about 40% of that height, aligned to the `A`'s
upper right, with clear ground between the `A`'s right stroke and the plus's
left arm at every size. **Judge it at actual size in a real tab strip, not
zoomed** — a mark that reads at 512px and mushes at 16px is the standard way
this goes wrong. If the plus cannot hold its own pixels at 16, drop it from the
16 and 32 rasters and keep it in the SVG and the large sizes. A mark that
simplifies at small sizes is normal; a mark that smears is not.

**Recommendation: B, with A as the fallback you take without regret** if the
16px version does not hold up. Decide by looking, not by argument.

### One thing to think about before committing to A+
`A+` is a grade. abacadaba's assessment is pass/fail against a threshold —
`Course.pass_ratio`, floored at 70% — and awards no letter grades at all. On
abacadaba, the rehearsal, that is a harmless bit of wit. Carried to superCPE it
becomes a mark that implies a grading scheme a CPE certificate does not have.
Not a reason to reject it here. A reason to decide it here rather than inherit
it there.

### Tasks
1. Redraw `frontend/public/favicon.svg` as outlined paths. Add the
   `prefers-color-scheme: dark` variant 030's spec asked for and never shipped.
2. Update `tools/brand/build_icons.py` to the same geometry. Its docstring
   already promises it "mirrors favicon.svg's geometry — same viewBox, same
   strokes"; keep that promise true, and update the docstring, which currently
   describes the mark you are removing.
3. Regenerate every size: `favicon.ico` (16/32/48), `apple-touch-icon.png`,
   `icon-192`, `icon-512`, `icon-maskable-512`. The maskable one insets art to
   the Android 40% safe zone — verify the new mark still clears it rather than
   assuming the old inset carries over.
4. Check whether `tools/brand/build_og_default.py` draws the mark. 030's entry
   says `og-default.png` lost it, but that entry has already been wrong three
   times in this file, so look rather than trust it.

## Part 2 — The wordmark palette

### This reverses a decision, and that is fine
030 chose one accent colour deliberately: "The b, c and d take `--bead` and sit
one step lighter, so they read as objects on a line rather than as emphasis."
You are overturning that, and the concept survives — arguably it lands harder.
030's own framing is an abacus: the `a`s are the constant rod, `b c d` are beads
counting along it. Beads on an abacus are coloured. One colour was the cautious
reading of the idea.

### The rule that makes it a system instead of decoration
The word is `a b a c a d a b a`. **Colour is keyed to the letter, not to the
position.** Three colours, and the second `b` takes the same colour as the
first:

```
a  b  a  c  a  d  a  b  a
   ①     ②     ③     ①
```

Four colours across four accent slots would make the two `b`s different, which
breaks the only pattern the word actually has. The sequence *returning* to `b`
is the thing worth showing.

### "Cool" is the word to pin down
030 rejected a cool palette on stated grounds: "the existing course thumbnails
are heavily blue, and a warm metallic separates the chrome from the content
instead of competing with it." If you mean cool literally — blues, teals,
violets — you are putting the wordmark into the same family as the thumbnails it
sits above, and that reason has not gone away. If you mean it colloquially, a
mixed palette is open.

Measured contrast for the candidates, against white, against the header's
`--wash` (#F2F5F7), and against the dark-mode page background (#16151A):

| Colour | on white | on `--wash` | on dark bg |
| --- | --- | --- | --- |
| `#C8432E` current `--bead` | 4.89 | **4.46** | 3.72 |
| `#B45309` brass | 5.02 | 4.59 | 3.62 |
| `#0F766E` teal | 5.47 | 5.00 | 3.32 |
| `#0E7490` deep cyan | 5.36 | 4.89 | 3.39 |
| `#BE123C` rose | 6.29 | 5.74 | 2.89 |
| `#A21CAF` magenta | 6.32 | 5.77 | 2.87 |
| `#1D4ED8` blue | 6.70 | 6.12 | 2.71 |
| `#4338CA` indigo | 7.90 | 7.22 | 2.30 |

Note the current `--bead` is already at 4.46 on the surface it actually sits on.
That is under 4.5. Fixing it is a small independent reason to be in here.

**Recommended set**, warm-cool-warm, one cool note so it does not read as a
blue product: `b` `#C8432E` darkened enough to clear 4.5 on `--wash`,
`c` `#0F766E`, `d` `#B45309`. **If you want it literally cool**: `#0E7490`,
`#4338CA`, `#A21CAF` — all clear on light, all fail on dark, see below.

Hold every value to **4.5:1 on `--wash`**. The letters are `aria-hidden` with
the accessible name on the link, so a strict WCAG reading says they are
decorative and the ratio does not apply. Do not take that exemption. These are
the only brand words on the page and people read them with their eyes.

### Token shape
The favicon needs exactly one colour. Keep `--bead` as that colour — the mark's
own — and add the letters as their own tokens:

```css
--bead:   /* unchanged role: the favicon mark, one colour */
--bead-b:
--bead-c:
--bead-d:
```

Then `--bead` and `--bead-b` may or may not be the same value, and that is a
choice someone makes rather than a coupling nobody noticed. Extend the existing
comment block in `global.css` — it already explains why `--bead` is not
`--color-accent`, and it should now also explain why there are four of these.

### Tasks
1. Three tokens in `global.css`, plus the comment.
2. `Wordmark.jsx`: `LETTERS` already carries `{ char, accent }`. Give each accent
   entry the token name it takes, keyed by `char` so the two `b`s cannot drift.
   Do not build a colour-cycling index — that is the position-keyed version this
   file just rejected.
3. `Wordmark.module.css`: one class per bead colour, or a CSS custom property set
   per letter. Whichever is fewer moving parts.
4. Leave `.constant`, the animation, and the `aria-hidden` structure alone.

## Things to check rather than assume
- **Dark mode.** The `prefers-color-scheme: dark` block in `global.css`
  redefines every `--color-*` token and none of the brand ones. `--ink`
  (#0C2233) against the dark page background measures 1.12:1 — invisible. That
  is only a live bug if the header background follows `--color-bg`; if it uses
  `--wash`, the header stays light in dark mode and everything is fine. **Open
  the header CSS and find out**, in dark mode, before picking values. If it is a
  live bug it is a real one and predates this feature — report it rather than
  silently fixing it inside a palette change.
- **Favicon caching is aggressive.** Browsers cache `.ico` at the profile level
  and a normal hard refresh often will not clear it. Verify in a fresh profile
  or a private window, or you will spend an hour debugging a correct build.
- **The `.ico` link order in `index.html`.** 030 got this right — `.ico` first
  with an explicit `sizes`, then the SVG — and it is easy to disturb while
  editing nearby. Leave it.

## Acceptance criteria
- The new mark is legible at 16px in a real tab strip, on a light and a dark tab
  bar, in a fresh browser profile
- Every generated size regenerates from `build_icons.py` and matches
  `favicon.svg`; the maskable icon still clears the 40% safe zone
- `b`, `c`, `d` render in three distinct colours; both `b`s match
- Every accent colour measures at least 4.5:1 against `--wash`; record the
  measured numbers in the changelog rather than asserting they pass
- The settle animation still runs once per session and is still absent under
  `prefers-reduced-motion: reduce`
- The wordmark's accessible name is still "abacadaba, home" and a screen reader
  still does not spell the word out
- `npm run lint` and `npm run build` pass

## COMPLIANCE.md
No row. Brand colour and tab iconography map to no locator in
`docs/2026-Statement-on-Standards-for-CPE-Programs.pdf`. CLAUDE.md requires that
conclusion be stated explicitly rather than left implicit, so say it.

Feature 027's note applies while you are in the file: the matrix covers the
Standards document and nothing else, and a green column is not full coverage.
That note is the reason a purely cosmetic feature still gets a sentence here.

## Before this crosses over
abacadaba's compliance machinery is meant to be identical to superCPE's; only
the subject matter differs. Its *branding* is meant to be nothing of the kind.
Whatever mark comes out of this is abacadaba's, and the `A+` question above is
the specific thing not to carry across without deciding again.

## When done
Two CHANGELOG entries, both appended, neither editing history:

1. The correction — what 030's entry claims, what the repo actually contains,
   and what `git log` says landed in between.
2. This feature — which mark option was taken and what the 16px test looked
   like, the three colour values with their measured ratios, what the dark-mode
   check found, and whether `build_og_default.py` needed touching.

Then stop.
