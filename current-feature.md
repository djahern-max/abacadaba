# Current Feature

## Feature 029, General programs

## Goal
A course can be offered as ordinary education rather than as a CPE program. On a
general course, no participant-facing surface says CPE, NASBA, credit, or field
of study — not the course page, not the certificate, not the verify page — and
publish stops demanding compliance artifacts that a general course has no reason
to produce. Courses offered as CPE programs are unchanged in every respect.

## Where this came from
abacadaba is about to have a real teacher and real students. It is still the
training ground for superCPE and every compliance feature built so far stays
built — but a middle-school science unit should not carry a red box about NASBA
registration, and its author should not have to name a second CPA reviewer and
clear a 0.2-credit floor to press Publish.

Feature 027 made the application stop *lying* about registration. This feature
lets a course stop raising the subject.

## Numbering note
`next-features.md` was spent at 026 and 027 was the first feature specified from
COMPLIANCE.md's Open Gaps list. This one is from neither. It is new product
capability, not corrective work and not a gap closure, so it takes the next
whole number rather than `027a`. That next whole number is 029, not 028: 028
was spent in the interim on "The completion path," a bug fix (BUG-001) found
during a testing walkthrough, unrelated to this feature and already shipped —
see CHANGELOG.md.

## In scope
- `program_kind` on a course: `'cpe'` or `'general'`
- Suppressing every CPE-specific field from the public course payload, the
  certificate, and the verify page when a course is general
- Relabelling the descriptors that survive, so they read as teaching rather than
  as compliance
- A named, enumerated set of publish-validation relaxations for general courses
- Snapshotting `program_kind` onto the certificate at claim time
- Deriving the footer's policy links rather than hardcoding them

## Out of scope
- Any change to a `'cpe'` course's behavior. This feature is additive. If a test
  written before this feature changes its expected output for a CPE course,
  something is wrong — stop and say so rather than updating the test.
- Multi-tenancy, workspaces, or per-teacher sites. abacadaba is single-tenant
  (`sponsor_profile` is a CHECK-enforced singleton) and this feature does not
  change that.
- Registration state. That is 027's `sponsor_profile.registry_status` and it
  must not be folded into this field. See "Two facts, two fields" below.
- A draft-and-version model for courses, still the real fix for
  published-but-edited and still larger than any one feature.
- Retention enforcement (9.02), still open in COMPLIANCE.md.
- Changing `courses.pass_ratio` or its 70 percent floor. A 70 percent pass mark
  is a defensible teaching choice as well as a CPE rule; leave it alone.
- Changing the credit formula, the question `kind` split, objectives, or any
  other schema shipped in 019–027 beyond the two new columns below.

## Two facts, two fields
There is a strong pull toward one enum with three values — something like
`'general' | 'shadow' | 'live'` — that folds this feature's question together
with 027's. Do not build that.

They are different facts with different owners:

- **Is abacadaba on the National Registry?** A fact about the world, about the
  sponsor, true or false for the whole site at once. That is
  `sponsor_profile.registry_status`, and 027 already models it.
- **Is *this course* offered as a CPE program?** An editorial decision, per
  course, made by whoever authored it.

Folding them produces a field where changing a course's presentation silently
restates the sponsor's legal status, which is the exact class of error 027
existed to remove. Two fields, and the interaction between them is derived — see
Part 3.

## Why this is not a role check
The obvious implementation is to hide the CPE furniture from non-admin users.
It is wrong for three reasons, and the file says so here because it will occur
to whoever builds this.

1. An author previewing her own course is not a participant, so she would never
   see what her students see. Every bug in this feature would be invisible to
   the only person positioned to notice it.
2. Role is the wrong axis. A CPE participant is not an admin either, and at
   superCPE the CPE descriptors must be visible to *everyone*. A role check
   gets that backwards and would have to be torn out.
3. It hides rather than decides. The disclosure block would still be generated,
   still be in the payload, and still be one CSS change or one API call away
   from a participant. Suppression that happens at the template is not
   suppression.

Decide it on the course, and suppress it in the schema. Which brings us to:

## Part 1, the column

Add to `courses`:
- `program_kind`: string, `NOT NULL`, CHECK in `('cpe', 'general')`, server
  default `'cpe'`

**String with a CHECK, not a boolean**, matching `registry_status` and
`questions.kind`. And a two-option `<select>` in the admin, not a checkbox — 027
made this argument about registry status and it holds here: a checkbox labelled
"CPE program" invites an idle click, and a select forces a choice with both
options visible and named.

