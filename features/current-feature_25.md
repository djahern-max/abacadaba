# Current Feature

## Feature 025, Favicon and header identity

## Goal
The product tells a signed-in participant what it is before they read anything
else. Today the header is the bare string `abacadaba` in the browser's default
bold, and the tab carries Vite's default icon. Both are placeholders that have
outlived their placeholder status.

This feature ships a mark, a wordmark, a header that separates product
navigation from account controls, and a complete favicon set.

## Numbering
024 and 026 are already reserved (certificate content; refund, cancellation and
complaint policies). 025 was unclaimed, so this takes it. If you would rather
keep design work off the app sequence entirely, renumber to `design-01` and
follow the `video/` precedent of a parallel track.

## What is actually wrong
Observed on abacadaba.com, signed in:

- The tab icon is the framework default.
- `abacadaba` is set in the body font at default bold. To anyone who does not
  already know the name, it is a string of letters.
- Four items sit in one undifferentiated row: `My progress`, `Admin`,
  `Daniel Ahern`, `Sign out`. Two are navigation, one is a label, one is a
  destructive-ish action. Nothing distinguishes them.
- `Sign out` is the only underlined item on the page, which makes the most
  consequential control look like the primary one.
- `Admin` sits inline with participant navigation with no indication it is
  privileged and invisible to most accounts.
- There is no current-page indication.
- The header does not identify the product as CPE, or as anything.

## The idea the design is built on
The name is `abacus` crossed with `abracadabra`, and the spelling carries a
structure worth using rather than hiding:

```
a b a c a d a b a
^   ^   ^   ^   ^     the a's are constant  — the rod
  ^   ^   ^   ^       b, c, d ascend        — beads counting along it
```

Every odd position is `a`. The even positions count up b, c, d and return to b.
So the wordmark sets the a's as the constant and the b/c/d as the moving
elements. The mark is the same idea reduced to one bead and one rod, which is
also a constructed lowercase `a`.

That connection is the entire concept. Everything below is quiet so it can be
the loud thing.

## Tokens
Add to the global stylesheet's `:root`. If tokens already exist under different
names, map onto them rather than adding a parallel system, and say so in the
summary.

```css
--ink:   #0C2233;  /* wordmark, body text, mark tile          */
--rod:   #7A94A6;  /* the constant: rules, borders, muted text */
--bead:  #C8871B;  /* the counter: active state, focus, mark   */
--wash:  #F2F5F7;  /* header background, hover                 */
--rule:  #DDE5EA;  /* hairlines                                */
--paper: #FFFFFF;
```

Brass over the more obvious accents on purpose: the existing course thumbnails
are heavily blue, and a warm metallic separates the chrome from the content
instead of competing with it.

## Part 1 — Favicon
Assets are built and attached to this feature. Drop them in `frontend/public/`
unmodified:

```
favicon.svg              scalable, with a prefers-color-scheme dark variant
favicon.ico              16 / 32 / 48 multi-resolution, for Safari and pinned tabs
apple-touch-icon.png     180x180
icon-192.png
icon-512.png
icon-maskable-512.png    art inset to the Android 40% safe zone
site.webmanifest
```

`build_icons.py` is included so the raster set can be regenerated from the same
geometry if the mark changes. It is a build artifact, not application code —
put it wherever the repo keeps those, not in `frontend/src`.

In `frontend/index.html`, inside `<head>`:

```html
<link rel="icon" href="/favicon.ico" sizes="48x48">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<meta name="theme-color" content="#0C2233">
```

Order matters. The `.ico` is declared first with an explicit `sizes` so browsers
without SVG favicon support do not fall through to a 404.

Set `<title>` too. It is currently just `abacadaba`; make it
`abacadaba — short CPE lessons` on the shell, and let route-level titles
override.

Check that nothing in `vite.config` rewrites or hashes `public/`, and that the
DigitalOcean nginx config serves `.webmanifest` as
`application/manifest+json`. A wrong content type here fails silently — the
manifest simply does not apply and no error surfaces.

## Part 2 — Wordmark
A `Wordmark` component, not a string. Mark on the left, wordmark to its right.

The a's take `--ink` at the display weight. The b, c and d take `--bead` and sit
one step lighter, so they read as objects on a line rather than as emphasis.
Tighten tracking slightly; the alternation needs the letters close to read as a
rhythm.

**Accessibility, and this is the part that gets missed.** Splitting a word into
per-letter spans makes some screen readers announce it letter by letter. Put the
label on the link and hide the letters:

```jsx
<a href="/" className={s.brand} aria-label="abacadaba, home">
  <Mark aria-hidden="true" />
  <span className={s.wordmark} aria-hidden="true">
    <i>a</i><b>b</b><i>a</i><b>c</b><i>a</i><b>d</b><i>a</i><b>b</b><i>a</i>
  </span>
</a>
```

