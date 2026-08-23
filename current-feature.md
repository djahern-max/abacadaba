# Current Feature

## Feature 022, Credit measurement

## Goal
A course knows how many CPE credits it is worth, how that number was arrived
at, and whether the number is still true. The arithmetic is visible in the
admin, disclosed to the participant before they enrol, and refuses to publish
when it is stale.

## In scope
- The word count formula and its all-video variant, as stored inputs plus a
  computed result
- A per-segment flag deciding whether that segment's runtime counts as A/V time
  or its words count as text
- Rounding to a legal increment
- Recomputation, staleness, and a publish rule
- The arithmetic rendered in the admin editor, and the credit disclosed on the
  public course page

## Out of scope
- Pilot testing (7.02.1 through 7.02.4). Method 1 is a separate path from the
  word count formula and abacadaba is not using it. Do not build a half version.
- Adaptive learning path averaging (7.02.6, second paragraph). No adaptive
  program exists.
- Splitting review from assessment questions. Feature 023. **This feature counts
  every question on a course, which is correct under the formula and must stay
  correct after 023 splits the type.** See the note in Backend task 4.
- Certificate content. Feature 024 consumes the credit this feature produces.
- Per-state non-technical credit caps. The technical/non-technical tag exists on
  the field of study constant from 020; nothing reads it yet and nothing should
  start here.

## Read this before starting
The formula is in Section 7 Paragraph 7.02.6, with the all-video variant in
7.02.7 and the rounding guidance in 7.01. Read all three in
`docs/2026-Statement-on-Standards-for-CPE-Programs.pdf` before writing any
code. Do not implement from the summary below; the summary exists to tell you
which paragraphs matter, not to replace them.

The general formula:

```
[(# of words / 180) + actual audio/video duration + (# of questions x 1.85)] / 50
```

The all-video variant, when the entire program is video and there is no text
learning material, drops the word term entirely.

Three things about that formula are easy to get wrong and expensive to get wrong
late:

1. **The A/V duration must be the real one.** Not an estimate, not a target
   length. `video/` already enforces this on its own side — `usingEstimates` in
   each lesson module flags any block still running on a word-count estimate,
   and `Root.tsx` warns. The app has no way to know whether the number in
   `lessons.duration_seconds` came from a measured render or a silent preview,
   so the only defence here is that the duration is auto-filled from the actual
   uploaded file rather than typed. Confirm feature 017's auto-fill is what
   populates it, and say so in the changelog.

2. **The question count includes review questions above the minimum, exercises,
   and qualified assessment questions.** All of them. A question you added
   because it was good, not because a floor required it, still counts. This is
   why the count must not become "assessment questions only" when 023 lands.

3. **Narration of the text is not additional learning.** If a segment's audio is
   somebody reading the on-screen text aloud, its runtime does not enter the
   formula — the words do instead. That is a per-segment editorial judgment and
   it needs somewhere to live.

## Data model

Add to `lessons`:
- `av_is_additional_learning`: bool, not null, default true. When true, this
  segment's `duration_seconds` enters the A/V term. When false, it does not, and
  `word_count` enters the word term instead.
- `word_count`: int, not null, default 0. The words of text learning material in
  this segment. For a pure video segment this is 0 and stays 0.

Add to `courses`:
- `credit_award`: numeric(4,1), nullable. The rounded, awardable credit.
- `credit_raw_minutes`: numeric(8,2), nullable. The numerator before dividing by
  50, kept because it is the number a reviewer will want to see.
- `credit_word_count`: int, nullable
- `credit_av_seconds`: int, nullable
- `credit_question_count`: int, nullable
- `credit_formula_version`: string, nullable
- `credit_computed_at`: timezone-aware timestamp, nullable

Store the inputs, not just the answer. On audit, "0.4 credits" is not a defence;
"0.4 credits from 486 seconds of A/V, 0 words, and 8 questions, under the 2026
7.02.6 formula, computed on this date" is. Six nullable columns is a cheap price
for that.

**Do not add a `credit_is_stale` boolean.** Staleness is derived, exactly as
019a derived collapsed-course mode and 021 derived review staleness:

```
stale = credit_computed_at is None or credit_computed_at < content_updated_at
```

`content_updated_at` already bumps on every participant-visible write through
`touch_content_invited_at`'s single choke point in `app/services/admin_content.py`
— read that function before assuming it covers the inputs this feature needs.
Duration and word count are lesson fields; the video upload route writes
directly and already calls the choke point. Verify rather than assume, and if
`av_is_additional_learning` or `word_count` can be written on a path that does
not bump, that is a bug in this feature, not an acceptable edge.

## The formula version constant
`CREDIT_FORMULA_VERSION = "2026-7.02.6"` in `app/constants/credit.py`, written
into `credit_formula_version` on every computation. NASBA revises the Standards;
a stored credit with no record of which formula produced it cannot be defended
or recomputed. When the constant changes, every course's credit is stale by
definition — make that fall out of a comparison in the staleness check rather
than requiring a data migration.

## Rounding
Section 7.01 permits self study credit to be awarded initially in one-fifth or
one-half increments, and — if one-fifth is awarded initially — in one-fifth
increments thereafter. Round **down**, per 7.02.6's closing sentence.

Implement one-fifth increments throughout: `floor(raw * 5) / 5`. That is the
finest legal granularity, it is uniformly applicable, and it never rounds up.

A raw credit below 0.2 is not awardable. Return 0.0 and let publish validation
produce the readable message; do not raise from the calculator.

Put a comment on the rounding function stating plainly that state boards differ
on acceptable increments and that superCPE will likely need a per-jurisdiction
policy. Do not build that policy here.