**Default `'cpe'`, deliberately.** Existing rows were authored as CPE programs
and the default preserves that with no backfill. More importantly it is the
fail-safe direction: a general course that accidentally renders CPE descriptors
is noisy but honest (the 027 notice fires, and the page says plainly that
completing it earns no credit), whereas a CPE course that accidentally hides
them is an 8.01.1 disclosure failure. When in doubt the column should fail
toward saying more, not less.

Add to `attempts`:
- `cert_program_kind`: string, nullable

Written once at claim time by `claim_certificate` alongside the other `cert_*`
columns, exactly as 024 established and 027 followed for `cert_registry_status`.
A certificate records what was true the day it was issued. For the pre-029
fallback, follow the pattern already in `certificates.py::_to_data`: a null
`cert_program_kind` on an otherwise-populated snapshot reads as `'cpe'`, since
every certificate claimed before this feature shipped was in fact issued for a
CPE-presented course. Put that reasoning in a comment at the fallback, the way
027 did.

Naming note: `program_kind`, not `program_type`. "Type of formal learning
program" is 9.01 item 6 and already means group / self study / nano — it lives
on `cert_delivery_method`. Do not reuse that phrase for this.

## Part 2, suppress in the schema, not in the template

`GET /courses/{slug}` currently carries `field_of_study`, `credit_award`,
`program_level`, `prerequisites`, `advance_preparation`, and (from 027)
`sponsor_registry_status`.

When `program_kind == 'general'`, the payload **omits** the CPE-only fields
outright rather than blanking them or letting the frontend skip rendering:

**Omitted:** `field_of_study`, `credit_award`, `sponsor_registry_status`, the
program expiration date (026), and `delivery_method` wherever it appears.

**Kept:** learning objectives, `program_level`, `prerequisites`,
`advance_preparation`, the review chain (developer, reviewer, `reviewed_at`),
and everything about the lessons themselves.

This follows 004's precedent, restated by 023a: `QuestionPublic` omits
`feedback` entirely rather than filtering it at serialization, and that is why
its guard test is meaningful. Same reasoning. If the field is absent from the
payload, no template change and no CSS change can put it back on screen, and the
guard test in the test list below actually proves something.

The kept fields survive because they are good instructional design that the
Standards happen to also require. A student benefits from knowing what she will
be able to do afterward, what level it is pitched at, and what she needs to know
first. They just need different words, which is Part 4.

## Part 3, the notice is derived and must stay derived

027 renders a pre-enrollment notice on `CourseDetail.jsx` when the sponsor is
unregistered, and the equivalent on the certificate and the verify page. That
notice now branches on two fields:

```
show_not_registered_notice = program_kind == 'cpe' and registry_status == 'not_registered'
```

**Derived at the point of use. Never stored, never independently settable.**

The failure this prevents is specific and worth naming: someone six months from
now turns off "the annoying red box" while leaving `CPE credit: 1.2` and
`Field of study: Taxes` on the page. That single configuration is the only one
that is actively misleading — worse than today's noisy honesty and worse than a
clean general course. Part 2's schema-level omission makes it unreachable by
construction, because the fields and the notice are suppressed by the same
branch on the same field. Keep it that way: do not add a separate flag for the
notice, and do not let the notice's condition drift into a different function
from the one that decides the payload.

There is a matching hazard on the other side. A published general course that is
switched to `'cpe'` would be presenting itself as a CPE program without ever
having passed the CPE publish gate. So: **`program_kind` may not change while
`is_published` is true.** Refuse the PATCH with a message telling the author to
unpublish first. This is one rule and no new state; bumping `content_updated_at`
would not help, because a general course has no review requirement for the
staleness rule to bite on.

## Part 4, what a general course says instead

One label map, one module — `frontend/src/constants/programLabels.js` or
equivalent. Not ternaries scattered through `CourseDetail.jsx`, because the next
person to add a descriptor needs one place to put both words.

| CPE | General |
| --- | --- |
| Program level | Level |
| Prerequisites | What you should know first |
| Advance preparation | Before you start |
| Field of study | *(omitted)* |
| CPE credit | Length |
| Expires | *(omitted)* |
| Qualified assessment | Quiz |
| What you will learn | *(unchanged — it already reads as teaching)* |

Leave the `program_level` *values* alone. "Basic" and "Intermediate" read fine
to a general audience, and "Overview" and "Update" reading oddly is not worth a
second list that NASBA controls one copy of. 020's `/meta/program-levels`
endpoint exists precisely so there is one list.

