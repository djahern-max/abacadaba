# Current Feature

## Feature 023, Review questions, assessment questions, and thresholds

## Goal
The application stops having one kind of question. Review questions reinforce
learning during the program and give feedback; the qualified assessment gates
credit and gives none until it is passed. Both floors derive from the course's
computed credit rather than from a hardcoded five.

## In scope
- A question type, with a backfill
- Review questions served at segment boundaries, with feedback
- The assessment serving assessment questions only
- A per-course pass threshold column, floored at 70 percent
- Credit-derived minimums for both kinds
- Removing per-question feedback from the assessment itself

## Out of scope
- Mid-video review cues. Real, and the honest reading of "throughout the
  program" — see "The placement gap this feature does not close". Not here; it
  touches the player, the heartbeat cadence, and the anti-skip rules in
  `app/services/watch.py` all at once and deserves its own feature.
- Question banks and randomised selection from a bank. The feedback rules in
  6.01.2 branch on whether a test bank exists, and this feature takes the
  no-test-bank branch throughout. Note where that branch is taken so the bank
  feature knows what to revisit.
- Simulations or other content reinforcement tools. The Standards permit them in
  lieu of review questions; nothing here should pretend to support them.
- Exercises as a distinct type. They count in the credit formula the same way
  questions do; a separate type buys nothing yet.

## Read this before starting
**Feature 022 must have shipped.** Both floors in this feature are per credit,
and a floor enforced against a credit that does not exist is a floor enforced
against zero. If 022 is not in, stop and say so rather than hardcoding a credit.

The governing paragraphs are 5.01.2.1 and 5.01.2.2 for review questions, and
6.01.2 for the qualified assessment. Read them in
`docs/2026-Statement-on-Standards-for-CPE-Programs.pdf`. Three rules in them are
counterintuitive enough to state up front:

- **Forced-choice responses are not permissible on the qualified assessment**,
  and true/false items do not count toward the review question minimum either.
- **Duplicate review and assessment questions are not allowed**, except in
  courses where recall of information is the learning strategy.
- **With no test bank, no feedback may be provided on a failed assessment.**
  Feedback on a passed one is optional and at the sponsor's discretion. There is
  no exception for feedback given question-by-question as the participant goes.

That third rule is the one that costs real work, because the application
currently breaks it. See Part 4.

## Part 1, the type

Add to `questions`:
- `kind`: string, not null, CHECK in `('review', 'assessment')`, default
  `'assessment'`.
- `feedback`: text, nullable. Shown after a review question is answered.

Backfill in the migration: `kind = 'review'` where `position <= 3`, else
`'assessment'`. That is the convention both seed scripts in `backend/scripts/`
were written to, precisely so this migration would be a `WHERE` clause and not a
judgment call. Read the header comment in `seed_asc606_construction_intro.sql`
before writing it — it says so explicitly.

Confirm the convention actually holds in the database before relying on it. If
any lesson has questions that do not follow it, the backfill is wrong for that
lesson and you should say which, not quietly mis-type them.

Add to `courses`:
- `pass_ratio`: numeric(3,2), not null, default 0.70, CHECK `>= 0.70 AND <= 1.00`.

The floor is in the constraint, not only in validation. 6.01.2 sets 70 percent
as a minimum for the qualified assessment; a sponsor may be stricter and may not
be laxer, and a CHECK is the cheapest way to make the laxer case unrepresentable.

## Part 2, what the assessment serves

`app/services/quiz.py` currently builds a course's quiz from every question of
every published lesson. It now filters to `kind = 'assessment'`, still ordered by
lesson position then question position, still shuffled per attempt from
`shuffle_seed`. Nothing about feature 012's shuffle changes.

`app/services/attempts.py::_pass_threshold` currently reads a module-level
`PASS_RATIO` and applies it to `courses_service.published_question_count`, which
counts everything. Both halves are now wrong:

- the ratio comes from `course.pass_ratio`
- the denominator is the count of **assessment questions only**

Get one of those and not the other and you ship a course whose pass mark is
computed partly off questions that legally cannot count toward it. Change them
in the same commit and test the boundary.

Delete the `PASS_RATIO` module constant outright. Leaving it as a default that
nothing reads is how it comes back.

**Do not point feature 022's credit calculation at the filtered count.** The
formula counts review questions, exercises, and assessment questions alike. 022
left a comment at that call site warning about exactly this. Read it, leave it
there, and add a test asserting the credit for a course is unchanged by the type
split.

## Part 3, review questions and where they are served

Review questions are served at the end of the segment they belong to, once that
segment's watch gate is met, before the participant moves to the next one. The
data model already implies this shape: questions belong to lessons, lessons are
ordered within a course. That is an interval structure you got for free in 019
and have not used.