Use `<i>`/`<b>` as bare hooks with `font-style` and `font-weight` reset in the
module, or plain spans with two classes — either is fine, but do not let the
default italic and bold semantics through.

**Type.** The wordmark needs a display face; the body font it currently borrows
has no personality to lend.

Use a face with a **single-storey `a`** — a geometric one, Futura-lineage. The
mark is a circle beside a stem, which is exactly what a geometric single-storey
`a` is, so the mark and the letter become the same object and the mark reads as
the first letter of the name rather than as an unrelated logo sitting next to
it. A double-storey `a` breaks that and the mark goes back to being decoration.

**Jost** is the pick: free, variable, Futura-derived, and less worn than
Poppins, which is the other obvious candidate and is everywhere. **Subset it to
`a b c d` only** — four glyphs is roughly 2 KB woff2, one request,
`font-display: swap`, preloaded. Do not pull a full family for a nine-letter
word.

If adding a webfont is not wanted, the fallback is the existing stack with
tighter tracking and the two-colour treatment, which carries most of the idea.
Say which you chose.

**Descriptor.** A short line beside the wordmark, `--rod`, small caps or
uppercase at ~11px, hidden below 640px. Pick one and use it everywhere:

- `Short CPE lessons` — plainest, says what it is
- `CPE, one piece at a time` — says what makes it different
- `Compliance rehearsal` — internal framing; probably too inside-baseball for a
  participant

## Part 3 — Header structure
Three zones, not one row.

```
┌──────────────────────────────────────────────────────────────────────┐
│  [◐] abacadaba   Short CPE lessons  │  My progress   │  Daniel Ahern ▾│
│      ───────                        │  ▔▔▔▔▔▔▔▔▔▔▔   │  · Admin       │
└──────────────────────────────────────────────────────────────────────┘
   brand                                 product nav      account menu
```

**Product nav.** `My progress`, and whatever else earns a slot later. Nothing
underlined by default.

**Active state.** This is where the concept pays off a second time: the current
page is marked by a short rule in `--rod` with a single `--bead` dot centred on
it — a bead resting at its position. It is the same object as the mark, at
nav scale, and it encodes something true rather than decorating. `aria-current="page"`
on the link; the indicator is CSS on `[aria-current="page"]` so the accessible
state and the visual state cannot drift apart.

**Account menu.** The name becomes a button opening a small menu containing
`Admin` (rendered only for accounts that have it) and `Sign out`. This solves
three problems at once: `Sign out` stops being the most prominent control,
`Admin` moves out of participant navigation, and the name stops being inert
text. Standard menu-button semantics — `aria-expanded`, `aria-haspopup="menu"`,
`role="menu"`, arrow-key navigation, Escape closes and returns focus, click
outside closes.

**Chrome.** Header background `--wash` against `--paper` content, a 1px `--rule`
bottom border. Sticky, with the border deepening once scrolled past ~8px — one
class toggled from a passive scroll listener, no library.

**Mobile.** Below 640px: mark plus wordmark, descriptor hidden, product nav and
account collapsed behind a single menu button. If the app already has a mobile
nav pattern, use it rather than inventing a second one.

**Signed out.** The same header with the account zone replaced by a single
`Sign in`. Do not build a separate marketing header.

## Part 4 — Quality floor
Not optional, and not worth a separate feature:

- A skip link to `<main>` as the first focusable element.
- `:focus-visible` rings in `--bead` at 2px with 2px offset, on every
  interactive element in the header. The current default outline is inconsistent
  across the nav.
- Contrast: `--rod` on `--wash` is too light for body text. Use it for rules,
  borders and the descriptor only — never for anything a participant has to
  read. Verify the descriptor clears 4.5:1 at its final size, and darken `--rod`
  if it does not.
- One motion moment, and only one: on first paint of a session the beads settle
  into place along the wordmark, ~300ms, staggered. Session-scoped so it does
  not replay on every navigation. `@media (prefers-reduced-motion: reduce)`
  removes it entirely. If it reads as cute rather than confident once built, cut
  it — the static wordmark is the deliverable and the animation is not.

## Part 5 — Link previews
Texting the URL currently produces a grey compass icon and the bare domain. The
favicon does **not** fix this. iMessage, Slack, WhatsApp, Signal, Discord and
LinkedIn all read Open Graph tags, and the site has none.

**The catch, and it is the whole difficulty of this part.** Apple's preview
fetcher does not execute JavaScript. Meta tags set from React — Helmet,
`react-helmet-async`, anything client-side — are invisible to it. Whatever is in
the served HTML is all it will ever see.

