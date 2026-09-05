# Current Feature

## Feature 030b, The share card, and where brand colour lives

## Numbering note
`030a` shipped the mark and the header palette. This is the same surface area —
the brand's colour values and the assets built from them — so it takes the next
letter rather than a whole number.

Confirm `030a`'s CHANGELOG entry is written before overwriting this file in.

## The premise, corrected
The share card is not lost. It renders: dark tile, wordmark, domain line, title
and URL beneath. What is wrong is narrower and more boring than "lost."

`tools/brand/build_og_default.py` colours the wordmark's accent letters with
`ACCENT` — `#a78bfa`, which is `--color-accent`'s **dark-mode** value. The
header stopped using `--color-accent` for those letters when `--bead` was
reintroduced in the undocumented commit `5cfdfc6`, well before 030a. So the
share card has been out of step since 030 shipped, in both colour schemes, and
030a widened a gap it did not open.

Worth stating plainly in the changelog, because "030a broke the OG image" is the
natural assumption and it is wrong. Nothing about the share card changed on
2026-09-05 except that the surface it should match moved further away.

## The trap in the obvious fix
The palette 030a measured — `--bead-b #C0402C`, `--bead-c #0F766E`,
`--bead-d #B45309` — was held to 4.5:1 against `--wash` (`#F2F5F7`), the light
header background those letters actually sit on.

The share card's tile is dark. Against `#0C2233`:

| Token | on `--wash` (header) | on the OG tile |
| --- | --- | --- |
| `--bead-b` `#C0402C` | 4.78 | **3.10** |
| `--bead-c` `#0F766E` | 5.00 | **2.97** |
| `--bead-d` `#B45309` | 4.59 | **3.24** |

So assigning the header tokens to the share card trades an inconsistency for an
unreadable card. It would look like a fix and measure like a regression.

The card needs a **dark-surface variant of the same palette**, which is exactly
what `favicon.svg` already does — `#C8432E` light, `#DE6C52` dark, the latter
measuring 4.93 on this tile.

### Candidate dark-surface values
Each is its light counterpart raised in HLS lightness until it clears 4.5:1 on
`#0C2233`, keeping the hue so the two palettes read as one family:

| Letter | light | dark-surface | on tile |
| --- | --- | --- | --- |
| `b` | `#C0402C` | `#D76452` | 4.51 |
| `c` | `#0F766E` | `#149A90` | 4.69 |
| `d` | `#B45309` | `#DB650B` | 4.55 |

`b`'s dark value lands close to the favicon's existing `#DE6C52`. Decide
whether they should be the same value or stay deliberately separate, and say
which in the changelog — do not let them be accidentally-nearly-identical.

Verify these numbers against the tile colour the script actually uses rather
than trusting `#0C2233` from this file. If the tile is not `--ink`, recompute.

## The actual problem underneath
After 030a, the brand's accent colour is written down in four places, in three
languages, with nothing checking them against each other:

| File | Holds | Language |
| --- | --- | --- |
| `frontend/src/styles/global.css` | `--bead`, `--bead-b/c/d` | CSS |
| `frontend/public/favicon.svg` | light + dark stroke colours | SVG, hardcoded |
| `tools/brand/build_icons.py` | `MARK` | Python |
| `tools/brand/build_og_default.py` | `ACCENT` | Python |

The SVG and `build_icons.py` are kept in step by a docstring promise and human
diligence, which has held so far. Adding a fourth is where that stops being a
convention and starts being a liability — and this feature is the fourth.

There is a second, quieter instance of the same thing already in the repo:
`--bead` is now documented as "the favicon mark's colour only," but nothing
reads it. `favicon.svg` hardcodes its own value and `build_icons.py` hardcodes
`MARK`. A CSS custom property that no stylesheet consumes and no build script
can read is a comment wearing a token's clothes. Changing it will silently do
nothing, which is worse than not having it.

### Pick one, and say why in the changelog

**Option 1 — one source, generated.** A small `tools/brand/palette.json` (or
`.py`) holding every brand colour. `build_icons.py` and `build_og_default.py`
import it. A build step writes `favicon.svg` and the `:root` block from it. One
edit propagates everywhere; nothing can drift.

Cost: a generation step, generated files in `git`, and the question of what
happens when someone hand-edits a generated file.

**Option 2 — one source, verified.** Values stay written where they are. A test
or a `tools/brand/check_palette.py` asserts that `global.css`, `favicon.svg`,
and both Python scripts agree, and fails loudly when they do not. Drift becomes
visible instead of impossible.