## Backend tasks
1. The two lesson columns and seven course columns, then
   `alembic revision --autogenerate -m "add credit measurement"`. Inspect it.
   Autogenerate handles added columns well; check the numeric precision survived.
   Verify `downgrade -1`.
2. `app/constants/credit.py`: `CREDIT_FORMULA_VERSION`, `MINUTES_PER_CREDIT = 50`,
   `WORDS_PER_MINUTE = 180`, `MINUTES_PER_QUESTION = 1.85`, `MIN_AWARDABLE = 0.2`.
   Named constants, not inline numerals. Every one of these is a number NASBA
   chose and can change.
3. `app/services/credit.py`, pure and read-only:
   - `compute(db, course_id) -> CreditBreakdown` — a dataclass carrying the
     inputs, the raw minutes, the raw credit, the rounded award, and the formula
     version. It reads; it does not write.
   - `round_down(raw) -> Decimal` as above.
   Use `Decimal`, not float, for anything that reaches a stored column. A credit
   of 0.30000000000000004 in an audit export is not a rounding curiosity, it is
   an error.
4. The question count is every question belonging to every published lesson of
   the course. `courses_service.published_question_count` already does this —
   reuse it. **Leave a comment at that call site saying the formula counts review
   and assessment questions alike, so that when feature 023 introduces the type
   split and the assessment starts serving a filtered subset, nobody
   "consistently" points this at the assessment-only count.** That is the single
   most likely way this feature silently breaks later.
5. A recompute path: `app/services/credit.py::store(db, course_id)` writing the
   seven columns and stamping `credit_computed_at`. Call it from an explicit
   admin action, not from every write. Recomputing inside every save means a
   course's credit changes while an author is mid-edit, and the staleness rule
   already tells them when to press the button.
6. `validate_for_publish` gains three rules, returning alongside all the others
   as one flat list (feature 017's checklist depends on that shape):
   - credit has been computed and is not stale
   - `credit_award >= 0.2`, with a message saying how many more minutes or
     questions would reach the next increment. An author who is 40 seconds short
     should be told that, not told "too short".
   - every published lesson with `av_is_additional_learning = true` has a
     non-null `duration_seconds`. You cannot count runtime you do not have.
7. `GET /admin/courses/{id}/credit` returning the full breakdown, and
   `POST /admin/courses/{id}/credit` to recompute and store. Behind the existing
   router-level `require_admin`.
8. `GET /courses/{slug}` gains `credit_award`. This is a pre-enrolment
   disclosure — a participant decides whether to take a program partly on how
   much credit it carries. If it is only in the admin API, this feature is not
   done, which is the same rule feature 020 applied to objectives.
9. Tests:
   - the all-video case: 486 seconds A/V, 0 words, 8 questions gives 0.4
   - the mixed case: a segment flagged narration-of-text contributes its words
     and not its runtime
   - rounding never rounds up: a raw 0.599 awards 0.4
   - a raw below 0.2 awards 0.0 and publish is refused with a readable message
   - editing a question bumps `content_updated_at` and the credit reads stale
   - recomputing clears staleness
   - publish is refused while stale
   - publish is refused when a counted segment has no duration
   - the public course payload carries the credit
   - the leak test still passes

## Frontend tasks
1. A Credit panel in `AdminCourseEditor` showing the arithmetic, not just the
   answer: a per-segment row with runtime, the additional-learning flag, and word
   count; then the question count; then the three terms, the sum, the division by
   50, the raw credit, and the rounded award. A reviewer should be able to check
   it by hand from what is on screen.
2. A stale state on that panel with a Recompute button, worded like 021's "this
   course has changed since it was reviewed" rather than as an error.
3. `LessonVideoFields` gains the additional-learning checkbox and the word count
   input, both joining the existing batched save. Label the checkbox with what it
   decides, not with the standard's wording — something closer to "This segment's
   audio teaches something the slides don't say" than "additional learning under
   7.02.7". The helper text can cite the paragraph.
4. `CourseDetail` shows the credit alongside program level and field of study, in
   the disclosure block feature 020 placed above the player.

## A thing to check rather than assume
Feature 021's `REVIEW_CHAIN_FIELDS` exclusion set exists so review fields do not
bump `content_updated_at`. The credit columns need the same treatment for the
same reason: storing a computed credit must not itself make the credit stale.
Add them to that exclusion set, and extend 021's `content_updated_at`-stability
test to PATCH the credit fields too — the changelog for 021 records that this
exact class of bug shipped once because the test only covered three of five
fields.

## Acceptance criteria
- `alembic upgrade head` adds all nine columns; `downgrade -1` reverses
- a course of one 486-second video and 8 questions computes and stores 0.4
- the admin panel shows every term of the arithmetic, and the numbers add up by
  hand
- editing any question, objective, lesson duration, or word count makes the
  credit read stale within the editor
- recomputing does not itself make the credit stale
- publish is refused while stale, and the checklist says so
- publish is refused below 0.2 with a message naming what would close the gap
- the public course page shows the credit to a signed-out visitor
- pytest passes, including the leak test and 021's staleness tests

## When done
Append an entry to CHANGELOG.md, including the answer to the auto-fill question
in "Read this before starting" point 1.

Then append to COMPLIANCE.md: rows for 7.01, 7.02.6, and 7.02.7. Quote the
Requirement column from the PDF. Expect the Gap column on 7.02.7 to record that
nothing in the application verifies the stored duration came from a measured
render rather than an estimated one — that guard lives in `video/`, outside the
app, and an author who types a number by hand can defeat it. Say that plainly
rather than implying the constraint is enforced end to end.
