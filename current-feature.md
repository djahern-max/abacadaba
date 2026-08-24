# Current Feature

## Feature 026, Policies, disclosures, and content currency

## Goal
The policies a sponsor is required to formalise, publish, and make available
exist as real pages a participant can read before registering. And the review
obligations that features 021 and 024 recorded but did not enforce become
something the sponsor is actually told about.

## In scope
- Refund, cancellation, complaint resolution, and records retention as published
  policy pages
- Program expiration dates for self study programs
- An overdue-review dashboard
- The published-but-edited state feature 021 deliberately left open

## Out of scope
- A draft-and-version model for courses. It is the real fix for the
  published-but-edited problem and it is a large feature. This one reports the
  state; it does not solve it.
- Emailing anyone about anything overdue.
- Legal drafting. The application stores and publishes policy text; a human
  writes it. Do not ship invented refund terms as seed data — see below.
- A complaint intake workflow. Publishing the resolution policy is the
  requirement; a ticketing system is not.

## Read this before starting
The disclosure requirements are in 8.01.1, which feature 020 already partly
satisfied and whose COMPLIANCE.md row already carries a Gap entry saying refund,
cancellation, and complaint resolution policies are not published anywhere. Read
that row before starting — this feature closes it, and the row should be updated
rather than duplicated.

Expiration dates for self study and nano learning are at 9.02.2. Records
retention is in Section 9; feature 024 was told to find the retention period and
put it in a constant, so read that constant rather than looking it up twice. If
024 did not record it, find it now and say so.

The currency requirement is 4.01: courses in subjects that undergo frequent
change must be reviewed by a subject matter expert at least once a year, others
at least every two years. Feature 021 stored `reviewed_at` and `review_cycle`
and stated explicitly that it does not check whether a course has actually been
re-reviewed inside its window — that enforcement is this feature, by design.

## Part 1, policies as data

New `policies` table:
- id, `slug` (unique, indexed), `title`, `body` (text, markdown), `updated_at`

Four seeded slugs: `refund-and-cancellation`, `complaint-resolution`,
`records-retention`, `program-cancellation`. Editable in the admin, rendered at
`/policies/{slug}`, linked from the site footer and from the course detail page's
disclosure block.

**Rows, not hardcoded JSX.** Three reasons, in order of importance: the text
changes without a deploy; `updated_at` is itself the evidence that the policy was
published as of a date, which is what "formalized and published" needs to be
demonstrable; and a sponsor who is not the person who runs `git push` can
maintain it.

**Seed the rows with an explicit placeholder, not with plausible policy text.**
Something that reads as unmistakably unwritten — `This policy has not been
written yet.` — and a publish rule that refuses any course while any of the four
is still placeholder. Seeding invented refund terms would produce an application
that looks compliant, publishes courses, and has published nothing anyone wrote.
That failure mode is worse than an empty page, because nobody goes looking for
it.

Markdown, rendered server-side or with an existing small renderer. Do not add a
rich text editor.

## Part 2, program expiration

Add to `courses`:
- `expires_on`: date, nullable

9.02.2 requires self study programs to carry an expiration date. Disclose it on
the course detail page alongside the credit and the last-reviewed date, refuse to
publish without it, and refuse to start an attempt on an expired course with a
clear message rather than a 404 — a participant who bookmarked it deserves to
know why, and "not found" is a lie.

An expired course should stop listing publicly but should not be force-unpublished
by a background job. That is the same reasoning feature 021 applied to
published-but-edited courses: pulling a program out from under someone partway
through is worse than the alternative. Let it stay reachable, gate new attempts,
and surface it on the dashboard.

Decide the default window from 9.02.2 rather than inventing one, and default the
field from `reviewed_at` plus that window when a review is recorded — an author
who has to type a date will eventually type a wrong one.

## Part 3, the currency dashboard

`GET /admin/currency`, one page, four sections. All read-only, all derived from
columns that already exist:

1. **Overdue review.** `reviewed_at + cycle window < now`, where the window is one
   year for `annual` and two for `biennial`. Feature 021's `review_cycle` column
   is what makes this a comparison rather than a judgment.
2. **Due soon.** The same, within 60 days. An annual review that surfaces the day
   it lapses has already lapsed.
3. **Published but edited.** `is_published AND content_updated_at > reviewed_at`.
   This is the gap 021 recorded in COMPLIANCE.md against 4.02: a published course
   can serve edited, unreviewed content until someone gets to it, and the stated
   mitigation was that 026 would report on it. This section is that mitigation.
   If it does not exist when this feature ships, 021's Gap entry becomes a false
   statement and should be corrected rather than left standing.
4. **Expired or expiring.** `expires_on` past or within 60 days.

