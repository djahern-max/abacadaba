# Current Feature

## Video pipeline 02, Multi-lesson support and data-driven slides

## Goal

The `video/` package renders exactly one lesson. `Lesson.tsx`, `Sheet.tsx`,
`Root.tsx`, and `generate-audio.ts` all import `./lesson-01` by name, and every
slide component in `slides.tsx` has its content hard-coded inside it.

After this feature:

- A lesson is selected by name, not by import. `npm run render -- Lesson02` and
  `npm run generate -- --lesson 02` both work.
- Six generic slide components render from a `figure` payload in the data file,
  so a new lesson is a new data file and nothing else.
- `lesson-02.ts` compiles, renders silent, and is ready for narration.

## Non-goals — do not do these

**Do not migrate lesson-01's slides onto the generic components.** `Misconception`,
`LegacyBranch`, `FiveSteps`, `Criteria`, `Methods`, and the rest stay exactly as
they are. Lesson 01 has generated audio whose measured reveals are indexed
positionally against those specific components; re-rendering it with different
slides would invalidate `audio-meta.json` and change a video that is already
correct. The generic set is **additive**. Both live in `SLIDES`.

**Do not regenerate any lesson-01 audio.** No task here touches
`video/public/audio/` or `video/src/audio-meta.json` for lesson 01.

**Do not add animation to the generic slides.** Reveal-in only, using the
existing `revealAt` / `isRevealed` helpers. The one spring in this package lives
on lesson 01's S-05 and should stay the only one.

## Two things that must survive

**Timing is measured, never typed.** No number expressing a duration or a reveal
point may appear in any component. Everything reads through `durationOf` and
`revealsOf`.

**There is one copy of the narration text.** `narration` is the transcript of
record and carries the `[[r]]` markers. `speech` exists only for blocks where a
word must be *said* differently than it reads. Lesson 02 needs no `speech`
anywhere — its numerals live in `figure`, and its narration spells numbers as
words already.

## Tasks

### 1. `video/src/lesson-02.ts` — fix the file that is already committed

The file exists and is wrong in four specific ways.

**a. Delete the `speech` field** from the `Block` type and from all twelve
blocks. Move each block's `[[r]]` markers out of `speech` and into `narration`,
at the same word positions. The marker goes immediately before the word it
reveals, mid-sentence where that is where the word falls. Discard the rest of
the `speech` text — `narration` already reads correctly for TTS.

**b. Add the `reveals` fallback array** to every block. Its length must equal
that block's marker count, or slide components will index `undefined` and
elements will never appear. Marker counts, for checking:

| block | markers | block | markers |
|---|---|---|---|
| title | 3 (already present) | block-06 | 2 |
| block-01 | 4 | block-07 | 4 |
| block-02 | 3 | block-08 | 4 |
| block-03 | 6 | block-09 | 4 |
| block-04 | 1 | block-10 | 2 |
| block-05 | 2 | block-11 | 1 |

Values are a preview fallback only, discarded the moment audio exists. Distribute
them evenly across `estimatedSeconds`, first at 1.0s, last no later than
`estimatedSeconds - 3`. Do not hand-tune them.

**c. Recompute `estimatedSeconds`** as `Math.round(wordCount / 130 * 60)` for
every block. They were written at 145 wpm; `lesson-01.ts`'s doc comment says the
constant is 130. Leave the title block at 8.

**d. Add the exports** `transcriptOf`, `speechOf`, `hasAudio`, `durationOf`,
`revealsOf`, `usingEstimates`, `totalSeconds`, copied from `lesson-01.ts`
unchanged, and the `import audioMeta from "./audio-meta-02.json"` they read from.

### 2. `video/src/audio-meta-02.json`

Create it containing exactly `{}`. One metadata file per lesson — do not merge
lesson 02's measurements into `audio-meta.json`, and do not add a lesson key to
it. Two files that each mean one thing beat one file with a nesting level.

### 3. `video/src/lessons.ts` — new

A single place that maps a lesson id to its module, so nothing else has to
import a lesson by name.

```ts
import * as lesson01 from "./lesson-01";
import * as lesson02 from "./lesson-02";

export const LESSONS = { "01": lesson01, "02": lesson02 } as const;
export type LessonId = keyof typeof LESSONS;
```

If the two modules' shapes have drifted enough that this does not typecheck,
the fix goes in `lesson-02.ts` to match `lesson-01.ts`, not the other way round.

### 4. `video/src/slides.tsx` — six generic components

