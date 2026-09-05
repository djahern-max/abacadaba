# Current Feature

## Feature 023b, The objective select overflows its panel

## Goal
The learning-objective select on an assessment question stays inside the
question panel, at every width, whatever an objective says.

## Numbering note
Corrective work against 023a's surface area, not new capability: 023a's
frontend task 1 added this select, and it has been wrong since. Hence the
letter suffix rather than the next whole number, following 020b/020c/019a.
If the working numbering has moved past this, renumber — the reasoning is what
matters, not the digit.

## Where this came from
Found while authoring the first real course through the admin UI. The select
extends roughly a hundred pixels past the right edge of the question panel and
past the panel's own border, on a desktop viewport with nothing unusual about
it.

The cause is in `QuestionEditor.jsx`, not in a stylesheet accident:

```jsx
<select
  id={`objective-${question.id}`}
  className={`${styles.kindSelect} ${objectiveDirty ? styles.fieldDirty : ''}`}
```

`.kindSelect` is the Type select's class. Type holds two short words. The
objective select holds a full learning objective — "Explain why buoyant lift
depends on the weight of the air displaced rather than on the weight of the
lifting gas" — and a native `<select>` sizes itself to its widest `<option>`.
Given no width constraint, it takes whatever it needs.

Two controls with opposite content requirements are sharing one class. Fixing
the width on `.kindSelect` would fix this and pointlessly constrain the Type
select at the same time.

## In scope
- A separate class for the objective select, width-constrained to its container
- Truncation of a long option label in the closed state
- The same treatment anywhere else a select is populated from author-entered
  text

## Out of scope
- Replacing the native `<select>` with a custom listbox. The native control
  gives keyboard behavior, mobile pickers, and full option text on open for
  free, and none of that is worth rebuilding for a width bug.
- Shortening or truncating objective text anywhere it is stored, served, or
  displayed to a participant. The overflow is a presentation defect in one
  admin control; 3.01 objectives say what they say.
- Numbering the options ("1. Explain why…") as a way to dodge the width.
  Position is not stable — `move_objective` renumbers — and a stale number in a
  dropdown is worse than a long one.
- Any change to `ObjectivesPanel`'s coverage readout.

## Frontend tasks
1. `QuestionEditor.module.css`: add `.objectiveSelect`. It should fill the
   available row width rather than its content width, and never exceed its
   container — `max-width: 100%` plus a `min-width: 0` on the flex parent if
   the row is a flex container, since a flex item's default `min-width: auto`
   is what usually defeats `max-width` here. Add `text-overflow: ellipsis`,
   `overflow: hidden`, `white-space: nowrap` for the closed state.
2. `QuestionEditor.jsx`: swap `styles.kindSelect` for `styles.objectiveSelect`
   on the objective select only. Leave the Type select alone.
3. Check `.metaRow` — both selects sit inside it, and the label/control
   proportions that suit "Type" may not suit "Learning objective". If the row
   needs to become two lines at narrow widths, let it.
4. Look for the same pattern elsewhere before calling this done: any select
   whose options come from author-entered text rather than a fixed list. If
   there is none, say so in the changelog rather than leaving it unstated.

## Backend tasks
None. If a task here appears to need one, stop — this is a CSS class
assignment.

## Acceptance criteria
- On the lesson editor, an assessment question tagged to the longest objective
  in this repo's test data renders with the select fully inside the question
  panel
- The closed select ellipsizes rather than overflowing; opening it shows the
  full text of every option
- The Type select is visually unchanged
- Selecting an objective still marks the question dirty and still saves through
  the existing batched save
- Nothing regresses at a narrow viewport: no horizontal scrollbar on the page
- `npm run lint` passes
- `pytest` passes, unchanged

## Compliance
No COMPLIANCE.md row. This changes the width of one control in the admin tool.
It does not change what is disclosed to a participant, what is stored, or what
any locator requires. Confirm that against
`docs/2026-Statement-on-Standards-for-CPE-Programs.pdf` and say so explicitly
rather than leaving the section blank.

## When done
Append an entry to CHANGELOG.md and stop.