So this splits in two.

**5a. Site default.** Static tags in `frontend/index.html`. `og-default.png` is
built and attached, 1200x630:

```html
<meta property="og:type"        content="website">
<meta property="og:site_name"   content="abacadaba">
<meta property="og:title"       content="abacadaba">
<meta property="og:description" content="Short CPE lessons you can actually finish.">
<meta property="og:url"         content="https://abacadaba.com/">
<meta property="og:image"       content="https://abacadaba.com/og-default.png">
<meta property="og:image:width"  content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt"   content="abacadaba">
<meta name="twitter:card"       content="summary_large_image">
```

`og:image` must be an absolute URL. A relative path fails silently on every
platform. Keep the file under 1 MB; the attached one is ~23 KB.

That alone turns the grey compass into a proper card and is most of the win.

**5b. Per-course previews.** A shared course link should show that course's
title, its hook-first description, and its thumbnail. That needs server-rendered
tags, which means one of:

1. A FastAPI route that serves `index.html` with the meta block substituted for
   `/courses/{slug}` — the SPA still boots normally afterwards, since the
   crawler's tags and the app's markup do not conflict.
2. nginx routing crawler user-agents to a small backend endpoint that returns
   meta-only HTML, and everyone else to the static build.

Option 1 is less machinery and does not depend on user-agent sniffing being
right. Prefer it unless the static-serving setup makes it awkward.

Apple's fetcher identifies itself with a UA containing
`facebookexternalhit/1.1 Facebot Twitterbot/1.0`, which is how you test:

```bash
curl -A "facebookexternalhit/1.1 Facebot Twitterbot/1.0" \
  https://abacadaba.com/courses/where-does-it-actually-go | grep 'og:'
```

**Two traps.**

Previews are cached hard, Apple's most aggressively of all. Changing
`og-default.png` in place will not update a preview anyone has already
generated. Version the filename — `og-default-v2.png` — rather than expecting a
cache to expire.

And a course preview must respect `is_published`. Draft courses are already
visible to the admin UI through the wrong endpoint (open bug), so do not let
that mistake reach a public meta endpoint. An unpublished slug returns the site
default card, not the course's.

## Out of scope
- Renaming or rebranding. `abacadaba` stays.
- Course card and thumbnail design. The grid below the header is untouched.
- Dark mode across the app. The favicon ships a dark variant because the tab bar
  demands it; nothing else does.
- Footer, marketing pages, superCPE.
- Any admin UI beyond moving the `Admin` link into the account menu.
- Per-lesson (as opposed to per-course) link previews
- Email and certificate branding. The certificate is 024's problem and will want
  this mark, so keep the assets somewhere 024 can reach them.

## Acceptance criteria
- The tab shows the mark in Chrome, Safari and Firefox, light and dark
- `favicon.ico` is served, not 404'd, and the `.webmanifest` returns
  `application/manifest+json`
- Add to home screen on iOS and Android shows the mark, and the Android icon is
  not clipped by the circle mask
- Lighthouse's installability check passes
- A screen reader announces the brand link as "abacadaba, home" and not as nine
  letters
- The current page is the only nav item with the bead indicator, and it carries
  `aria-current="page"`
- `Sign out` is reachable in at most two interactions from the header, and is
  not visible on the header surface itself
- `Admin` does not render for an account without the role — verify server-side
  behaviour is unchanged and the header is only hiding a link, not enforcing
  anything
- Every header control shows a visible focus ring under keyboard navigation
- Escape closes the account menu and returns focus to the trigger
- At 375px wide nothing wraps, overflows or overlaps
- With `prefers-reduced-motion: reduce`, the wordmark does not animate
- The header font subset is one file and under 5 KB
- Texting `abacadaba.com` to yourself shows the card, not the grey compass
- `curl -A "facebookexternalhit/1.1 Facebot Twitterbot/1.0"` on `/` returns
  `og:image` as an absolute URL in the HTML body, with JavaScript never running
- The same curl on a published course URL returns that course's title,
  description and thumbnail
- The same curl on an unpublished course URL returns the site default card and
  leaks nothing about the draft
- The card also renders in Slack and WhatsApp
- `npm run lint` passes
- pytest passes

## When done
Append to CHANGELOG.md. Note that `Sign out` and `Admin` moved into an account
menu — it changes muscle memory for the two people currently using the site, and
is the only behavioural change in an otherwise visual feature.

Nothing here touches COMPLIANCE.md. Sponsor identification, refund and complaint
policies are 026's scope and belong in the footer, not the header. If you find
yourself putting a NASBA sponsor ID in the header while doing this, stop and
leave it for 026.
