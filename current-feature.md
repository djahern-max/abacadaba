# Current Feature

## Feature 024, Completion documents and participant records

## Goal
A certificate carries every field a sponsor is required to put on one, states
facts that were true at the moment of completion and stay true afterward, and is
backed by a record the sponsor can produce on audit.

## In scope
- A sponsor identity record: name, National Registry ID, contact details
- Every required field on the certificate
- A snapshot of the course's credit-bearing facts, taken at claim time
- An admin completions view with filtering and CSV export
- The retention period, recorded

## Out of scope
- Emailing certificates. Worth doing, not compliance.
- Certificate templates, branding, or per-course design.
- Revocation and expiry.
- Publishing the retention policy as a participant-facing page. Feature 026.
- Program expiration dates for self study (9.02.2). Related and real; it belongs
  with 026's currency work, not here.

## Read this before starting
**Feature 022 must have shipped.** A certificate that does not state the number
of credits is not a certificate, and the credit has to come from somewhere
defensible.

Section 9 of `docs/2026-Statement-on-Standards-for-CPE-Programs.pdf` governs
required documentation. **Read it and derive the field list from it.** The list
in "Certificate fields" below is a working list assembled from
`next-features.md`; treat it the way feature 020 treated the fields of study —
verify every item against the document, add anything missing, and drop anything
that turns out not to be required. Then record what you found in the changelog,
so the next person knows the list was checked rather than copied.

The same goes for the retention period. Find it in Section 9, put it in a named
constant, and do not guess it.

## The problem this feature actually solves
`app/services/certificates.py::_to_data` builds certificate data by reading the
course live at download time. Course title, question count, and — once 022 lands
— credit, field of study, and program level all come from the current row.

That means editing a course silently rewrites every certificate ever issued from
it. Change the credit from 0.4 to 0.6 and a certificate downloaded last year now
says 0.6. Change the title and a verification page contradicts the PDF the
participant already has.

For a fun micro-learning app that is a curiosity. For a CPE sponsor it is an
audit defect: the certificate is supposed to record what a participant completed,
not what the course happens to say today.

**The fix is a snapshot, written once at claim time.** Everything the certificate
asserts is copied onto the attempt when the certificate is first claimed, and the
PDF and the verification page read the snapshot, never the course.

## Data model

New `sponsor_profile` table, singleton:
- id, `name`, `national_registry_id`, `state_registry_ids` (text, nullable, free
  form — sponsors registered with individual state boards carry more than one),
  `website`, `contact_email`, `address`, `updated_at`

One row. Enforce it with a CHECK on `id = 1` rather than by convention; a second
sponsor row is not a state this application has any meaning for. Editable in the
admin, not an environment variable — this is audit data that changes rarely and
must be visible to whoever is responsible for it, and `.env` is not where a
responsible person looks.

Add to `attempts`, all nullable, all written at claim time:
- `cert_course_title`, `cert_field_of_study`, `cert_program_level`
- `cert_delivery_method`
- `cert_credit_award` (numeric(4,1))
- `cert_sponsor_name`, `cert_sponsor_registry_id`
- `cert_issued_at`

Nullable because attempts predating this feature have no snapshot, and because
an unclaimed attempt has none either. `certificate_code` already follows exactly
this pattern from feature 007 — generated on first claim, not at attempt
creation. Follow it.

`cert_delivery_method` is a string, not a boolean or an enum with one value. It
reads `QAS Self Study` today. Nano learning and blended learning are real
delivery methods in the Standards and superCPE will issue certificates for them;
a column that can already hold the answer costs nothing now.

Claiming twice keeps the original code — feature 007 established that. It must
now also keep the original snapshot. A second claim updates the recipient name
and nothing else.

## Certificate fields
Working list, to be verified against Section 9:

- Sponsor name
- Sponsor's National Registry of CPE Sponsors ID (and state registry IDs where
  the sponsor holds them)
- Participant name
- Course title
- Field of study
- Delivery method
- Number of CPE credits awarded
- Date of completion
- Program knowledge level

The current PDF in `app/services/certificates.py::render_pdf` carries the name,
the course title, the score, the date, the wordmark, and the verification code.
Score is not on the required list and should stay anyway — it is what the
verification page asserts and dropping it would weaken that page for no gain.

`_fit_font_size` already shrinks a long name or title to fit. The new fields turn
a sparse landscape page into a fairly full one; lay the required fields out as a
labelled block in the lower third rather than as more centred lines, and check a
long course title against a long sponsor name before calling it done.

