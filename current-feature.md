# Current Feature

## Feature 023a, Question feedback, objective coverage, and assessment integrity

## Goal
A question carries the two things 023 left it unable to carry: the feedback a
participant reads after answering, and the learning objective it tests. Publish
enforces objective coverage and the per-one-fifth question minimums the
Standards actually specify. And the qualified assessment stops giving away
feedback it is not permitted to give.

## Why this is a separate feature
023 split the question type and made the pass threshold a column. Both were
correct and both shipped. This file exists because authoring a real course
against 023's schema — see "The fixture" below — surfaced three things the
schema cannot express, and one thing the quiz UI does that the Standards do not
allow.

None of it is a defect in 023. 023 built what it scoped. This builds the rest.

## In scope
- `feedback` on a question, and rendering it where it is permitted
- `objective_id` on a question, and the 75% coverage rule it makes checkable
- The two per-one-fifth minimum charts as lookup data, replacing any flat
  per-credit floor
- The assessment feedback restriction: no feedback on a failed assessment
- Extending the leak test, because feedback text is a new way to leak an answer

## Out of scope
- `question_type` and `pass_threshold`. 023 shipped both. Do not touch them
  beyond reading them.
- Test banks and randomized question generators. 6.01.2 offers these as an
  alternative path to the 75% coverage rule and as a relaxation of the feedback
  restriction. Neither exists, and building half a test bank to dodge a rule
  that is easy to satisfy directly is the wrong trade. See "The test bank
  question" below — it changes what this feature builds, so read it before
  deciding it is irrelevant.
- Simulations, essays, matching, and rank-order items. 5.01.2 and 6.01.2 permit
  "other content reinforcement tools" and varied assessment formats. abacadaba
  has multiple choice. Adding a format means a new answer model, a new grader,
  and a new leak surface; it is its own feature and there is no content asking
  for it.
- Per-lesson objectives. 020 decided objectives attach to the course and the
  reasoning has not changed. `objective_id` points at a course-level objective
  from a question that lives on a lesson — that crosses a level deliberately,
  and it is fine, because a question tests a program objective regardless of
  which segment it sits in.
- Certificates (024), evaluations (025), policies and the overdue-review
  dashboard (026).

## The locators this feature is built against
Read these in `docs/2026-Statement-on-Standards-for-CPE-Programs.pdf` before
starting. Quote them into COMPLIANCE.md in the Standard's own words; do not work
from the summary below, which exists to say which paragraphs matter.

- **5.01.2.1** — at least three review questions or other content reinforcement
  tools with scored responses per CPE credit; two if marketed for one-half
  credit; none required at one-fifth. After the first one-fifth, required counts
  follow a per-increment chart. "True or false" questions do not count toward
  the required number. No minimum passing rate on review questions.
- **5.01.2.2** — feedback must be provided on review questions. **At a minimum,
  feedback must indicate that a response was "correct" or "incorrect."** The
  stated goal is to reinforce understanding, highlight knowledge gaps, and
  provide additional resources for comprehension.
- **6.01.2** — qualified assessment, minimum passing grade of at least 70
  percent; at least 5 questions and scored responses per CPE credit, following a
  per-increment chart below a full credit; duplicate review and assessment
  questions not allowed except where recall is the learning strategy; forced
  choice ("true or false", "yes or no") not permissible on the assessment; the
  assessment must measure **75 percent or more of the learning objectives** for
  the program; and — the paragraph 023 had no reason to read — the feedback
  rules at 6.01.2 sub-ii, which govern when assessment feedback may be given
  at all.

**Read 5.01.2.2 and 6.01.2 sub-ii side by side before writing any UI.** They
point in opposite directions on purpose. Review questions must give feedback.
The assessment may be forbidden from giving it. A single quiz component that
treats both the same is wrong for one of them.

## The finding that motivates the assessment work
6.01.2 sub-ii b says that where a sponsor does not use a test bank, whether
feedback can be given depends on whether the participant passed:

- on a **failed** assessment, the sponsor **may not** provide feedback
- on a **passed** assessment, the sponsor may

