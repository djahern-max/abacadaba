# Reveal marker placements, blocks 02 through 07

Insert `[[r]]` immediately before each anchor phrase below, changing no other
character of the narration text. Anchors are quoted exactly as they appear in
`lesson-01.ts`.

The marker count per block must equal the length of that block's existing
`reveals` array — the slide components index into it positionally, so a
mismatch renders `undefined` and the element never appears. Counts are stated
per block; verify with `npm run generate -- --dry-run` before generating.

Leave the existing `reveals` arrays in place. They remain the fallback until
audio exists for that block.

## Order of work

Do **block-04 first, alone**. It contains `ASC 606-10-25-27`, which is the real
test of whether a pronunciation dictionary is needed. A dictionary changes the
audio for every block, so that question has to be settled before generating the
rest — regenerating gives a different take, and mixed takes are audible as tonal
drift between sheets.

---

## block-04 — S-04 Fork — 5 markers

Slide elements, in reveal order: the heading; the "At a point in time / DEFAULT"
panel; the "Over time / MUST QUALIFY" panel; the "you do not elect" paragraph;
the closing MEET ANY ONE / FAIL ALL THREE rule.

1. before `Step five asks whether a performance obligation`
2. before `Point in time is the default.`
3. before `Over time is the exception`
4. before `You do not elect over-time recognition`
5. before `Meeting any one of them`

Note marker 1 goes before the *second* occurrence of "Step five" — the narration
opens with "Step five is where contractors feel the change", which is the lead-in,
not the heading cue.

---

## block-02 — S-02 LegacyBranch — 5 markers

Reveal order: eyebrow + heading; the "Percentage of completion" panel; the
"Completed contract" panel; the balance-sheet caption with its two panels; the
closing pink line.

1. before `ASC 605-35 gave contractors a purpose-built model`
2. before `Percentage of completion, if you could make dependable estimates.`
3. before `Completed contract, if you could not.`
4. before `costs in excess of billings, or billings in excess of costs`
5. before `ASC 606 took that neighborhood apart.`

Marker 4 sits mid-sentence, immediately before the two phrases the panels
display. The narration reaches them well after the sentence begins.

---

## block-03 — S-03 FiveSteps — 6 markers

Reveals 0 through 4 drive the five numbered steps one at a time. Reveal 5 is the
closing "when, or as" callout. The eyebrow and heading are ungated and need no
marker.

1. before `identify the contract with the customer.`
2. before `Identify the performance obligations in the contract.`
3. before `Determine the transaction price.`
4. before `Allocate the transaction price to the performance obligations.`
5. before `And recognize revenue when`
6. before `When, or as. Four words`

These five are tightly spaced — the narrator lists them in about twelve seconds.
That is the point: the steps should land as he names them, in rhythm. This is
the block where hand-written estimates were least likely to survive contact with
real audio.

---

## block-05 — S-05 Criteria — 5 markers

Reveal order: criterion (a); criterion (b); criterion (c), which also turns pink;
the AND gate closing; the cost-recovery caption.

1. before `The first: the customer simultaneously receives`
2. before `The second: your performance creates or enhances`
3. before `The third: your performance creates an asset with no alternative use`
4. before `both halves have to hold.`
5. before `not just recover your costs.`

**Marker 4 is the most important placement in the lesson.** It fires the AND
gate — the one spring animation in the whole composition. It must land on
"both halves have to hold", not at the start of that sentence. Everything else
in the visual language is deliberately static, so this moment carries weight it
would not carry in a busier deck.

Marker 5 lands on the negation. The caption reads COST RECOVERY ALONE IS NOT AN
ENFORCEABLE RIGHT TO PAYMENT, and it should appear as he says what cost recovery
is *not* enough for.

---

## block-06 — S-06 Methods — 5 markers

Reveal order: eyebrow + heading; the INPUT METHODS column; the OUTPUT METHODS
column; the highlight that marks "Costs incurred" within the input column; the
closing paragraph.

1. before `That is a second, separate decision`
2. before `Input methods measure your efforts`
3. before `Output methods measure results`
4. before `Cost-to-cost is an input method.`
5. before `You are no longer applying a method you elected.`

Marker 4 does not reveal anything new — it re-marks an item already on screen,
turning "Costs incurred" pink. Late is worse than early here: if it fires after
he has moved on, the highlight looks arbitrary.

---

## block-07 — S-07 Summary — 3 markers

Reveal order: eyebrow + JUDGMENT 01 panel; JUDGMENT 02 panel; the NEXT line.

1. before `first, does this performance obligation qualify`
2. before `and second, what measure of progress`
3. before `Next lesson, we go back a step`

---

## Also change

In `lesson-01.ts`, the file comment says estimates come from word count at
~145 wpm. Block-01 measured 48.3s against a 43s estimate, which puts Russ at
roughly **130 wpm**. Update the comment, and if the estimates are ever
regenerated, use 130.

This only affects silent renders before audio exists. It has no bearing on the
credit calculation, which uses measured duration only.

## Verify before generating

```
npm run generate -- --dry-run
```

Expected marker counts: block-01 3, block-02 5, block-03 6, block-04 5,
block-05 5, block-06 5, block-07 3.