## Publish and claim rules
- Publishing is refused when the sponsor profile is incomplete. A course that
  cannot produce a compliant certificate should not be able to enrol anyone.
  Message names the missing fields and links to the sponsor settings page.
- Claiming is refused, as today, unless the attempt is complete and passed. That
  is feature 007's rule and it does not change.
- The snapshot is written inside the same transaction that generates the code.
  A certificate with a code and no snapshot is a state nothing can render.

## Backend tasks
1. `app/models/sponsor_profile.py` and the eight columns on `Attempt`. Hand-add
   the singleton CHECK. Verify `downgrade -1`.
2. A seed or migration inserting the single sponsor row with empty strings, so
   the admin page has something to edit rather than needing a create path for a
   record that can only ever exist once.
3. `app/services/certificates.py`:
   - `claim_certificate` writes the snapshot on first claim only, from the course
     and the sponsor profile, in the same transaction as the code
   - `_to_data` reads the snapshot, not the course. **This is the change.** If any
     field still resolves through `attempt.course`, the feature is not done.
   - `render_pdf` lays out the full field list
   - `verify_code` returns the snapshot, so the verification page and the PDF can
     never disagree
4. `app/services/completions.py`, read-only: completed attempts with course
   title, participant name and email where signed in, credit, completion date,
   pass or fail, and certificate code. Filter by course, by date range, and by
   passed. Aggregate SQL, one query — feature 012 set that rule for analytics and
   it holds here.
5. `GET /admin/completions` and `GET /admin/completions.csv`. The CSV is the
   audit artifact; give it a stable column order and a header row, and stream it
   rather than building it in memory.
6. `GET /admin/sponsor` and `PATCH /admin/sponsor`, behind `require_admin`.
7. `validate_for_publish` gains the sponsor-profile rule, joining the flat list.
8. Tests:
   - claiming writes a snapshot matching the course at that moment
   - editing the course afterwards does not change the certificate, the PDF, or
     the verification page
   - claiming twice updates the name, keeps the code, and keeps the snapshot
   - the PDF contains every required field, asserted against extracted text
     rather than by eyeballing bytes
   - publish is refused with an incomplete sponsor profile, naming the fields
   - the completions CSV has a stable header and one row per completed attempt
   - filters narrow the result set correctly
   - a certificate issued before this feature still renders — decide whether that
     means backfilling snapshots or rendering from the course with a comment, and
     say which you chose and why

## Frontend tasks
1. An admin sponsor settings page, reachable from the admin nav rather than
   buried inside a course.
2. An admin completions page: filters, a table, a download button. Plain table,
   no charts — feature 012 settled that argument.
3. `Verify` renders the snapshot fields, including credit, field of study, and
   delivery method. The existing self-reported-name wording from feature 007 stays
   and still applies to anonymous attempts.
4. `Result` needs no change beyond whatever the new fields surface.

## A thing to check rather than assume
Anonymous attempts. Feature 007 built certificates before accounts existed, and
feature 008 kept the anonymous path working: a signed-out participant types a
name and gets a certificate whose name is self-reported.

Section 6 requires sponsors to verify individual successful completion, and
states that self-certification of attendance or completion alone is not
sufficient. A typed-in name on an anonymous attempt is close to exactly that.

**Do not fix it in this feature by removing the anonymous path** — that is an
auth and enrolment decision with product consequences. Do determine whether an
anonymous attempt should be allowed to claim a certificate at all, state the
conclusion in the changelog, and record the gap in COMPLIANCE.md against 6.01
either way. If it stays, the verification page's existing wording is the
mitigation and should be strengthened, not softened.

## Acceptance criteria
- `alembic upgrade head` adds the table and columns; `downgrade -1` reverses
- an admin can fill in the sponsor profile, and publish is refused until they do
- a claimed certificate PDF carries every field on the verified Section 9 list
- editing the course title and credit afterwards changes neither the PDF nor the
  verification page
- the verification page and the PDF agree on every field, by construction
- a long name against a long course title against a long sponsor name still fits
  the page
- the completions view lists every completed attempt and exports to CSV
- pytest passes

## When done
Append an entry to CHANGELOG.md recording what Section 9 actually required
against the working list above, what you concluded about anonymous attempts, and
the retention period you found.

Then append to COMPLIANCE.md: rows for the Section 9 documentation locators and
for 6.01. The 6.01 Gap column carries the anonymous-attempt conclusion. Do not
mark 6.01 satisfied on the strength of a passed assessment alone if the identity
behind it is self-asserted.