Feature 005 built the quiz to reveal the correct choice in green immediately
after each wrong answer, and to fire confetti immediately after each correct
one. That is per-question feedback delivered before pass or fail is known, which
means a participant who goes on to fail has already received it.

abacadaba has no test bank, so the restrictive path is the one that applies.

**The confetti is feedback.** A burst on correct and nothing on incorrect
communicates correct-or-incorrect as clearly as any text does. Do not reason
around this on the grounds that it is decorative. It is the product's
personality and it is also, on the qualified assessment, a signal the Standards
do not permit before a pass.

The resolution, which keeps the personality where it is legal:

- **Review questions** keep everything. Immediate reveal, immediate confetti,
  the feedback paragraph. This is exactly what 5.01.2.2 asks for and review
  questions have no passing rate to protect.
- **Assessment questions** defer all of it. No reveal, no per-answer confetti,
  no feedback text during the attempt. The result screen shows the score and
  pass/fail. On a **pass**, it then shows per-question feedback and the big
  confetti. On a **fail**, it shows the score and nothing else.

That is a real product change and it should be stated plainly in the changelog
rather than slipped in. A participant who fails learns that they failed and by
how much, and is told to re-study — which is what the Standard intends.

## The test bank question
If a sponsor uses a test bank of sufficient size to minimize question overlap
for a repeat test taker, 6.01.2 sub-ii a permits feedback on the assessment
regardless of outcome, and the 75% objective coverage rule may be satisfied by
the bank rather than by any single served assessment.

abacadaba does not have one, and this feature does not build one. But the choice
is worth recording: a test bank is the more permissive design and superCPE will
probably want it, because retakes against a fixed ten-question assessment are a
memorization exercise. Build the restrictive version now — it is correct without
a bank, and a bank added later relaxes rules rather than reworking them.

Put a comment to that effect on the feedback-gating logic.

## Data model
Two columns on `questions`:

- `feedback`: `Text`, nullable. The explanation shown after answering. Nullable
  because assessment questions may legitimately have none, and because a
  question mid-authoring has none.
- `objective_id`: FK to `learning_objectives.id`, nullable, indexed,
  **`ondelete SET NULL`**.

**`SET NULL`, not `CASCADE`.** Everywhere else in this schema a child row
cascades from its parent, so autogenerate and habit will both push toward
`CASCADE` here. It is wrong. Deleting a learning objective would delete every
question that tested it — silently destroying authored content as a side effect
of editing a course's objectives. The question survives its objective and
becomes untagged, which publish validation then reports.

`objective_id` is nullable and stays nullable. Review questions are not required
to be tagged; only the assessment's coverage is regulated.

No new tables. No change to `choices`, `attempts`, or `attempt_answers`.

## The minimum charts
5.01.2.1 and 6.01.2 each specify a per-one-fifth chart, not a flat per-credit
floor. Both read the same way: the chart gives the requirement up to the first
full credit, and after a full credit the chart's increments are added on top of
the base minimum.

| Credit | Review (5.01.2.1) | Assessment (6.01.2) |
| --- | --- | --- |
| 0.2 | 0 | 2 |
| 0.4 | 1 | 3 |
| 0.5 | 2 | 4 |
| 0.6 | 2 | 4 |
| 0.8 | 3 | 5 |
| 1.0 | 3 | 5 |

Transcribe these from the PDF, not from this table. This table is here to tell
you the shape of the thing you are transcribing.

Put them in `app/constants/question_minimums.py` as data — a mapping keyed by
`Decimal` credit, plus the per-credit base (3 review, 5 assessment) and the
addition rule above a full credit. Not inline branching. These are numbers NASBA
chose, they differ between the two charts, and they changed between the 2024 and
2026 Standards; the crosswalk says so explicitly for the assessment chart.

Worked example, because the addition rule is the part that gets implemented
wrong: a **1.2 credit** course needs 5 + 2 = **7** assessment questions and
3 + 0 = **3** review questions.

If 023 implemented a flat "3 review and 5 assessment per credit" floor, replace
it with these charts. A flat floor is wrong in both directions — it demands 5
assessment questions of a 0.4-credit course that needs 3, and lets a 1.2-credit
course pass with 5 when it needs 7.

