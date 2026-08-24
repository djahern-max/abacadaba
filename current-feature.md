# Current Feature

## Feature 025, Evaluations

## Goal
Every participant is asked to evaluate the program on the dimensions the
Standards name, the results are stored, and an admin can review them.

## In scope
- An evaluation form covering the required dimensions
- Solicitation at the right moment, for every participant
- Storage, one evaluation per attempt
- An admin view with per-course aggregates and free-text comments

## Out of scope
- Instructor evaluation. There is no instructor in a self study program. See
  "The dimension that does not apply".
- Emailing a reminder to anyone who skips it.
- Public display of ratings. This is quality data for the sponsor, not social
  proof, and publishing it changes what people write.
- NPS, star ratings, or anything invented. The dimensions are enumerated in the
  Standards; use those.

## Read this before starting
4.04 and 4.04.1 govern this, with 4.04.2 covering what the sponsor does with the
results. Read them in `docs/2026-Statement-on-Standards-for-CPE-Programs.pdf`.

This is a small feature and it is mandatory, which is a combination worth
noticing: it is the cheapest remaining compliance requirement in the sequence and
it is the one most likely to be skipped because it feels like product polish. It
is not. 4.04 says sponsors **must** employ an effective means of evaluating
program quality and **must** provide a mechanism for participants to assess
whether learning objectives were met.

It also produces the first real signal on whether AI-drafted content is any good,
which is the actual thesis abacadaba exists to test. Read the results.

## The required dimensions
4.04.1 lists what evaluations determine, among other things:

1. whether stated learning objectives were met
2. whether stated prerequisite requirements were appropriate and sufficient
3. whether program materials, including the qualified assessment, were relevant
   and contributed to the achievement of the learning objectives
4. whether the time allotted to the learning activity was appropriate
5. whether instructors were effective, where applicable

Verify that list against the PDF rather than trusting this file. Note "among
other things" — the list is a floor, not a ceiling. One free-text field is a
reasonable addition and nothing more is needed.

Put the five in `app/constants/evaluation_dimensions.py` as ordered records
carrying a key, the participant-facing question text, and an
`applies_to_self_study` flag. Two copies of a list the Standards control will
drift; the same reasoning produced feature 020's `/meta/fields-of-study`
endpoint, and the same solution applies — serve the dimensions from the server so
the frontend never holds its own copy.

## The dimension that does not apply
Instructor effectiveness is qualified in the Standard itself with "where
applicable". A traditional self study program has no instructor — the definition
in Section 1 covers a human or technology-assisted teaching mechanism, and the
sponsor could argue the video narration qualifies, but asking a participant to
rate an instructor they never met produces noise, not quality data.

Do not render it for self study programs. Do not delete it from the constant
either: mark it `applies_to_self_study = False` and filter at serve time. When
superCPE runs a group program, the dimension is already there and already worded.

Record this in COMPLIANCE.md's Gap column against 4.04.1 as a deliberate
omission with the reasoning, not as an unmet requirement and not silently.

## Data model

New `evaluations` table:
- id
- attempt_id: FK attempts, ondelete CASCADE, **unique**, not null
- one integer column per applicable dimension, 1 to 5, CHECK constrained,
  nullable
- `comments`: text, nullable
- `submitted_at`

Keyed to the attempt, not to the course plus a viewer. The attempt is already the
completion record, it already resolves identity through both `user_id` and
`viewer_id`, and the unique constraint gives you one-evaluation-per-completion
for free rather than as application logic.

**Columns per dimension, not a rows-per-answer table.** A fixed list of five that
changes when NASBA revises the Standards is not an entity; it is a form. Five
integer columns aggregate with a single query and read plainly in a CSV export.
An `evaluation_answers` table would need a join and a pivot to answer "what is
the mean score for objectives met on this course", which is the only question
anyone will ask of it.

Nullable per dimension: a participant who answers four of five and submits has
given you four useful data points. Do not refuse the submission to protect the
shape of the data.