Add, alongside the existing components, one component per `Figure` kind:
`Statement`, `Facts`, `Calc`, `List`, `Compare`. `Title` already exists — extend
it to read from a lesson's `meta` rather than lesson 01's.

`SlideProps` gains an optional `figure`. Existing components ignore it.

```ts
type SlideProps = { reveals: number[]; figure?: Figure };
```

Every generic component reveals its items one per `reveals` entry, in order,
using the existing `revealAt` helper. Reuse `Eyebrow`, `Heading`, and `Panel`
from this file — the drawing-set language is not being redesigned.

`Calc` is the one that needs thought. It is a right-aligned figure column with
left-aligned labels, monospace for the numbers so the digits line up, a hairline
rule above any row with `rule: true`, and flag pink on any row with
`emphasis: "right"`. `emphasis: "wrong"` renders in slate, not red — the sheet
is a working calculation, not an error state. Rows appear one at a time; a row
with no marker of its own appears with the previous one.

Add all six to the `SLIDES` registry.

### 5. `video/src/Sheet.tsx`

It imports `meta` from `./lesson-01`. Take `meta` as a prop instead. `Lesson.tsx`
is the only caller.

### 6. `video/src/Lesson.tsx`

Take `lessonId: LessonId` as a prop, resolve the module through `LESSONS`, and
pass `figure={block.figure}` to the slide. Audio path becomes
`audio/${lessonId}/${block.id}.mp3`.

Move the existing files: `video/public/audio/block-*.mp3` →
`video/public/audio/01/block-*.mp3`. This is a `git mv`, not a re-generation.

### 7. `video/src/Root.tsx`

Register `Lesson01` and `Lesson02` as separate compositions, each with its
duration derived from its own lesson's `totalSeconds`. The estimated-duration
warning must fire per composition, reading that lesson's `usingEstimates`.

### 8. `video/scripts/generate-audio.ts`

Add `--lesson <id>`, defaulting to `01`. It selects which module to read blocks
from, which meta file to write, and which audio subdirectory to write into.
Everything else — hashing, skipping unchanged blocks, `--only`, `--force`,
`--dry-run` — is unchanged.

**Voice settings stay frozen at the current values for this feature.** Do not
add a `speed` parameter. That is a separate decision recorded below.

### 9. `video/package.json`

```json
"render": "remotion render Lesson01 out/lesson-01.mp4",
"render:02": "remotion render Lesson02 out/lesson-02.mp4",
"generate": "tsx scripts/generate-audio.ts",
"generate:02": "tsx scripts/generate-audio.ts -- --lesson 02"
```

## Acceptance

- `npx tsc --noEmit` clean
- `npm run generate -- --dry-run` reports 7 blocks for lesson 01, unchanged
- `npm run generate:02 -- --dry-run` reports 11 narrated blocks and spends nothing
- `npm run render` produces a lesson 01 MP4 **visually identical to the current
  `out/lesson-01.mp4`** — verify by scrubbing S-01 through S-07 in Studio, not
  by reading the diff
- `npm run render:02` produces a silent lesson 02 MP4 with all twelve sheets,
  every figure element visible by the end of its block
- The estimated-duration warning shows on Lesson02 and not on Lesson01
- `git status` shows the audio files as renames, not as deletes plus adds

## Open threads — record these, do not act on them

**Lesson 01 and lesson 02 will have different narration pacing.** Lesson 01 was
generated at the default speed. Lesson 02 will likely be generated faster, after
a one-block speed test. Both live in the same course, so before that course
publishes, lesson 01's seven blocks must be regenerated at the matching speed and
lesson 01 re-rendered. This is deferred cost, not deferred correctness — but it
must not be forgotten, because a participant taking both lessons in one sitting
will hear it.

**Lesson 01 closes by promising the performance obligation as the next lesson.**
Lesson 02 is the cost-to-cost calculation instead, and closes by pointing to the
performance obligation lesson. Either lesson 01's block-07 gets regenerated, or
the course sequence accepts a one-lesson delay against a stated promise.

## When done

Append to `CHANGELOG.md`. Update `video/README.md`'s Structure section — it names
`lesson-01.ts` and "the seven slide components," both now wrong. Note explicitly
in the changelog that lesson 01's slides were **not** migrated and why.

Update `COMPLIANCE.md` only if this feature changes what a locator requires. It
probably does not: this is build tooling, and the 7.02.7 runtime constraint is
unchanged. Say so explicitly rather than leaving the section blank.

`lesson-02.ts` remains `DRAFT — NOT REVIEWED`. Do not generate its audio as part
of this feature — a licensed CPA has to read the narration and check the
arithmetic first, under 4.01.1 and 4.02.