## The fixture
Use the hazardous waste course as the worked example throughout, in the tests
and in the acceptance criteria. It is real content, it was authored against the
Standards rather than against the schema, and it is what surfaced every gap in
this file.

- 5 lessons, 5 course-level learning objectives, one objective per lesson
- Questions per lesson: 4 / 3 / 3 / 3 / 2, totalling 15
- Position 1 in every lesson is the review question; the rest are assessment
- 5 review, 10 assessment
- Assessment questions tag objectives 1,1,1 / 2,2 / 3,3 / 4,4 / 5 — all five
  objectives covered, which is 100% against a 75% requirement
- `pass_threshold` 0.70, the 6.01.2 floor, exercising 023's column rather than
  sitting on the default
- Every question has feedback written
- All video, so credit comes from 7.02.7's variant

**Note the positional boundary.** `seed_asc606_construction_intro.sql` documents
"position <= 3 means review" so that 023's migration could be a `WHERE` clause.
This course's boundary is position 1. If 023's migration used that constant,
confirm it was applied only to the ASC 606 rows and not left as a live rule.

The credit lands at either 1.0 or 1.2 depending on final runtime — the scripts
run 700-850 words each and `video/` measures roughly 130 wpm, so five segments
land between 27 and 33 minutes against a 27.75-minute question term. **Assert
the minimums hold at both**, in one test with two parameters. A fixture that
only passes at the credit you expected is not testing the chart.

## Backend tasks
1. The two columns, then `alembic revision --autogenerate -m "add question
   feedback and objective tag"`. Inspect it. **Autogenerate will almost
   certainly write `CASCADE` on the new FK** — change it to `SET NULL` by hand
   and say why in the migration docstring. Verify `downgrade -1`.
2. `app/constants/question_minimums.py`, per "The minimum charts" above.
3. `app/services/` — a coverage helper: given a course, the set of objective ids
   its assessment questions reference, and the ratio against the course's total
   objectives. Pure and read-only, alongside `credit.py`'s shape.
4. `validate_for_publish` gains four rules, returning in the same flat list as
   every other rule — 017's checklist depends on that shape and 020, 021, and
   022 each confirmed it holds:
   - every review question has non-blank feedback (5.01.2.2)
   - assessment questions reference at least 75% of the course's objectives,
     with a message **naming the uncovered objectives by their text**, not
     reporting a percentage. An author who is one objective short should be told
     which one.
   - review count meets the 5.01.2.1 chart for the course's computed credit
   - assessment count meets the 6.01.2 chart for the same
   The last two read `credit_award`, which 022 already refuses to publish while
   stale — so these rules inherit that guarantee and must not re-derive credit
   themselves.
5. If 023 did not already do it: refuse publish when a review question and an
   assessment question on the same course share a prompt (6.01.2's duplicate
   rule). Check before building; this may already exist.
6. `touch_content_updated_at` must fire on writes to both new columns. `feedback`
   is participant-visible content. `objective_id` changes what the assessment
   measures, which changes whether the course satisfies 6.01.2 — arguably more
   review-worthy than editing a prompt. Neither goes in `REVIEW_CHAIN_FIELDS`.
7. **The leak surface.** `QuestionPublic` must not carry `feedback` on an
   assessment question served during an attempt. Feedback text routinely states
   the answer — "a pH of 1.4 falls below the corrosivity threshold of 2.0"
   identifies the correct choice as surely as `is_correct` does. Follow 004's
   precedent exactly: a separate schema class that does not define the field at
   all, rather than excluding it at serialization. Review questions may carry it.
8. Result-screen feedback: a payload on `GET /attempts/{id}/result` carrying
   per-question feedback **only when the attempt passed**. On a fail it carries
   the score and nothing per-question.
