# Lesson video runbook

How to take a lesson from nothing to a published video with recorded credit.
Written after producing lessons 01 and 02 of *Where Does It Actually Go?*

Everything happens on the Mac. The droplet only ever receives the finished
MP4, through the admin UI.

---

## Before you start

Know these three things about the lesson you are building:

- **Lesson number** — `02`, `03`, and so on. Two digits, always.
- **Lesson slug** — read it from the database, do not guess. See step 8.
- **Which learning objective it maps to** — the narration has to actually
  teach that objective, because assessment questions are tied to it.

---

## 1. Write the lesson module

Copy an existing one and edit it. `lesson-02.ts` is the better template
because it imports its types instead of defining them.

```bash
cd ~/projects/abacadaba/video
cp src/lesson-02.ts src/lesson-03.ts
echo '{}' > src/audio-meta-03.json
```

In the new file, change:

- The header comment (lesson number, title)
- `import audioMeta from "./audio-meta-03.json"`
- Every field in `meta` — `lessonId`, `courseCode`, `lessonTitle`, `title`,
  `subtitle`, `eyebrow`
- All the blocks

**Block anatomy.** Each block is one sheet on screen plus the narration read
over it:

```ts
{
  id: "block-01",          // unique within the lesson; drives the mp3 filename
  sheet: "S-01",           // printed in the sheet's corner
  citation: "40 CFR §262.13",
  slide: "Statement",      // Title | Statement | Facts | List | Compare | Calc
  figure: { kind: "statement", lines: ["...", "...", "..."] },
  narration: "Text with [[r]] markers before the word each item appears on.",
  reveals: [1, 25, 49],    // FALLBACK ONLY — discarded once audio exists
  estimatedSeconds: 55,
}
```

**Rules that will bite you if you break them:**

1. **Marker count must equal `reveals` length.** Slide components index into
   `reveals` positionally. A mismatch reads `undefined` and the element never
   appears on screen. The dry run in step 3 checks this.
2. **Figure items should be ≥ marker count.** Extra items reveal alongside the
   last marked one. Fewer items than markers means wasted markers.
3. **Mark the word, not the sentence.** `[[r]]` goes immediately before the
   word the item corresponds to, mid-sentence if that is where it falls.
4. **Never type a timing number anywhere else.** `reveals` and
   `estimatedSeconds` are the only permitted numbers, and both are fallbacks.
   `estimatedSeconds = Math.round(wordCount / 130 * 60)`.
5. **Aim for 40–75 seconds per sheet.** Attention resets every 20–30 seconds
   and a new sheet is the cheapest reset available. Eight blocks of ~120 words
   lands around 6 minutes.

---

## 2. Register the lesson

Add one import line and one map entry:

```ts
// src/lessons.ts
import * as lesson01 from "./lesson-01";
import * as lesson02 from "./lesson-02";
import * as lesson03 from "./lesson-03";

export const LESSONS = { "01": lesson01, "02": lesson02, "03": lesson03 } as const;
export type LessonId = keyof typeof LESSONS;
```

`Root.tsx` loops over `LESSONS`, so the composition appears automatically.
Nothing else to edit.

---

## 3. Typecheck and dry run

Neither spends money. Do not skip.

```bash
npx tsc --noEmit
npm run generate -- --lesson 03 --dry-run
```

The dry run must show every narrated block with its marker count, and the
title sheet must be **absent** — it has no narration by design.

If `tsc` errors on `meta`, you missed a field the sheet chrome reads. The
error names it.

---

## 4. Preview silent

```bash
npm run dev
```

Open `Lesson03` in Studio and scrub every sheet. Check:

- Title sheet renders real text, not blanks
- Every `Facts` row and `List` item is visible by the end of its block
- Console shows the estimated-duration warning — it **should** fire, no audio
  exists yet

This is the last free review. After generation, fixing narration means
regenerating a block, and a regenerated block is a different take.

---

## 5. Generate narration

**This spends ElevenLabs credits.** It is the first irreversible step.

```bash
npm run generate -- --lesson 03
```

The script sends each block's narration to ElevenLabs, strips the `[[r]]`
markers, reads their real timestamps out of the character-level alignment
data, and writes duration + measured reveals + a content hash to
`audio-meta-03.json`. MP3s land in `public/audio/03/`.