**Length is derived from runtime, not from credit.** Sum
`lessons.duration_seconds` across the course's lessons and render it in minutes.
Do not relabel `credit_award` as minutes and do not multiply it back out by 50 —
0.4 credit is a floored one-fifth increment and reversing the arithmetic gives a
number that is confidently wrong by up to nine minutes. `duration_seconds` is
auto-filled from the actual uploaded file (feature 017, confirmed by 022), so
the runtime sum is the one duration figure in this application that is measured
rather than derived from a derived value. Compute it at read time; do not add a
column.

**The certificate.** A certificate for a general course omits Field of Study,
CPE Credit Awarded, Type of Formal Learning Program, the registry ID, the NASBA
time statement, *and* 027's not-registered notice — the notice exists to
contradict a CPE claim, and there is no claim here to contradict. It keeps the
participant name, course title, completion date, score, issuing organization,
and the verification code. Relabel the `Sponsor` field to `Issued by` on the
general path; `sponsor_profile.name` is just an organization name and "sponsor"
is CPE vocabulary. `Verify.jsx` renders from the same `CertificateData` the PDF
does and should inherit all of this without a second code path — 027 proved that
with a dedicated agreement test, so extend that test rather than writing a new
one.

## Part 5, publish validation

`validate_for_publish` in `app/services/admin_content.py` gains a `program_kind`
branch. **Enumerate the relaxations individually with the reason attached. Do
not implement this as "skip the CPE rules."** A future reader needs to see which
specific rule was dropped and why, and a blanket skip means the next rule added
to that function is silently relaxed too by an author who never considered it.

Relaxed when `program_kind == 'general'`:

| Rule | Feature | Why it drops |
| --- | --- | --- |
| Field of study required | 020 | Not applicable. Leave whatever value is in the column alone; just stop requiring it. |
| Developer, reviewer, reviewer ≠ developer, `reviewed_at` set, review not stale | 021 | The two-person SME chain is a CPE control. Requiring a second credentialed reviewer to publish a science unit is the red tape this feature removes. |
| Licensed-CPA participation for accounting / auditing / tax fields | 021 | Downstream of field of study, which no longer applies. |
| Credit computed and not stale | 022 | There is no credit. |
| `credit_award >= 0.2` | 022 | The largest practical blocker: a four-minute lesson floors to 0.0 and is refused today. |
| Every counted lesson has `duration_seconds` | 022 | An input to a formula that is not running. |
| Credit-derived review and assessment question minimums | 023 | Floors expressed per credit, against a credit that does not exist, are floors against zero. |
| 75 percent objective coverage | 023a | A 6.01.2 assessment rule. |
| Non-blank feedback on every review question | 023a | A 5.01.2.2 rule. Good practice; not a gate here. |
| Forced-choice ban on the assessment | 023 | True/false is a legitimate item type for a general quiz. |
| Sponsor profile completeness | 027 | 9.01's certificate fields, none of which the general certificate prints — except the name. See below. |

Still enforced when `program_kind == 'general'`:

- At least one learning objective. It is the "What you will learn" list and it
  is the best thing on the page.
- At least one assessment question. A course whose quiz is empty is not
  publishable regardless of what it is offered as.
- `pass_ratio >= 0.70`. Out of scope to change, and defensible on its own terms.
- `sponsor_profile.name` non-blank. It prints on the certificate as "Issued by."
- The four policies not being placeholder text (026) — **but see Part 6**, which
  changes what this rule is doing rather than whether it runs.

Every relaxed rule keeps its message text unchanged for CPE courses.

## Part 6, the footer

Screenshot evidence and 026: the site footer links Complaint Resolution, Program
Cancellation, Records Retention, and Refund and Cancellation on every page.
These are site-wide policy pages, not course fields, so a per-course column
cannot govern them directly.

Do not add a second, site-wide flag. It would be able to contradict the
per-course one, and 027's whole lesson was that two fields describing one fact
drift. Derive it:

```
show_policy_footer = EXISTS (select 1 from courses where is_published and program_kind = 'cpe')
```

One cheap `EXISTS`. The policy pages stay reachable at `/policies/{slug}` and
stay linked from every CPE course's own disclosure block — which is what 8.01.1
actually asks for ("made available to participants"), so satisfying it per
course rather than in the chrome is not a weakening. State that reasoning in
COMPLIANCE.md's 8.01.1 Gap column, because a reader who checks the footer of a
general-only site and finds nothing needs to be able to find out why.

The nice property: publish one CPE-presented course again and the footer returns
with no configuration.

If the query cost matters later, cache it. Do not preempt that with a column.

## Backend tasks
1. `program_kind` on `Course`, `cert_program_kind` on `Attempt`, one migration.
   Verify `downgrade -1` against a database with rows. No backfill: the server
   default covers existing courses, and `cert_program_kind`'s null fallback is
   handled in code for the same reason 027's was.