New `review_responses` table:
- id, question_id (FK, ondelete CASCADE, indexed)
- viewer_id (UUID, not null, indexed), user_id (FK users, nullable, indexed,
  SET NULL) — the same identity pair `watch_progress` uses
- choice_id (FK, ondelete CASCADE), is_correct (bool), answered_at

**This table must not touch `attempts`.** Review questions carry no minimum
passing rate and no bearing on credit; recording them against the credit-bearing
attempt is how they end up in a score. Resolve identity the way feature 015
resolved it for `watch_progress` — read that function rather than writing a
second one, and carry its leak test forward: two users, one browser, no
cross-contamination.

Endpoints:
- `GET /courses/{slug}/lessons/{lessonSlug}/review` — the segment's review
  questions and their choices. `is_correct` appears nowhere in this payload; the
  feature 015 leak test covers the whole public surface and must keep passing.
- `POST /courses/{slug}/lessons/{lessonSlug}/review/{question_id}` — takes a
  choice, returns correct or incorrect plus the question's `feedback`.

Grade on submit. Do not ship the answer key with the question and grade in the
browser; that is the feature 005 hole, and feature 006's replay test exists
because it was already made once here.

5.01.2.2 sets the feedback minimum at indicating correct or incorrect, with the
goal of reinforcing understanding, highlighting knowledge gaps, and pointing at
resources. The verdict is therefore mandatory and the `feedback` text is
optional. Render the verdict always; render the text when present.

Re-answering a review question is allowed and overwrites. There is no score to
protect.

## Part 4, the assessment stops giving feedback

`AttemptAnswerResponse` currently returns `correct` and `correct_choice_id` on
every answer during an attempt. Under 6.01.2, with no test bank, feedback on a
failed assessment is not permitted — and the application cannot know whether an
attempt will pass while it is still in progress, so per-question feedback during
the assessment is feedback on a failed assessment roughly half the time.

Change it:
- during an attempt, an answer response carries the answered count and the
  question count, and nothing about correctness
- on completion, the result page shows the score and pass or fail
- on a **pass**, per-question correctness may be shown, at the sponsor's
  discretion. Show it; it is the more useful product and it is permitted.
- on a **fail**, show the score and nothing else. No per-question breakdown, no
  correct answers, no "you missed question 3".

Check the Quiz page, the Result page, and any per-question review view for
places that assume correctness is available mid-attempt. Feature 020a found the
same class of bug in question numbering by taking the quiz in a browser rather
than by reading a diff; do that here too.

Leave a comment at the branch saying it is the no-test-bank arm of 6.01.2 and
that a bank feature would revisit it.

## Part 5, the floors

5.01.2.1 and 6.01.2 each carry a chart keyed to one-fifth credit increments:

| Credit | Review questions | Assessment questions |
| --- | --- | --- |
| 0.2 | 0 | 2 |
| 0.4 | 1 | 3 |
| 0.5 | 2 | 4 |
| 0.6 | 2 | 4 |
| 0.8 | 3 | 5 |
| 1.0 | 3 | 5 |

Transcribe both charts into `app/constants/question_minimums.py` from the PDF,
not from this file. Above one full credit, the Standards require the per-credit
minimum plus additional questions per the chart for each remaining one-fifth
increment. Implement that as:

```
whole, remainder = divmod(credit, 1)
required = whole * PER_CREDIT + CHART[remainder]
```

**That decomposition is an interpretation.** It is a reasonable one and it
matches the worked example in 6.01.2 for a 5½ credit course, but it is a reading
of prose, not a quoted rule. Say so in a comment, verify it against that worked
example as a test, and record it in COMPLIANCE.md's Gap column as an
interpretation rather than a citation.

Two counting rules on top:
- A question with exactly two choices does not count toward the review minimum
  (true/false items do not count under 5.01.2.1).
- An assessment question must have at least three choices. Forced-choice
  responses are not permissible on the qualified assessment, and two choices is
  the shape that makes them possible. `MIN_CHOICES_PER_QUESTION = 2` stays as the
  global floor from feature 010; the assessment rule is stricter and sits beside
  it.

Publish validation gains: enough review questions, enough assessment questions,
every assessment question has at least three choices, and no exact duplicate
prompt between a review and an assessment question in the same course. Normalise
whitespace and case for that comparison. Near-duplicates are the reviewer's job
under 021 and this must not pretend otherwise — say so in the message.

All of these join the existing flat list of failures; feature 017's checklist
depends on getting every failure at once.