9. Tests, against the fixture:
   - a 1.0-credit course with 5 review and 10 assessment questions publishes
   - the same course at 1.2 credit still publishes (the chart's addition rule)
   - a 0.4-credit course publishes with 1 review and 3 assessment questions —
     the case a flat per-credit floor gets wrong
   - a 1.2-credit course with 6 assessment questions is refused, naming 7
   - dropping the objective-5 assessment question takes coverage to 4/5 = 80%
     and still publishes; dropping objective 4 as well takes it to 60% and is
     refused, naming both uncovered objectives
   - a review question with blank feedback is refused
   - deleting a learning objective leaves its questions in place with
     `objective_id` null, and publish then reports the coverage failure
   - editing feedback bumps `content_updated_at`; so does retagging an objective
   - **the assessment payload contains no `feedback` field at all** — extend the
     004/015 leak test rather than writing a second one
   - a failed attempt's result carries no per-question feedback
   - a passed attempt's result carries it

## Frontend tasks
1. `QuestionEditor` gains a feedback textarea, and — on assessment questions
   only — an objective select populated from the course's own objectives. A
   question editor on a lesson page needs the course's objectives, which it does
   not currently have; check how `CoursePublishPanel`'s lesson lookup solved the
   same shape rather than inventing a second path.
2. An objective coverage readout. It belongs in `ObjectivesPanel`, beside the
   objectives themselves — a per-objective indicator of how many assessment
   questions test it, so an untested objective is visible where an author is
   already looking. This is 021's stale-review lesson applied again: state the
   problem where the author is, not only in the publish checklist.
3. The quiz split. Review questions: immediate reveal, per-answer confetti, and
   the feedback paragraph. Assessment questions: none of it. The component
   branches on `question_type`, which 023 already put on the payload.
4. The result screen: score and pass/fail always; per-question feedback and the
   big confetti only on a pass.
5. Verify the publish checklist picks up all four new rules through its existing
   `publishErrors` list without a second surface. 020, 021, and 022 each checked
   this and it held each time; check it again rather than assuming a fourth.

## A thing to check rather than assume
**This file was written without seeing 023's shipped code.** Read
`current-feature_23.md` and 023's changelog entry first, and reconcile:

- Did 023 use a flat per-credit floor or the per-increment charts? If the
  charts, task 2 is already done — delete it from this file rather than
  building it twice.
- Is `question_type` in an `app/constants/` module, per 020's fields-of-study
  precedent? If it is a bare string literal, this feature is the cheap moment to
  move it, since it is already touching the same table.
- Did 023 implement the duplicate-prompt rule? Task 5 depends on the answer.
- Did 023 conflate the two true/false rules? They differ: 6.01.2 makes forced
  choice **impermissible** on the assessment, while 5.01.2.1 merely says such
  questions **do not count toward** the required review minimum — they are
  allowed, they just do not satisfy the floor. If 023 banned them outright on
  review questions, that is stricter than the Standard and should be relaxed;
  if it counted them toward the review minimum, that is wrong and this feature
  fixes it.

If any of the above makes a task here redundant, say so explicitly in the
summary rather than silently skipping it.

## Acceptance criteria
- `alembic upgrade head` adds both columns; the FK is `SET NULL`; `downgrade -1`
  reverses cleanly
- deleting a learning objective leaves its questions in place, untagged
- the hazardous waste fixture publishes at 1.0 credit and at 1.2 credit
- a 0.4-credit course publishes with 1 review and 3 assessment questions
- a coverage failure names the uncovered objectives by text, not by percentage
- a review question with no feedback blocks publish, and the checklist says which
- an assessment question's feedback appears nowhere in any payload served during
  an attempt
- a failed attempt shows a score and no feedback; a passed attempt shows both
- no per-answer confetti fires on an assessment question
- per-answer confetti still fires on a review question
- the objective panel shows which objectives no assessment question tests
- `npm run lint` passes
- pytest passes

## When done
Append an entry to CHANGELOG.md. State plainly that assessment feedback timing
changed and why, since it is a visible product change and not only a schema one.

Append to COMPLIANCE.md: 5.01.2.1, 5.01.2.2, and 6.01.2. If 023 already wrote
rows for 5.01.2.1 or 6.01.2, **append new rows rather than editing theirs** —
the file is append-only — and note in the new row's Gap column what the earlier
row no longer describes accurately.

The Gap column should carry, at minimum: that no test bank exists and the
restrictive 6.01.2 sub-ii b feedback path is therefore the one implemented;
that "other content reinforcement tools" are not supported, so only multiple
choice can satisfy the review minimum; and that objective tagging is an
author's assertion that a question tests an objective, which nothing validates
beyond its presence.
