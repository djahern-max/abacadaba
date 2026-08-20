# Session notes — 2026-08-20

## What we built

An automated narration pipeline for Remotion lesson videos. One command now
produces the audio, measures its real duration, and derives every animation
timing from the audio itself.

The first course video is complete: **ASC606-CON-01, "Why Percentage of
Completion Is No Longer a Method."** 8m06s, seven narrated sheets plus a title
sheet, rendered to `video/out/lesson-01.mp4`.

## The problem this solved

Before today, `reveals` on each block was an array of seconds typed by hand and
guessed against a word-count estimate at 145 wpm. That worked while the video
was silent. The moment real narration existed, every guess drifted.

How badly, measured:

| block | estimated reveals | measured reveals | worst drift |
|---|---|---|---|
| block-01 | 1, 14, 26 | 1.9, 23.7, 37.2 | 11.2s late |
| block-03 | 22, 25, 28, 31, 34, 43 | 30.5, 33.6, 37.5, 40.1, 44.2, 53.8 | 10.8s late |

Block-03 lists the five steps of ASC 606. Under the estimates, all five would
have appeared on screen before the narrator started naming them — the slide
would have carried no meaning at all. Nothing in a silent render would have
revealed this.

## How it works

`scripts/generate-audio.ts` calls ElevenLabs'
`/v1/text-to-speech/{voice}/with-timestamps`, which returns the audio **and**
character-level alignment data — the exact second every character is spoken.

Reveal points are marked inside the narration text with `[[r]]`. The script
strips the markers before sending, then locates each marker's position in the
alignment stream and reads off the real timestamp. Timings became a measurement
rather than a guess.

Marker placement rule that matters: **mark the word, not the sentence.** The
strikethrough on S-01 draws across the word "method," so the marker sits
immediately before that word mid-sentence, not at the start of the sentence.

## Three ideas holding this up

Everything else is machinery serving these:

1. **Content is data.** `lesson-01.ts` is an array of plain objects. No React,
   no JSX. It is what an LLM will eventually emit.
2. **Timing is measured, never typed.** Everything reads from
   `audio-meta.json`. There is no timing number anywhere in a component.
3. **Presentation is reusable.** The slide components do not know which lesson
   they render.

## Changes made

**New**
- `video/scripts/generate-audio.ts` — generate, measure, write metadata
- `video/src/audio-meta.json` — duration, measured reveals, content hash per block
- `video/public/audio/block-01.mp3` … `block-07.mp3`
- `reveal-markers.md`, `current-feature_video-01.md` — specs handed to Claude Code

**Deleted**
- `video/scripts/measure-audio.mjs` — the ffprobe path, superseded
- `video/src/durations.json`
- `AUDIO_PRESENT` in `Lesson.tsx` — a hand-maintained map that could go stale

**New exports in `lesson-01.ts`**
`transcriptOf`, `speechOf`, `hasAudio`, `durationOf`, `revealsOf`,
`usingEstimates`, `totalSeconds`

**Config**
- `tsx` and `@types/node` added; `scripts` added to tsconfig `include`
- ElevenLabs key in `video/.env`, gitignored, scoped to TTS + dictionaries,
  capped at 20,000 credits per period
- Voice: Russ, `HKFOb9iktHA85uKXydRT`, model `eleven_multilingual_v2`

## Decisions worth remembering

**No pronunciation dictionary.** Russ reads "ASC 606-10-25-27" correctly
unaided. Verified on block-04 before bulk generating — one API call to close a
whole workstream. Revisit only if a future lesson introduces terms he mangles.

**Voice settings are frozen at stability 0.55.** ElevenLabs is nondeterministic,
so regenerating a block gives a different take. Changing voice settings or
adding a dictionary means regenerating everything for consistency. Settle those
before bulk generation, never during.

**MP3s are committed to git.** They cannot be reproduced from source, which
makes them source, not build output. `video/out/` stays ignored — the MP4 *is*
reproducible.

**Estimates stay, but only as previews.** Block-03 ran 24% over its estimate
because Russ pauses between list items and word counts cannot model that. Do not
chase this with a better wpm constant. List-heavy blocks will always
under-estimate.

## Compliance state

Runtime 486 seconds, measured. Under 7.02.7, with the entire program a video:

```
[8.11 min + (8 questions x 1.85)] / 50 = 0.458 → 0.4 credits
```

0.4 is a legal award — self-study may start at one-fifth and add in one-fifth
increments up to a full credit (Section 7.01).

**Caveats to carry forward:**
- That figure is a segment-level sanity check, not a course credit. Under
  feature 019 the **course** is the credit-bearing unit. The real calculation
  sums all five lessons' runtimes and all their questions.
- Five lessons at this length puts the course near 2 credits, which sets the
  question minimums: at least 3 review and 5 assessment questions **per credit**
  (5.01.2.1, 6.01.2). No true/false items count.
- The video still carries the `DRAFT — NOT REVIEWED` stamp from `meta.status`.
  It stays until a reviewer signs. Fine for platform testing; not fine for
  anything a CPA sees as finished.
- The transcript must be published as an accessibility supplement, not as
  required course content. If it is required reading, the narration becomes
  "narration of the text" under 7.02.7 and the runtime argument is lost.

---

# Next session

## Open question from this session

Watch the full 8m06s and note anything that needs fixing:
- Do Russ's tone and pacing hold across sheet changes, or reset at each seam?
- Block-03: six reveals over 23 seconds instead of the 21 designed for. Better
  rhythm, or does it drag?
- Block-05 at 57.8s: the AND gate, the only animation in the piece. Does it land?

Any fix is a marker move plus `npm run generate -- --only block-0N`.

## The decision to make

**Lesson two, or feature 021 first?**

**Lesson two** is the cheap test of an expensive assumption. Right now there are
seven slide components and every one was built for the block it renders —
`Criteria` exists because criterion (c) has two halves, `FiveSteps` because
there are five steps. If lesson two reuses most of them, this is a system. If
every lesson needs bespoke slides, it is a very good one-off and the automation
thesis does not hold. That question should be answered before building more on
top of it.

Lesson two is already written into the S-07 handoff: *what exactly is the
performance obligation in a construction contract?*

**Feature 021, the development and review chain** — `developer_id`,
`reviewer_id`, `reviewed_at`, `review_notes`, a sources table, publish blocked
when there is no reviewer or when reviewer equals developer. `next-features.md`
says build this before the LLM pipeline, and that is right: an auto-generated
lesson with no second signature is not publishable CPE, and retrofitting a
second signature onto a workflow designed around one person clicking through is
painful.

Recommendation: **lesson two first.** It is a few hours, it answers the
structural question, and it makes 021's requirements concrete instead of
theoretical.

## Smaller items

- **Upload lesson-01.mp4 to the app** and confirm the watch gate works against a
  real 486-second file. Feature 017 should auto-fill `duration_seconds` from the
  upload — verify it does, rather than typing the number.
- **Dry-run ordering bug** in `generate-audio.ts`: the unchanged check runs
  before the dry-run check, so already-generated blocks report "skipped" instead
  of their marker count. A dry run spends nothing and should always report. Move
  the `if (dryRun)` branch above `if (unchanged && !force)`.
- **README** — confirm the build order section reflects `npm run generate` and
  no longer describes the retired four-step manual flow.

## Context to bring

The project files (2026 Standards, Fields of Study, crosswalk, explanatory memo)
and the repo. Say which of the two paths above was chosen, and what the full
watch-through turned up.