## The placement gap this feature does not close
5.01.2.1 requires review questions to be placed throughout the program in
sufficient intervals to let a participant evaluate what needs re-studying.
Segment-boundary placement satisfies that for a multi-segment course. It cannot
satisfy it for a **one-lesson course**, which has exactly one seam and that seam
is the end — there is no "throughout" in a program with one segment.

That collides directly with feature 019a's collapsed single-lesson editor, which
was built to make a one-video course the easy path.

Record it in COMPLIANCE.md's Gap column against 5.01.2.1, explicitly, with the
mitigation: multi-segment courses are compliant, one-segment courses above the
0.2-credit tier are not, and mid-video cues are the real fix. Do not write a Gap
entry that implies placement is handled. This is exactly the kind of thing
abacadaba exists to find before superCPE has an audit.

Consider a publish warning — not a refusal — on a one-lesson course carrying more
than 0.2 credits. A refusal here would block the platform's own demo content;
a warning names the problem where the author can see it.

## Backend tasks
1. The columns, the new table, and the backfill migration. Hand-add both CHECK
   constraints; autogenerate will not write them. Verify `downgrade -1`.
2. `app/constants/question_minimums.py`, transcribed from the PDF.
3. `app/services/quiz.py`: filter to assessment questions.
4. `app/services/attempts.py`: the threshold from the course column against the
   assessment count; correctness stripped from the in-attempt response; the
   result payload branching on pass.
5. `app/services/review.py`: serve, grade, record. Identity resolution reused
   from feature 015, not rewritten.
6. `app/routers/review.py`, plus the type and feedback fields on the admin
   question payloads.
7. `validate_for_publish`: the five new rules above.
8. Tests:
   - the backfill types the seeded courses as 3 review and 5 assessment per lesson
   - the assessment serves assessment questions only
   - the pass mark is the course's ratio applied to the assessment count, checked
     at the boundary
   - an in-progress answer response carries no correctness
   - a failed result exposes no per-question correctness anywhere in the payload
   - a passed result may
   - a review answer returns a verdict and feedback and writes no attempt row
   - user A's review responses are invisible to user B sharing a browser
   - the floors refuse publish at 0.4 credits with 2 review and 2 assessment
     questions, naming both shortfalls in one response
   - a two-choice assessment question refuses publish
   - a two-choice review question is allowed but does not count toward the floor
   - the 5½ credit worked example from 6.01.2 requires 29 assessment questions
   - the credit computed by feature 022 is unchanged by the type split
   - the leak test still passes

## Frontend tasks
1. `QuestionsEditor` gains a review/assessment control per question and a
   feedback textarea shown only for review questions. Both join the batched save.
   Group the list by type rather than interleaving — an author needs to see the
   two sets as two sets.
2. A review panel on `LessonSegment`, appearing once that segment's watch gate
   closes. Reuse the gate state already on that page; do not fetch it twice.
3. `Quiz` stops rendering per-answer correctness.
4. `Result` branches on pass for the per-question breakdown, and on a fail says
   plainly that the answers cannot be shown, rather than showing an empty area.
5. A pass threshold input on the course details form, with helper text stating
   the 70 percent floor and that it cannot be set lower.

## A thing to check rather than assume
Feature 019 set `PASS_RATIO = 0.8` and its acceptance criteria included passing a
fifteen-question course at 12 of 15. Those tests exist and will break. They
should break — but check each one before changing it, because a test that breaks
for the right reason and a test that breaks because the new threshold is wrong
look identical from the failure line.

## Acceptance criteria
- `alembic upgrade head` adds the columns and table and backfills the type;
  `downgrade -1` reverses on a database with rows
- a two-lesson course serves three review questions after segment one, three
  after segment two, and a ten-question assessment at the end
- a review answer returns correct or incorrect plus feedback, immediately
- taking the assessment in a browser shows no correctness until the end
- failing shows a score and no answers; passing shows the breakdown
- the pass mark is 70 percent of the assessment questions, not 80 percent of all
  questions
- publishing a 0.4-credit course with too few of either kind is refused, and the
  checklist names both
- publishing an assessment question with two choices is refused
- the course credit from feature 022 is the same before and after this feature
- `npm run lint` passes
- pytest passes, including the leak test and feature 015's cross-user test

## When done
Append an entry to CHANGELOG.md, including which questions the backfill typed as
review and whether the position convention held in the real database.

Then append to COMPLIANCE.md: rows for 5.01.2, 5.01.2.1, 5.01.2.2, and 6.01.2.
Quote the Requirement column from the PDF. Three Gap entries are expected and
none of them should be softened — the one-lesson placement gap, the
above-one-credit chart decomposition as an interpretation, and the fact that the
duplicate check catches exact matches only.