## Solicitation
The evaluation is offered on the result page, after the attempt completes,
whether the participant passed or failed. A failed participant's opinion of
whether the time allotted was appropriate is at least as informative as a passed
one's, and 4.04 says evaluations must be solicited from participants, not from
successful participants.

Offer it; do not gate anything on it. Blocking the certificate behind an
evaluation would make the responses worthless and is not something the Standards
ask for.

If an evaluation already exists for the attempt, show what was submitted rather
than the form again.

## Backend tasks
1. `app/models/evaluation.py`, plus the migration. Hand-add the five range CHECKs;
   autogenerate will not write them. Verify `downgrade -1`.
2. `app/constants/evaluation_dimensions.py` as described.
3. `app/services/evaluations.py`:
   - `submit(db, public_id, payload)` — refuses on an incomplete attempt, refuses
     a second submission for the same attempt with a conflict signal rather than
     an IntegrityError
   - `get_for_attempt(db, public_id)`
   - `course_summary(db, course_id)` — response count, response rate against
     completed attempts, and a mean per dimension. Aggregate SQL, one query.
4. `app/routers/evaluations.py`: `POST /attempts/{id}/evaluation`,
   `GET /attempts/{id}/evaluation`, and `GET /meta/evaluation-dimensions`
   unauthenticated so the form builds itself from the server.
5. `GET /admin/courses/{id}/evaluations` behind `require_admin`: the summary plus
   the comments, newest first.
6. Tests:
   - submitting on a completed attempt stores every dimension
   - submitting on an incomplete attempt is refused
   - a second submission for the same attempt is refused with a clean status, not
     a 500
   - a partial submission with three of five dimensions is accepted
   - a rating of 0 or 6 is refused
   - the instructor dimension is absent from the served dimension list
   - the course summary computes means over submitted values only, ignoring nulls
   - response rate counts completed attempts as the denominator

## Frontend tasks
1. An evaluation form on `Result`, below the certificate section, using the
   dimensions from `/meta/evaluation-dimensions`. A 1-to-5 scale with labelled
   ends, a comments textarea, one submit. Do not hand-code the five questions in
   JSX — that is the second copy of the list the constant exists to prevent.
2. A submitted state showing the responses back, so a reload does not look like
   the submission failed.
3. An admin evaluations view per course: response count and rate, a mean per
   dimension, and the comments. Flag a mean below 3 the way feature 012's stats
   page flags a question under 40 percent correct — reuse that treatment rather
   than inventing a second visual language for "look at this".
4. Link it from the admin course editor and the course list, next to the existing
   stats link.

## A thing to check rather than assume
4.04.2 requires sponsors to periodically review evaluation results and to inform
developers and instructors of them. This feature builds the view; it does not
build the periodic review or the notification.

Decide whether that is a gap worth a row in COMPLIANCE.md or a process the
sponsor performs outside the software, and say which. A defensible answer is that
review is a human obligation and the software's job is to make results available
— but state it rather than leaving it unaddressed, because "the admin can look at
it if they remember to" is exactly the kind of thing feature 026's dashboard
exists to stop relying on.

## Acceptance criteria
- `alembic upgrade head` creates the table with working range CHECKs;
  `downgrade -1` reverses
- completing an attempt, passed or failed, offers the evaluation
- the form renders four dimensions for a self study course, not five
- a submitted evaluation shows back on reload
- a second submission is refused cleanly
- the admin view shows response count, response rate, and a mean per dimension
- a course with no responses shows a plain message, not an empty table
- `npm run lint` passes
- pytest passes

## When done
Append an entry to CHANGELOG.md, including your conclusion on 4.04.2.

Then append to COMPLIANCE.md: rows for 4.04, 4.04.1, and 4.04.2. Quote the
Requirement column from the PDF. The 4.04.1 Gap column records the deliberate
omission of the instructor dimension and why.