2. The publish branch in `validate_for_publish`, one relaxation at a time, each
   with the table above's reason as a comment. Return the same flat list shape —
   feature 017's checklist depends on it.
3. Refuse `program_kind` changes on a published course, in the course PATCH
   path.
4. Omit the CPE fields from `CourseWithLessons` / `CourseDetail` when general.
   Prefer omission at schema-construction time over `exclude_none`-style
   filtering; the guard test should be able to assert absence, not emptiness.
5. Runtime sum for the general Length figure. Read-time, no column.
6. `claim_certificate` writes `cert_program_kind`; `_to_data` falls back to
   `'cpe'` on null with a comment; `render_pdf` branches on it for the field
   list, the notice, and the `Sponsor` → `Issued by` label.
7. The footer `EXISTS`, exposed wherever the frontend already gets site-level
   data.

## Frontend tasks
1. The `program_kind` select in `CourseDetailsForm.jsx`, placed first on the
   form — it changes which other fields matter, so it should not be discovered
   after filling them in. A hint saying what each option means, in the shape of
   `AdminSponsorSettings.jsx`'s registry-status hint. Disabled with an
   explanation while the course is published.
2. The label map module, and `CourseDetail.jsx` reading from it.
3. Hide field-of-study, credit, and the Credit panel's Publish-gating banner in
   the admin editor for a general course. The Credit panel itself can stay
   visible and computable — it is useful information and 022 already keeps it
   outside the batched save — but it must not read as a publish blocker.
4. `CoursePublishPanel.jsx`: the relaxed rules should simply not appear in the
   checklist for a general course, rather than appearing pre-checked. A green
   check against a rule that was never evaluated is exactly the defect 020c's
   Bug 4 was about.

## Tests
- **The guard test, modelled on `test_quiz_response_never_leaks_correct_answer`:**
  serialize a published general course's public payload and assert that "CPE",
  "NASBA", "credit", "field of study", and "sponsor" do not appear in it at all,
  case-insensitively. Not that the fields are null — that they are absent.
- The same assertion against the general certificate PDF's extracted text and
  against the `/certificates/{code}` payload.
- A CPE course's payload, certificate, and verify page are byte-for-byte what
  027 left them. Parametrize an existing 024/027 certificate test over
  `program_kind` rather than writing a parallel suite.
- Each relaxed publish rule, one test each: a general course publishing while
  violating it, and the CPE course still refused for the same violation. This is
  the bulk of the new tests and it is the point — a relaxation nobody tested is a
  relaxation nobody can see.
- Each still-enforced rule refuses a general course.
- `program_kind` cannot be changed while published; can be changed after
  unpublishing; and a general course switched to CPE and republished must clear
  the full CPE gate.
- A certificate claimed as general stays general after its course is unpublished
  and switched to CPE — the snapshot holds.
- The null-`cert_program_kind` fallback renders as a CPE certificate.
- The footer `EXISTS` is true with one published CPE course, false with only
  published general courses, and false with an unpublished CPE course.
- `conftest.py`'s shared fixtures: courses default to `'cpe'`, so the existing
  343 tests should need no fixture change. If any do, that is a signal this
  feature is not additive — investigate before editing the fixture, and follow
  027's precedent of explaining the default in a comment.

## COMPLIANCE.md
**Add no new rows.** No locator in the Standards is satisfied by a general
course, and none is violated by one — a program not offered as CPE is outside
the document's scope by construction, not by exemption.

Two edits instead:

1. Extend 027's scope note. It currently says the matrix maps abacadaba's
   behavior to the Standards document and nothing else. Add that every row
   describes courses with `program_kind = 'cpe'`, and that general courses are
   not claimed-and-unverified but out of scope entirely.
2. The 8.01.1 Gap column: the policy links moved from the site footer to a
   derived condition, with the per-course disclosure block as the surface that
   actually satisfies the requirement. Part 6's reasoning, in two sentences.

## Acceptance criteria
1. A general course publishes with one objective, one assessment question, a
   video of any length, no reviewer, no field of study, and no computed credit.
2. Its public page, certificate PDF, and verify page contain no instance of CPE,
   NASBA, credit, field of study, or sponsor.
3. The words on its page read as teaching: Level, What you should know first,
   Before you start, Length, Quiz.
4. A CPE course is unchanged end to end, proven by 027's tests passing untouched.
5. There is no reachable configuration in which a credit figure or a field of
   study renders without either a registry ID or the not-registered notice.
6. The full backend suite passes with no pre-existing test modified. `npm run
   lint` and `npm run build` pass.

Then append to CHANGELOG.md and stop.