A course appears in more than one section when it qualifies for more than one.
Do not collapse them into a single worst-status column; a course that is both
overdue for review and expiring needs both facts stated.

Sort each section by how overdue, worst first — the same convention feature 012's
question stats used for worst-performing questions. Reuse that page's table
treatment rather than designing a second one.

Link it from the admin nav, not from inside a course. It is a cross-course view
and burying it inside one course is how it stops being looked at.

## Backend tasks
1. `app/models/policy.py` and `expires_on` on `Course`. Migration, with the four
   policy rows inserted as placeholders in the same migration so a fresh database
   has them. Verify `downgrade -1`.
2. `app/services/policies.py`: get by slug, list, update. `is_placeholder` derived
   by comparing against the seeded constant, not stored as a flag — the same
   derived-not-stored rule 019a set and 022 followed.
3. `app/services/currency.py`: the four queries above, aggregate SQL, read-only.
4. `app/routers/policies.py`: `GET /policies` and `GET /policies/{slug}`,
   unauthenticated. `PATCH /admin/policies/{slug}` behind `require_admin`.
5. `GET /admin/currency` behind `require_admin`.
6. `validate_for_publish` gains two rules: `expires_on` is set, and no policy is
   still placeholder. The second is a site-wide condition surfacing in a
   course-level checklist, which is unusual — word the message so the author
   knows it is not something wrong with their course, and link to the policies
   admin.
7. `start_attempt` refuses an expired course with a clear message. Check the order
   of the guards: feature 019 established authenticate, then gate, then policy.
   Expiry is a property of the course, not of the participant, so it goes first —
   telling someone how much video is left on a program they cannot take is worse
   than useless.
8. Tests:
   - publish is refused while any policy is placeholder, and the message says
     which
   - editing a policy clears that refusal for every course at once
   - publish is refused without an expiration date
   - starting an attempt on an expired course is refused with a readable reason,
     not a 404
   - an annual course reviewed 13 months ago appears as overdue; one reviewed 6
     months ago does not
   - a biennial course reviewed 13 months ago does not appear as overdue
   - a published course edited after its review appears in the published-but-edited
     section
   - a course appears in two sections when it qualifies for two
   - the policy pages render for a signed-out visitor

## Frontend tasks
1. `/policies/{slug}` pages, and a footer linking all four site-wide.
2. Links to the refund, cancellation, and complaint policies in `CourseDetail`'s
   disclosure block, above the player with the rest of the pre-enrolment
   disclosure — feature 020 established that placement and the reasoning holds.
3. The expiration date on `CourseDetail`, next to the last-reviewed line from 021.
4. An admin policies editor: four documents, a textarea each, one save.
5. An admin currency dashboard with the four sections. Each row links to that
   course's editor. Plain tables.
6. `expires_on` on the course details form, defaulted as described.

## A thing to check rather than assume
8.01.1 also requires that when CPE programs are offered alongside
non-educational activities, or several concurrently, participants receive a
schedule of events indicating which components are recommended for CPE credit.
Nothing in abacadaba does this and nothing needs to.

Confirm that reading rather than assuming it, and if it holds, record it in
COMPLIANCE.md's Gap column as not applicable with the reason. A locator marked
satisfied when it was never tested is worse than one marked not applicable, and
"we don't do that" is a legitimate and checkable answer.

## Acceptance criteria
- `alembic upgrade head` creates the policies table with four placeholder rows
  and adds `expires_on`; `downgrade -1` reverses
- a fresh database refuses to publish any course until all four policies are
  written, and says so plainly
- all four policies render at their URLs for a signed-out visitor and are linked
  from the footer
- refund, cancellation, and complaint links appear in the course disclosure block
  before enrolment
- publish is refused without an expiration date
- an expired course refuses new attempts with a reason, and does not 404
- the currency dashboard lists overdue, due-soon, published-but-edited, and
  expiring courses, worst first
- a course qualifying for two sections appears in both
- `npm run lint` passes
- pytest passes

## When done
Append an entry to CHANGELOG.md.

Then update COMPLIANCE.md rather than only appending to it:
- 8.01.1's existing Gap entry from feature 020, which records that refund,
  cancellation, and complaint resolution policies are not published, is closed by
  this feature. Update the row; do not add a second one.
- 4.02's Gap entry from feature 021, which records the published-but-edited
  problem and names this feature as the mitigation, should be updated to point at
  the dashboard — and should still say the underlying problem is unsolved,
  because reporting a state is not the same as preventing it.
- Add rows for 4.01's review cycle enforcement and for 9.02.2.

With this feature the sequence begun at 019 is complete. Write a short section at
the end of COMPLIANCE.md listing every locator still carrying an open Gap, so the
next person reads one list instead of nineteen rows.
