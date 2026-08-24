# Current Feature

## Feature 027, Sponsor registration state

## Goal
abacadaba stops asserting things about its relationship with NASBA that are not
true. A certificate issued by an unregistered sponsor says so, plainly, on its
face — and the publish gate stops requiring an author to type a registry ID that
does not exist.

## Numbering note
`next-features.md` ends at 026. That roadmap is now spent, and COMPLIANCE.md's
Open Gaps list is the working backlog in its place. This is the first feature
specified from that list rather than from the original plan — except that the
problem below is **not in that list**, which is the point of the next section.

Not `026a`: this is new capability (registration state as a modeled concept),
not corrective work against 026's surface area.

## Where this came from
Publishing the first real course required filling in the sponsor profile.
`national_registry_id` is a free-text string, `validate_for_publish` refuses to
publish while it is empty, and whatever goes in it is frozen onto every
certificate by `claim_certificate` alongside `NASBA_TIME_STATEMENT`.

abacadaba is not a registered CPE sponsor and has no registry ID. So the publish
gate, as built, requires the author to invent one. A plausible six-digit number
in that field produces a PDF that carries a sponsor name, a registry ID, and the
50-minute-hour NASBA statement — a document that asserts registered-sponsor
status on every axis a reader would check. Real registry IDs belong to real
sponsors, so an invented one may also name somebody else.

**Note what COMPLIANCE.md did not catch.** Every row in that file is keyed to a
paragraph of the Standards, and there is no paragraph that says "do not claim to
be a registered sponsor when you are not." That obligation lives in the
registry's own terms and in ordinary honesty, not in the Statement on Standards.
So the matrix is green here and the application is wrong anyway. Add a short note
to COMPLIANCE.md saying the matrix covers the Standards document and nothing
else, so the next person does not read a full green column as full coverage.

## In scope
- Registration state as an explicit field on the sponsor profile
- Suppressing the NASBA time statement and registry ID on certificates issued by
  an unregistered sponsor
- An unmistakable not-CPE-credit notice on those certificates and on the verify
  page
- Making the publish gate's registry ID requirement conditional on that state

## Out of scope
- Retention enforcement (9.02). Real, open in COMPLIANCE.md, and a bigger
  feature than this one. Not here.
- Whether the program cancellation policy's stated grace period matches what
  unpublishing actually does to in-progress attempts. That is a question to
  answer by reading `courses.py` and `attempts.py`, not a task. Answer it, and
  if the code and the policy disagree, that is a separate feature.
- The NASBA escalation paragraph in the complaint resolution policy. Policy
  bodies are human-written text in a table row; nothing here should generate or
  conditionally rewrite them.
- Anything about actually applying to the National Registry.
- Backfilling certificates already issued. See "The gap this feature does not
  close."

## Part 1, registration state as a stated fact

Add to `sponsor_profile`:
- `registry_status`: string, CHECK `'not_registered'` / `'registered'`,
  `NOT NULL`, server default `'not_registered'`

**This one is stored, not derived, and that is deliberate.** 019a set the
derived-not-stored rule, 022 followed it for credit staleness, and 026 followed
it for `is_placeholder`. This is an exception and the reasoning should go in the
model docstring so it does not read as someone forgetting the rule.

Whether a sponsor is on the National Registry is a fact about the world. No
amount of inspecting the string in `national_registry_id` can determine it — a
six-digit number is not evidence, and format-sniffing would give a confident
wrong answer. Deriving it would mean inferring a legal status from a text field,
which is exactly the failure this feature exists to remove. Make the sponsor
state it.

Default `'not_registered'`, so a fresh database and the existing seeded row are
both honest without anyone doing anything.

## Part 2, what a certificate says

`app/services/certificates.py` currently prints `NASBA_TIME_STATEMENT` on every
certificate and the registry ID whenever the snapshot has one.

When the sponsor is not registered at claim time:
- Do not print the NASBA time statement
- Do not print a registry ID field at all — not "N/A", not blank, absent
- Print a notice, in the same weight as the participant name rather than as fine
  print: this program is not offered by a sponsor registered with NASBA, and
  completion does not earn CPE credit

The last one is the substantive change. Suppressing the boilerplate makes the
document silent about registration; the notice makes it explicit. Silence is
what an author skimming a PDF fails to notice.