**Blocks are cached by content hash.** Re-running skips anything unchanged, so
a second run costs nothing. If you edit one block's narration, only that block
regenerates.

Useful flags:

| Flag | Effect |
|---|---|
| `--dry-run` | Report only, send nothing |
| `--only block-04` | One block, for a pronunciation test |
| `--force` | Regenerate even if the hash matches |

The output line reports total runtime and how many blocks are still
estimated. **It should say zero.**

Ignore the 7.02.7 sanity check it prints. That is this segment alone through
the formula, which is not how credit works — credit attaches to the course,
summing all lessons and all questions, divided once.

---

## 6. Review, then clear the draft stamp

Listen straight through. Two things: reveals landing as the narrator names
each item, and no sheet sounding tonally different from its neighbors.

Send the MP4 to the subject matter expert. When they sign off, set
`status: ""` in `meta` and re-render. **Clearing the stamp does not require
regenerating audio** — it is a re-render only, and free.

---

## 7. Render

```bash
npx remotion render Lesson03 out/lesson-03.mp4
ffprobe -i out/lesson-03.mp4 2>&1 | grep Duration
```

A few minutes. The MP3s are pulled in automatically — the output has audio,
no separate mux step.

**That `ffprobe` duration is the number that matters.** It is measured off the
artifact, and it is the only figure permitted to reach the credit calculation
(7.02.7).

`video/out/` is gitignored. Do not commit the MP4 — it is reproducible from
what is committed.

---

## 8. Commit before uploading

This is the step that was skipped once and cost a morning. The original ASC
606 lesson modules were never committed and existed only in a git stash.

```bash
git add src/lesson-03.ts src/lessons.ts src/audio-meta-03.json public/audio/03/
git commit -m "video: lesson 03 narration and module"
```

The MP3s are worth tracking — regenerating costs money and gives a different
take. The MP4 is not.

---

## 9. Upload

`backend/scripts/upload_video.py` **does not work on production.** It
authenticates with email and password, and every account on the deployed
system is Google-only with a null `password_hash`. Use the admin UI.

1. Sign in as the admin account
2. Open the course → the lesson → the video field
3. Upload `video/out/lesson-03.mp4`
4. Duration auto-fills from the video. Confirm it matches `ffprobe`.
5. Add a description
6. Save

To confirm the lesson slug from the database:

```bash
ssh deploy@134.209.77.184
cd /srv/abacadaba
docker compose -f docker-compose.prod.yml exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"' <<'SQL'
SELECT l.position, l.slug, l.title FROM lessons l
JOIN courses c ON c.id = l.course_id
WHERE c.title = 'Where Does It Actually Go?'
ORDER BY l.position;
SQL
```

The `-T` flag is required when piping a script to `docker compose exec`.

---

## 10. Recompute credit

Course editor → **Recompute credit**.

Credit is stale — and the course cannot publish — whenever the course changes
after the last computation. Adding a video is such a change.

The formula sums total A/V runtime plus questions × 1.85, divides by 50, and
rounds **down** to the nearest one-fifth. It never rounds up.

Expect the number to climb as each lesson lands. Five lessons at ~6:20 is
about 31 minutes of A/V; with 15 questions contributing 27.75 minutes, the
course should reach roughly 1.0 credit once all five are in.

---

## Traps, collected

| Symptom | Cause |
|---|---|
| `generate` says "unchanged, skipped" on a fresh block | The run already happened. Check `public/audio/<id>/` before assuming failure. |
| Composition has audio timings but no sound | `audio-meta*.json` has entries whose MP3s were deleted. Reset the JSON to `{}`. |
| Estimated-duration warning never fires | Same cause. `usingEstimates` is reading stale measurements. |
| `KeyError` on an env var in a one-line-per-variable command | Trailing whitespace after a `\`. Put it on one line. |
| A list item never appears on screen | Marker count ≠ `reveals` length. |
| Reveals land seconds off the words | You are on estimates, not measured audio. |
| CORS error in the browser | Often a 500 surfacing through Starlette middleware ordering. Check server logs first. |
| File missing that "definitely existed" | It was never committed. Commit before you need it. |