Cost: a parser per format, and a check nobody runs unless it is wired into
something.

**Option 3 — accept it, and write it down.** Four files, a comment in each
naming the other three, and the honest note that this is held together by
attention. Legitimate for a rehearsal repo with one person in it.

Cost: it has already failed twice — the `5cfdfc6`/`e7b5988` drift, and this
share card.

**Recommendation: Option 2.** Option 1 is the right end state and the wrong
amount of machinery for a repo this size; Option 3 is what is already in place
and it is what produced this feature. A check that reads four files and compares
hex strings is perhaps forty lines and turns a silent class of bug into a loud
one. **But this is your call, not the implementer's** — and if the answer is 3,
say so deliberately rather than by default.

Also resolve `--bead` while you are here: give it a real consumer, or delete it
and put its value in a comment.

## In scope
- The share card's accent letters, in dark-surface variants of the 030a palette
- Regenerating `og-default.png` and deploying it
- Whichever of the three options above you pick
- Resolving `--bead`'s no-consumer state

## Out of scope
- The header, the favicon, the icon set, the maskable inset. 030a shipped all of
  it and it is verified correct in production.
- The card's layout, tile colour, type, or the domain line. Colour only.
- `og:description` and the site tagline. 030 removed that copy deliberately.
- Per-course share cards' *content*. But see the check below — their rendering
  path may or may not be this script.

## A thing to check rather than assume
`app/services/og.py` serves per-course share cards at
`GET /api/v1/og/courses/{slug}`. **Find out whether those cards render the
wordmark at all**, and if so, whether they go through `build_og_default.py`'s
code path or their own. If they have their own, they need the same palette and
this feature's scope is two files, not one.

Also: the nginx crawler branch that routes crawlers to that endpoint is still
commented out at lines 93 and 100 of `sites-enabled/abacadaba`, despite 030's
entry claiming it was uncommented. So per-course cards may not be reachable in
production at all right now. That is a third instance of the entry not matching
the box — worth confirming and noting, though enabling it is not this feature's
job.

## Tasks
1. Read `build_og_default.py`. Establish the tile colour it actually uses and
   recompute the table above against it.
2. Implement the chosen option from "Pick one" — do this **before** changing
   colours, so the new values land in whatever the new arrangement is rather
   than being moved twice.
3. Replace `ACCENT` with the three dark-surface bead values, keyed by letter,
   both `b`s sharing one value. Same rule 030a established: keyed by character,
   not by array position.
4. Regenerate `og-default.png`. Confirm the file size changes — the previous
   deploy's identical `icon-512`/`icon-maskable-512` byte counts were what
   revealed the maskable inset had never shipped, and a byte count is a cheaper
   check than looking.
5. Deploy. `npm run build` then rsync `dist/` to `/var/www/abacadaba/` — the
   frontend does not go through Docker, and `og-default.png` lives in `public/`,
   so it needs both steps.
6. Verify the card as a card, not as a file: paste the URL into a real client
   after deploying. Note that iMessage, Slack, and Twitter all cache OG images
   aggressively and by URL, so use a cache-busting query string to see the new
   one rather than concluding it failed.

## Acceptance criteria
- Every accent colour on the share card measures at least 4.5:1 against the
  card's own tile; record the measured numbers in the changelog rather than
  asserting they pass
- Both `b`s are the same colour on the card
- The card's palette reads as the same family as the header's, not as a
  different brand
- `og-default.png` changed size from its predecessor
- Whichever source-of-truth option was chosen is in place and, if it is Option
  2, actually fails when a value is deliberately mismatched — test that it
  fails, not just that it passes
- `--bead` either has a consumer or is gone
- `npm run lint` and `npm run build` pass

## COMPLIANCE.md
No row. Share-card colour maps to no locator in
`docs/2026-Statement-on-Standards-for-CPE-Programs.pdf`.

One thing not to disturb: `app/services/og.py` reuses
`courses_service.get_by_slug`'s `is_published` filter, so an unpublished course
cannot leak its title through a share card. That is a real property with tests
in `tests/test_og.py`. If this feature touches that file at all, confirm those
tests still pass and say so.

## When done
A CHANGELOG entry that states plainly that the share card's mismatch predates
030a rather than being caused by it, which source-of-truth option was taken and
why, the measured contrast numbers on the card's own tile, what `--bead` became,
what the per-course card check found, and whether the card was verified in a
real client or only as a file.

Then stop.