**Snapshot it.** `registry_status` joins the `cert_*` columns written once at
claim time, for the same reason `cert_sponsor_registry_id` did in 024: a
certificate records what was true on the day it was issued. A sponsor who
registers next year must not retroactively convert last year's certificates into
credit-bearing documents, and one who lapses must not retroactively void them.

`Verify.jsx` renders from the same `CertificateData` the PDF does, so it should
inherit all of this without a second code path. Confirm that rather than assume
it — that single-source property is worth a test of its own.

## Part 3, the publish gate

`sponsor_profile.py::REQUIRED_FIELDS` currently lists `national_registry_id`
unconditionally.

Make it conditional: a registry ID is required when `registry_status` is
`'registered'`, and irrelevant when it is not. `name` stays required either way —
9.01 item 1 wants a sponsor name on the certificate regardless of who the sponsor
is.

Today's gate has it backwards. It compels a false statement in order to publish,
which is a worse outcome than the missing field it was written to prevent.

Keep `missing_fields`'s existing message shape. `AdminSponsorSettings.jsx` reads
that list directly and should need no change beyond the new control — which is a
plain two-option select with a hint explaining what registered means, not a
toggle. A checkbox labelled "registered" invites an idle click.

## Backend tasks
1. `registry_status` on the model, migration with the CHECK hand-added and the
   server default. Verify `downgrade -1`. Check whether the dev database has any
   claimed certificates before running it; if it does, say so in the changelog —
   they will render under the pre-024 no-snapshot path and keep reading live.
2. `cert_registry_status` on `attempts`, written by `claim_certificate` inside
   the same transaction as the rest of the snapshot.
3. `_to_data` carries it. `render_pdf` and the verify payload branch on it.
4. `REQUIRED_FIELDS` becomes a function of the profile, not a module constant.
   Grep for other readers of it first.
5. `GET`/`PATCH /admin/sponsor` accept and return the new field.
6. Tests:
   - an unregistered sponsor's certificate PDF contains neither the time
     statement nor a registry ID, asserted against extracted text the way 024's
     tests do
   - it does contain the not-credit notice
   - a registered sponsor's certificate is unchanged from what 024 shipped
   - the verify page and the PDF agree in both states
   - publish succeeds with an empty registry ID when not registered
   - publish is refused, naming the field, with an empty registry ID when
     registered
   - publish is refused with an empty sponsor name in both states
   - registering after a certificate is claimed does not change that certificate
   - `conftest.py`'s `DEFAULT_SPONSOR` needs a `registry_status` — decide which
     default the shared fixture uses and say why in a comment, because every
     existing certificate test inherits it

## Frontend tasks
1. The select on `AdminSponsorSettings`, with the registry ID field's required
   marker following it.
2. Whatever the certificate and verify page need for the notice. No new page.
3. Consider whether the course detail page should carry the same notice before
   enrollment. 8.01 item 11 makes the sponsor statement conditional on being an
   approved sponsor, which is the same conditional in the other direction — a
   participant deciding whether to spend an hour deserves to know before, not
   after. Decide it, do it or don't, and record which in the changelog.

## The gap this feature does not close
An admin can set `registry_status` to `'registered'` and type any number. Nothing
here verifies anything against the National Registry, and nothing could, short of
an integration that does not exist.

What changes is that the false claim becomes a deliberate act rather than a
side effect of a validation rule that left no honest option. That is the whole
of what software can do about it, and the Gap column should say exactly that
rather than implying the claim is now checked.

## Acceptance criteria
- `alembic upgrade head` adds both columns with honest defaults; `downgrade -1`
  reverses
- a course publishes with an empty registry ID while unregistered
- that course's certificate carries the notice and neither NASBA field
- flipping to registered restores 024's certificate exactly
- previously claimed certificates are unaffected by the flip in both directions
- `npm run lint` passes
- pytest passes

## When done
Append to CHANGELOG.md.

In COMPLIANCE.md: 9.01's row (items 8 and 10) needs updating — those fields are
now conditional, and the row currently reads as though they are always present.
Add the scope note described in "Where this came from" above the matrix. Add
nothing to the Open Gaps list unless Part 3 turns something up; this feature
closes a problem that list never contained.
