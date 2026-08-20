# abacadaba video

Remotion compositions for CPE lesson videos.

This is a separate package from `backend/` and `frontend/`. It is a build tool
for content, not application code — it pulls in a bundler and a headless
browser, none of which belongs in the API image. Nothing in the app imports
from here; the only output that crosses the boundary is an MP4.

## Setup

```bash
cd video
npm install
npm run dev      # Remotion Studio at localhost:3000
```

## Build order

The order matters, and it is not the obvious one.

**1. Render silent, and judge the slides.** Block durations start as word-count
estimates at ~145 wpm, so you can see the whole lesson before spending a single
ElevenLabs credit. Scrub through Studio. Fix what reads badly.

**2. Generate narration.** Take `narration` from each block in
`src/lesson-01.ts`. Generate one file per block, not one file for the lesson —
when the SME corrects one sentence on sheet S-05, you regenerate S-05 and
nothing else.

Write numbers the way you want them *said* before sending to ElevenLabs. The
narration in `lesson-01.ts` is the transcript of record and is written normally;
"ASC 606" will come out as "ASC six hundred six" unless you spell it "ASC
six-oh-six" in what you actually submit. Keep the two versions distinct — the
ugly one is for the API, the clean one is the transcript.

Save output as `public/audio/block-01.mp3` … `block-07.mp3`. The title sheet has
no narration.

**3. Measure.**

```bash
npm run measure
```

Writes `src/durations.json` from the real audio, prints the runtime and the
credit calculation, and prints the `AUDIO_PRESENT` block to paste into
`src/Lesson.tsx`.

**4. Render.**

```bash
npm run render
```

## Two things that are compliance, not preference

**Estimated durations must never reach the credit calculation.** Under 7.02.7,
when the entire program is video, credit is
`[video minutes + (questions × 1.85)] / 50`. The runtime in that formula has to
be the real one. `Root.tsx` warns loudly when any block is still estimated;
don't render a publishable video while that warning is showing.

**The transcript is a supplement, not required reading.** If the transcript is
presented as required course content, the narration becomes "narration of the
text" under 7.02.7 and you lose the argument for counting runtime. Publish it
labelled as an accessibility aid.

## Structure

```
src/
  lesson-01.ts    content as data — the handoff point from the writing pipeline
  durations.json  measured audio lengths, written by npm run measure
  theme.ts        palette, type, layout tokens
  Sheet.tsx       drawing border + title block, wraps every slide
  slides.tsx      the seven slide components
  Lesson.tsx      sequences blocks; contains no timing numbers
  Root.tsx        composition registration, duration derived from content
scripts/
  measure-audio.mjs
public/audio/     narration, one file per block
```

`lesson-01.ts` is deliberately free of React. When script generation is
automated, that file's shape is what the pipeline emits — so a new lesson is a
new data file plus, at most, a new slide component.

## Design notes

The visual language is a construction drawing set. Each slide is a numbered
sheet inside a drawing border, with a title block in the lower right carrying
the course code, the ASC paragraph under discussion, the revision, and the sheet
number.

That is not decoration. It puts a persistent citation on screen without a
caption fighting the content, and it tells the participant where they are in a
sequence that genuinely is one.

Palette is drafting vellum, graphite, and the fluorescent pink of surveyor's
flagging tape. The pink marks only the thing currently under discussion. **If it
appears on more than two elements at once, something is wrong** — that
restraint is the whole reason it reads as a marker rather than a brand colour.

Motion is deliberately thin. One real animated moment exists, on sheet S-05: the
AND gate closing across the two halves of criterion (c). It earns the animation
because it carries the idea a static slide cannot — that both conditions must
hold, which is exactly where practitioners go wrong.

The `DRAFT — NOT REVIEWED` stamp in the lower left comes from `meta.status` in
`lesson-01.ts`. It is on by design: a course that has not passed content review
should not produce a video that looks finished. Clear it when the reviewer
signs.
