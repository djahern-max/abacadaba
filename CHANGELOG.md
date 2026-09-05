# Changelog

Completed features, oldest first. Append only.

## 2026-08-04, Feature 001, Walking skeleton
Backend (FastAPI + SQLAlchemy + Alembic) and frontend (React + Vite) now talk to
Postgres end to end: GET /api/v1/health checks the database and the app shows a
green/red connection status pill. Vite boilerplate removed, global CSS variables added.

## 2026-08-04, Feature 002, Lessons: model, API, and browsing
Lessons are a real domain object now: a Postgres-backed lessons table, list and
detail endpoints under /api/v1, an idempotent seed script with three sample
lessons, and client-side routing with a lesson grid and a detail page with a
16:9 "video coming soon" placeholder.

## 2026-08-04, Feature 003, Video storage and playback
Lessons can now have a video in a private DigitalOcean Space. Added a Spaces
storage service (presigned GET URLs, private uploads), a video-url endpoint,
a shared-secret-guarded admin upload endpoint, and an upload_video CLI. The
lesson detail page plays the video inline via a VideoPlayer component with a
reload button for expired presigned URLs, falling back to the existing
placeholder when no video has been uploaded yet.

## 2026-08-04, Feature 004, Quiz data model and delivery
Lessons now have real quiz content: questions and choices tables (cascading,
position-ordered), a GET /lessons/{slug}/quiz endpoint served through
schemas that never include is_correct, and a seeded five-question quiz for
each of the three lessons. The frontend has a read-only quiz page listing
every question with lettered choices, reachable via a "Take the quiz" button
on the lesson detail page. Answering, grading, and scoring are feature 005.

## 2026-08-04, Feature 005, Taking the quiz with per answer confetti
Added POST /lessons/{slug}/quiz/answers to grade one answer at a time
(400 on a choice from a different question, 404 on an unknown or
cross-lesson question). The quiz page now walks through one question at a
time with a progress bar: pick a choice, Submit grades it, a correct
answer fires a small canvas-confetti burst (skipped under
prefers-reduced-motion), a wrong answer reveals the correct choice in
green, and Next/Finish advances to a "Quiz complete" placeholder. Choices
are real buttons with visible focus rings and an aria-live announcement
of the result. Scoring, pass/fail, and the attempts table are feature 006.

## 2026-08-04, Feature 006, Attempts, scoring, and passing at 4 of 5
Added attempts and attempt_answers tables (the latter unique on
attempt_id + question_id, the DB-level replay guard) plus
POST /lessons/{slug}/attempts, POST /attempts/{id}/answers, and
GET /attempts/{id}/result, replacing and removing the sessionless
POST /lessons/{slug}/quiz/answers from feature 005. The server now owns
scoring and pass/fail (PASS_THRESHOLD = 4) and rejects a question
answered twice in the same attempt with a 409. The quiz page starts an
attempt on load and redirects to /attempts/:attemptId on the final
answer; the new results page shows the score and pass/fail state,
fires a bigger, staggered confetti burst on a pass, and offers rewatch
and retry links on a fail. Certificates land in feature 007.

## 2026-08-04, Feature 007, Certificate generation and download
Passed attempts can now earn a downloadable PDF certificate. Added
recipient_name and certificate_code (confusion-free, hyphenated,
unique) columns to attempts, POST /attempts/{id}/certificate to claim
one (409 if not passed/complete), GET /attempts/{id}/certificate.pdf
to stream a reportlab-rendered landscape PDF (font shrinks to fit long
names or titles), and GET /certificates/{code} for case- and
hyphen-insensitive public verification, returning valid: false rather
than a 404 for unknown codes. The results page now offers a name entry
form on a pass that reveals the code and a plain download link once
claimed (persisted in localStorage so a reload skips the form), and a
new /verify/:code page renders the certificate details or a clear
not-found state, wording things as self-reported since there are no
accounts yet. SITE_URL/VITE_SITE_URL back the verification URL printed
on the certificate. Feature 008 will replace the typed name with an
authenticated user.

## 2026-08-04, Feature 008, Accounts, real auth, and progress
Real accounts arrive: users and sessions tables (opaque bcrypt-backed
sessions, 30-day httpOnly/SameSite=Lax cookies, no JWT), a user_id on
attempts (nullable, ON DELETE SET NULL, anonymous quizzes still work),
and /auth/register, /auth/login, /auth/logout, and /auth/me. The
shared-secret upload guard from feature 003 is gone, replaced by a
real is_admin check (require_admin: 401 signed out, 403 non-admin) and
a make_admin CLI to promote the first account; upload_video.py now
logs in instead of sending a header. Certificates claimed by a signed
in user use the account's display_name automatically instead of a
typed name, and the verify page and CertificateVerification say so.
GET /me/attempts feeds a new /me progress page. On the frontend, an
AuthContext wraps the app, the header shows sign in/out state, Login
and Register pages handle the forms, and the result page skips the
name form entirely and auto-claims when signed in, replacing the
feature 007 localStorage persistence with the certificate_code the
API now returns on the attempt result itself.

## 2026-08-06, Feature 009, Deploy to production
abacadaba.com is live on the public internet. Re-specced mid-flight from
DigitalOcean App Platform to a Droplet (Ubuntu 24.04, Docker Compose, nginx,
Postgres in a container) for cost and to keep building raw-VM ops skills; the
container image is unchanged so the original target stays a drop-in option.
The API lives on api.abacadaba.com and the frontend on abacadaba.com,
sharing a registrable domain so SESSION_COOKIE_DOMAIN=.abacadaba.com works
with SameSite=Lax rather than needing SameSite=None. The Droplet never runs
npm or installs Node — the frontend is built off-box and only dist/ is
shipped — closing off the postinstall-script compromise vector that hit an
earlier project. Backend changes: a non-root Dockerfile, config-driven
cookie/CORS/docs settings (docs disabled in production), a DATABASE_URL
scheme normalizer for psycopg, and a DB-backed /api/v1/health. Host
hardening: key-only SSH restricted to the deploy user, ufw plus a matching
DigitalOcean Cloud Firewall, and docker-compose.prod.yml running the db on
an internal-only network with no published ports and the api bound to
127.0.0.1 with dropped capabilities and a read-only filesystem. deploy.sh
encodes the required order — migrate, then restart the api — so a failed
migration halts the deploy instead of leaving the api on a mismatched
schema. DEPLOYMENT.md and HARDENING.md document the layout, env vars, and
the reasoning behind each control. Monitoring/alerting and automated
backups are feature 013; CDN/transcoding and staging/blue-green deploys
remain out of scope.

## 2026-08-06, Feature 010, Admin authoring
An admin can now create a lesson, upload its video, write its five
questions, and publish it entirely in the browser, no CLI or seed
script required. Backend: AdminLesson/AdminQuestion/AdminChoice
schemas (deliberately kept separate from the leak-free public ones,
which stay is_correct-free), an admin_content service with full
lesson/question/choice CRUD, move-up/move-down reordering that
renumbers the whole set in two passes to dodge the position unique
constraint, set_correct_choice clearing every other choice on the
same question in one transaction, and validate_for_publish returning
every failed rule at once (exactly 5 questions, video uploaded,
title/slug/description non-empty, each question 2+ choices with
exactly one correct). All /admin/* routes sit behind require_admin at
the router level. Deleting a lesson with completed attempts is
refused with a 409 rather than orphaning attempt data. scripts/seed.py
is retired to a bootstrap-only role now that the admin UI is the real
authoring path. Frontend: a new /admin section (lesson list with
published state/question count/video presence, and a per-lesson
editor with details, video upload with a progress bar, and inline
question/choice editing with move and correct-choice controls),
gated by an AdminGuard that redirects signed-out visitors to login
and shows a plain not-authorized message to signed-in non-admins: the
Admin link itself never renders for a non-admin. The publish button
shows the server's validation checklist and disables itself until the
next edit, since the same checklist would just repeat on retry.
Measured time to author one complete lesson by hand, from an empty
form to published: about 5 minutes.

## 2026-08-06, Feature 011, Watch tracking and quiz gating
The quiz now unlocks only after someone has actually watched enough of
the video; seeking to the end no longer counts. Every request gets a
viewer_id (a new ViewerIdentityMiddleware sets a one-year httpOnly
cookie for anonymous visitors, read via a get_viewer_id dependency
everywhere else), and a watch_progress table (unique on lesson_id +
viewer_id, optionally carrying user_id) tracks watched_seconds against
a new required_watch_ratio on lessons (default 90%, admin-editable as
a percentage). The player sends a heartbeat roughly every 10 seconds;
app/services/watch.py credits time only when the gap since the last
heartbeat is at least 8 seconds, the position has advanced by no more
than 15 seconds, and the position is within the lesson's duration —
credit is the smaller of the position delta and the wall-clock delta.
A backward jump (a rewind) resets the comparison point without
crediting anything, and POSTs faster than about one every 5 seconds
get a 429 rather than silently no-opping, both proven out with a
FLOOD and a SKIP test. A signed-in user's progress is looked up by
viewer_id OR user_id, so it follows them to a new device once they're
signed in on it. POST /lessons/{slug}/attempts now 403s with how much
video remains when the gate isn't met, checked via the same
is_unlocked function the frontend reads from; admins bypass it
entirely so authoring can be tested without watching. The quiz
delivery endpoint (GET .../quiz) was deliberately left open rather
than gated too — nothing sensitive lives there since it already omits
is_correct, and gating it as well would only complicate the "preview
the questions" case for no real security benefit. On the frontend,
VideoPlayer throttles heartbeats to actual playback (stopped on
pause, flushed on ended and on tab-hide via visibilitychange) and
renders a plain-text progress bar; LessonDetail's "Take the quiz"
button reads that same progress live and swaps from a disabled
explanation to the real link the moment the threshold is crossed, no
refresh needed. Reaching the quiz URL directly while still gated shows
the server's own explanation with a link back to the lesson instead of
a bare 403. A lesson with no duration_seconds can't gate by
definition, so it's simply ungated, with a warning surfaced in the
admin editor when duration is missing. Feature 012's per-second
heatmaps and resuming playback where you left off remain out of
scope; so does retroactively applying the gate to attempts completed
before this feature shipped.

## 2026-08-06, Feature 012, Question analytics and retake policy
An admin can now see which questions people get wrong and where they
drop off, and retaking a quiz no longer replays the same five
questions in the same order. Added shuffle_seed to attempts (a random
int generated on attempt creation) plus retake_cooldown_minutes and
max_attempts to lessons; also added viewer_id to attempts (not called
out in the original data-model note, but required to count anonymous
retakes by the feature 011 cookie the same way signed-in ones are
counted by user_id). app/services/quiz.py derives question and choice
order deterministically from the seed (a folded seed+salt int, since
random.Random only accepts a single scalar) — GET .../quiz now takes
an optional attempt_id and serves shuffled order for it, authored
order without it; the leak test still passes since ChoicePublic is
built the same way either way. app/services/attempts.py enforces the
retake policy in start_attempt before creating a row: max_attempts
compares completed-attempt counts, the cooldown compares against the
most recent completed_at, both keyed by user_id when signed in and by
viewer_id otherwise (a cleared cookie resets an anonymous viewer's
count — noted in the code as accepted for now), and admins bypass
both, both returning 429. app/services/analytics.py is four read-only
aggregate queries (lesson_stats, question_stats, choice_distribution,
dropoff) straight from attempt_answers, no new reporting tables,
exposed as GET /admin/lessons/{id}/stats behind require_admin.
Frontend: a new /admin/lessons/:id/stats page (linked from the lesson
list and editor) with a summary row, a worst-first question table
flagging anything under 40% correct, expandable per-question choice
distributions, and a drop-off list, showing a plain message instead
of an empty table when a lesson has no attempts yet; the Quiz page
now starts the attempt before fetching the quiz so it can pass
attempt_id along, and reads a 429's detail message on both the locked
(watch gate) and limited (retake policy) paths; the lesson editor's
Details form exposes retake cooldown and max attempts with helper
text explaining that blank means unlimited. Question banks larger
than five with random selection, per-user analytics and exports, and
charts beyond a plain table remain out of scope.

## 2026-08-07, Feature 013, Sign in with Google
A visitor can now sign in or register with a Google account and land in the
exact same session mechanism as a password account: Google only replaces the
identity check, then the existing create_session/_set_session_cookie takes
over untouched. Added google_sub (unique, nullable) to users and made
password_hash nullable for Google-only accounts, plus three optional
GOOGLE_CLIENT_ID/SECRET/REDIRECT_URI settings that make /auth/google/start
404 (and the frontend button disappear via the same failure mode) when
unset, so a half-configured deploy fails visibly. app/services/google_auth.py
keeps every authlib and HTTP call contained to that one module: it builds
the authorization URL, exchanges the code and verifies the ID token's
signature against Google's JWKS, and resolves identity in the required
order — match google_sub, else match a verified email and link, else create
a new user with password_hash NULL. An unverified email on an existing
address is refused rather than linked, which is the account-takeover trap
this feature is built around. GET /auth/google/start and
/auth/google/callback are the only new routes, both redirects rather than
JSON since the browser arrives from Google, not apiFetch; state is a random
token round-tripped through a short-lived httpOnly cookie, and any failure
(state mismatch, bad code, unverified email) redirects to
/login?error=<code> instead of a bare 400. Fixed a latent bug this feature
would otherwise have exposed: auth_service.authenticate() called
verify_password(password, user.password_hash) unconditionally, which would
have thrown on a Google-only account's None hash; it now falls through to
the same dummy-hash comparison as a missing user, so a password attempt
against a Google-only account is a uniform-timing 401, not a 500 or an
oracle for which addresses are Google-only. On the frontend, a new
GoogleButton component (full page redirect to /auth/google/start, not
apiFetch) sits above the existing form on both Login and Register with a
Google-brand-styled button and an "or" divider; AuthContext's existing
getMe()-on-mount needed no changes to pick up the session after the
callback redirects back. Apple/GitHub/Microsoft sign-in, unlinking Google,
adding a password to a Google-only account, and refresh tokens/storing
Google access tokens remain out of scope; the last two need a password
reset flow that doesn't exist yet.

## 2026-08-07, Feature 014, Header cleanup and password field polish
The feature 001 backend status pill is gone from the header (and its
App.jsx health-check polling and src/api/health.js with it), leaving just
the wordmark and auth nav; GET /api/v1/health itself is untouched. A new
shared PasswordInput component (inline SVG eye toggle, per-field
visibility state, type="button" to avoid submitting the form it sits in)
replaces the bare password inputs on Login and Register, and Register
gained a Confirm password field validated on submit — after name length
and password length — with "Passwords do not match." reusing the
existing validate() rather than a second path. Password reset, strength
meters, and a frontend test framework remain out of scope.

## 2026-08-11, Feature 015, Watch progress correctness
Closed the leak where two people signing into the same browser inherited
each other's watch history: app/services/watch.py resolved progress by
`viewer_id OR user_id`, so a signed-out user's cookie still matched the
next person's row. Progress is now resolved by identity, not union —
signed in matches `user_id` alone, anonymous matches `viewer_id` alone
among unclaimed (`user_id IS NULL`) rows — in one function,
`_identity_filter`. Migration 6f58cd9b86ef swaps the old
`(lesson_id, viewer_id)` unique constraint for two partial unique
indexes, one per identity, after collapsing any pre-existing duplicate
rows by `user_id`; `downgrade -1` restores the original constraint.
`viewer_id` now rotates on sign out (defence in depth), and
`claim_anonymous_progress()` folds a browser's anonymous progress into
the account at sign in — register, login, and the Google callback all
call it before responding, taking the larger `watched_seconds` when the
user already has their own row so a returning viewer never loses
progress. On the frontend, the watch readout now measures against the
lesson's full duration instead of the unlock threshold (no more "5:09 of
4:41"), swapping to a plain "Watched" state once unlocked; the progress
bar is driven by the video's own `timeupdate` event for smooth movement,
reconciled to the server's value on every heartbeat response, while the
heartbeat POST cadence itself is unchanged. Requiring sign-in to take a
quiz and resuming playback where a viewer left off remain out of scope.

## 2026-08-11, Feature 016, Require sign in to take a quiz

`POST /lessons/{slug}/attempts` now requires a signed-in user — a
signed-out request gets 401 before the watch gate or retake policy are
even checked, so a visitor is told to sign in rather than how much
video is left. The retake-policy keying dropped its `viewer_id`
fallback since every new attempt now has a `user_id`; `attempts.user_id`
itself stays nullable and every downstream endpoint (answering, reading
a result, claiming a certificate) is still unguarded, so historical
anonymous attempts and their certificates keep working exactly as
before. On the frontend, `LessonDetail` swaps the quiz button for a
"Sign in to take the quiz" link (to `/login`, carrying `state.from` back
to the lesson) whenever there's no signed-in user, and renders a neutral
state while `AuthContext` is still resolving so a signed-in visitor
never sees the prompt flash. `Quiz` redirects straight to `/login` with
the same `from` state if reached directly while signed out, instead of
rendering an error. The anonymous name-entry form on `Result` is
unreachable for new attempts but stays in place for old certificate
links.

## 2026-08-11, Feature 017, Authoring UX
Authoring a lesson stops tripping the author over gaps between what the
form shows and what the server actually requires. Backend: `POST
/admin/lessons/{id}/publish` gained a `dry_run` query flag that runs the
same `validate_for_publish` and returns `{"errors": [...]}` without
touching `is_published`, so the frontend has a side-effect-free way to
read the same rules instead of a second copy of them. On the frontend,
`VideoUploader` reads `video.duration` off an offscreen `<video>` element
on file selection (object URL created and revoked, value rounded down)
and hands it up to `DetailsForm`, which fills the still-editable duration
field and marks it as auto-filled until the author types over it.
`DetailsForm` also lifts its existing dirty check up to
`AdminLessonEditor`, which now disables Publish with "Save your details
first." while dirty, and warns via `beforeunload` (plus a confirm on the
in-app "All lessons" link) whenever details are unsaved or a video
upload is running — uploading no longer blocks editing questions or
details, replaced a blocking progress bar with an "Uploading… N%" /
"Processing…" status line, and says plainly that leaving cancels it. A
new shared `FileInput` component (visually-hidden input behind a real
`<label for>`, focus-visible on the styled button, selected filename
shown beside it) replaces the bare `<input type="file">`. `PublishPanel`
now renders a permanent six-item checklist (title, slug, description,
video, five questions, one correct choice each) driven entirely by the
dry-run error list, ticking items off as edits are saved rather than
only speaking up after a failed publish click. Queued/background
uploads, transcoding, and thumbnails (feature 018) remain out of scope.

## 2026-08-11, Feature 018, Lesson thumbnails
A lesson now carries a `thumbnail_key` (nullable, added via migration
`af95594e5536`), mirroring `video_key`: private object in Spaces, served
through a presigned GET, `lessons/<slug>-thumb.<ext>` since the
extension varies with upload. `POST /admin/lessons/{id}/thumbnail`
validates the declared content type, caps the file at 2 MB, then opens
the bytes with Pillow (added as a direct dependency; it was already
pulled in transitively by reportlab) to confirm they actually decode as
the claimed JPEG/PNG/WebP — the declared content type alone is a
browser guess off the filename, so a PDF renamed to `.jpg` would
otherwise sail through. A non-16:9 upload is accepted with a `warning`
in the response rather than rejected. Replacing a thumbnail overwrites
the old object (`storage.delete_object`, new) when the extension
changes rather than leaving it behind. `GET /lessons/{slug}/thumbnail-url`
mirrors `video-url` (404 when unset, 3600s expiry); `LessonSummary`
gained a `has_thumbnail` bool (a `Lesson.has_thumbnail` property) so the
list page knows whether to fetch a URL without a presign per card.
Frontend: `LessonCard` reserves a 16:9 box via `aspect-ratio` (plain
placeholder when there's no thumbnail, so the grid never reflows) with
`alt` set to the lesson title since the card is a link; `VideoPlayer`
sets `poster` from the same endpoint, fixing the black rectangle before
playback. `AdminLessonEditor` gained a `ThumbnailUploader` beside
`VideoUploader`, reusing `FileInput` from feature 017; it previews the
just-picked file immediately via `URL.createObjectURL` (so upload and
replace both show without a hard refresh, independent of publish
state) and surfaces the aspect-ratio warning inline. Thumbnail
generation from a video frame, multiple sizes/`srcset`, and a CDN
remain out of scope.

## 2026-08-12, Feature 019, Courses as the credit-bearing unit
The unit a person completes is now a course, not a lesson — the structural
change the 2026 CPE compliance work depends on. Both databases were
confirmed empty right before this shipped (0 rows in `attempts` and
`lessons`), so migration `05e053f86e0a` adds `courses`, moves `lessons`
under it (`course_id` FK not null, `position` unique per course, `slug`
still globally unique), and swaps `attempts.lesson_id` for
`attempts.course_id`, all with no backfill logic — the migration's own
docstring says why. `retake_cooldown_minutes`/`max_attempts` moved from
lessons to courses (a person retakes a course); `watch_progress`,
`questions`, and `choices` stay exactly where they were, deliberately.
`PASS_THRESHOLD = 4` is gone, replaced by `PASS_RATIO = 0.8` applied to a
course's total published-lesson question count and rounded up
(`math.ceil`) — identical behaviour on a five-question course (4/5) and
the generalised case proven with a fifteen-question course (12/15 passes,
11/15 doesn't). Backend: a new `app/services/courses.py`
(`list_published`, `get_by_slug`, `get_with_lessons`, plus
`published_question_count`, `get_published_lesson`, and
`get_lesson_in_course` for the segment page's prev/next links) backs a new
`app/routers/courses.py` that replaces `lessons.py`/`quiz.py`/`watch.py`
outright: `GET /courses`, `GET /courses/{slug}`, `GET
/courses/{slug}/lessons/{lesson_slug}` (+ its `video-url`/`thumbnail-url`/
`watch`), `GET /courses/{slug}/watch-status` (new — per-lesson progress
plus one `gate_met` bool from `watch.course_watch_status`, which just
reuses `get_progress`'s existing "no duration means unlocked" rule rather
than re-deriving it), `GET /courses/{slug}/quiz`, and `POST
/courses/{slug}/attempts`. `quiz.get_quiz_for_course` walks every
published lesson's published questions in lesson-then-question order for
free, since both relationships are already position-ordered — no extra
sort, and the leak test moved over unchanged. `attempts.start_attempt`
keeps feature 016's authenticate-then-gate-then-policy order, now against
a course, and a locked assessment names the specific outstanding segment
(`WatchRequirementNotMetError` carries its slug/title) rather than a bare
second count. `admin_content.py` gained full course CRUD, `create_lesson`/
`move_lesson`/`delete_lesson` nested under a course (reusing the existing
two-phase `_renumber` unchanged), and `validate_for_publish` now walks a
course: title/slug/description, at least one lesson, every lesson has a
video and at least one question, and the feature 010 per-question rules —
still one flat list of every failure at once. Publishing a course also
flips every one of its lessons to `is_published = True` in the same
transaction (there's no separate per-lesson publish action any more —
`validate_for_publish` already proved each one was complete); this was
caught by a test that actually re-fetched the public quiz after
publishing rather than only asserting `course.is_published`. Deleting a
course with completed attempts still 409s exactly as a lesson used to;
deleting a lesson now checks its *course's* attempts, so a segment can't
be pulled out from under an already-graded assessment either.
`app/services/analytics.py` re-keys its four aggregates on `course_id`,
and `question_stats`/`dropoff` now carry `lesson_title` per row (dropoff
groups by `question_id`, not raw position, since position resets inside
each lesson) so the admin can see which segment a bad question or a
drop-off point belongs to. Frontend: `CourseList`/`CourseDetail` replace
`LessonList`/`LessonDetail` (`CourseCard` reuses `LessonCard`'s 16:9 shape
plus a segment count), a new `LessonSegment` page plays one segment with
previous/next links, and `Quiz`/`Result`/`Progress`/`Verify` all take a
course slug and `course_title` now. `AdminCourseList` and a new
`AdminCourseEditor` (details, a generalised `ThumbnailUploader` moved to
`components/` so both course and lesson can reuse it, an ordered
`LessonsPanel` with add/move, and `CoursePublishPanel`) wrap the existing
`AdminLessonEditor`, which lost its own publish panel and now links back
to its course. The old `/lessons/:slug` routes are gone outright, no
redirect layer — there was no live traffic to preserve. Verified against
a real dev database end to end in a browser (Playwright): author a
three-lesson course, reorder it, publish it, watch all three segments as
a signed-in user, confirm the assessment button stays locked until every
segment is watched and names which one is outstanding, pass a
fifteen-question run at 12/15, and download the resulting certificate.
Learning objectives/program level/field of study (020), the development
and review chain (021), credit calculation (022), and splitting review
from assessment questions with a per-course pass threshold column (023)
remain out of scope.

## 2026-08-12, Feature 020, Program metadata and learning objectives
New `learning_objectives` table (`course_id` FK ondelete CASCADE, unique
`(course_id, position)`, `text`) plus four columns on `courses`:
`program_level`, `field_of_study` (both plain `String` with a hand-added
`CHECK` constraint and a Python constant, not a native Postgres enum —
NASBA revises these lists on its own schedule, and altering a native
enum in a migration is far more friction than editing a constant),
`prerequisites`, and `advance_preparation` (both nullable `Text`).
`app/constants/program_levels.py` and `app/constants/fields_of_study.py`
hold the allowed values, transcribed from
`docs/2026-Statement-on-Standards-for-CPE-Programs.pdf` and
`docs/2024-Fields-of-Study-Document.pdf` (both added to `docs/` this
feature) rather than from memory; fields of study carry a
technical/non-technical split alongside each value for a future
per-state non-technical credit cap, plus a `non_cpe` ("Not CPE
eligible") sentinel that's abacadaba's actual default, since its
content is deliberately non-financial. `admin_content.py` gained
`create_objective`/`update_objective`/`delete_objective`/
`move_objective`, reusing the existing two-phase `_renumber` unchanged
rather than a second implementation. `validate_for_publish` gained five
rules: at least one non-blank objective, a valid `program_level`, a
non-blank `field_of_study`, and — the one with real logic — Intermediate/
Advanced/Update courses must have both `prerequisites` and
`advance_preparation` non-empty (3.02.1's conditional-on-another-field
requirement), while Basic/Overview may leave both blank. `GET
/courses/{slug}` now returns all five pieces of metadata in the public
payload — the actual disclosure requirement, not just an admin-side
add. Two new unauthenticated endpoints, `GET /meta/fields-of-study` and
`GET /meta/program-levels`, feed the admin selects from the server
instead of duplicating NASBA's lists in JavaScript. Frontend:
`AdminCourseEditor` gained an `ObjectivesPanel`/`ObjectiveRow` pair that
reuse `QuestionsEditor`/`QuestionEditor`'s CSS modules directly rather
than forking them, and `CourseDetailsForm` gained a program-level
select, a field-of-study select with Technical/Non-technical `optgroup`s
("Not CPE eligible" first, selected by default for new courses),
and two textareas. `CourseDetail` renders a "What you will learn" list
and a program-details block — rendering literal "None" for blank
prerequisites/advance preparation rather than omitting the row, since
3.02.1 asks for a stated none — above both the lesson list and the
assessment button, so it's pre-enrollment disclosure rather than
something found after starting. `CoursePublishPanel` needed no changes:
the new failures surface automatically through its existing
`publishErrors` list, confirming feature 017's checklist design has no
gap here. Verified against a real dev database end to end in a browser
(Playwright): added, reordered, edited, and deleted objectives on a
live course; set an Intermediate course's level with blank prerequisites
and watched Publish block with the exact two missing-field messages;
filled them in, set field of study via the grouped select, and
published; confirmed the signed-out public page shows objectives,
level, field of study, prerequisites, and advance preparation above the
assessment button; and confirmed a Basic course with both fields left
blank publishes and renders "None" for both on its public page. Objectives
on individual lessons, and the development/review chain's "most recent
publication, revision, or review date" (021), remain out of scope.

## 2026-08-14, Feature 020a, Dirty-tracking defects in the questions and objectives editors
`DetailsForm` already reported its dirty state up to the page-level
`hasUnsavedWork` (the `beforeunload` warning and the "Back" link's
confirm dialog); the row editors for questions, choices, and learning
objectives did not, even though each row already computed its own
dirty flag locally to enable its own Save button. Editing a question
prompt, a choice, or an objective and then navigating away without
clicking that row's Save lost the edit silently. Extended the same
`onDirtyChange` pattern one level deeper: `ChoiceRow` and `ObjectiveRow`
now report `(id, dirty)` up; `QuestionEditor` combines its own prompt
dirty state with the OR of its choices' into one signal per question;
`QuestionsEditor` and `ObjectivesPanel` aggregate their rows' signals
(dirty-id `Set`s) into a single boolean each and report it up via their
own `onDirtyChange`; `AdminLessonEditor`'s and `AdminCourseEditor`'s
`hasUnsavedWork` now OR in `questionsDirty`/`objectivesDirty` alongside
the existing `detailsDirty`/`uploading`. The three aggregator callbacks
(`QuestionsEditor`, `QuestionEditor`, `ObjectivesPanel`) needed
`useCallback` — without a stable identity, each child row's dirty-effect
depends on the callback reference, and a fresh function every render
put React into an infinite `setState`-in-`useEffect` loop
("Maximum update depth exceeded"), caught during manual browser
verification (Playwright) before shipping, not by lint or pytest. No
Save button moved, no save granularity changed — that's 020b, next.
Verified against a live dev database via a scripted Playwright session:
editing an objective, a question prompt, and a choice each independently
triggers the confirm dialog on navigating away when unsaved and does not
when clean or after that row's own Save is clicked; console stayed free
of repeated render-loop errors through all three. `npm run lint` and the
full backend `pytest` suite (183 tests, unchanged) both pass.

## 2026-08-14, Feature 020b, Authoring workflow
One save model, field labels, a restructured questions editor, an explicit
next step, and orientation text for an empty course — five presentation-only
fixes from watching one person author a course start to finish. All Details,
Objectives, Questions, and Choices edits are now held in client state and
committed by a single sticky `StickySaveBar` (new, `components/StickySaveBar`)
pinned to the bottom of each editor page, showing a live count of unsaved
changes and inert at zero; every per-row Save button (`ChoiceRow`,
`QuestionEditor`'s prompt, `ObjectiveRow`, `DetailsForm`, `CourseDetailsForm`)
is gone. Reaching this from 020a's per-row dirty booleans meant widening the
contract to counts and adding a matching commit path: each row now exposes a
`save()` via `useImperativeHandle` (fresh closure every render, since a
memoized handle would go stale the way the naive dirty-callback did in 020a),
and each aggregator (`QuestionEditor` over its choices, `QuestionsEditor` over
its questions, `ObjectivesPanel` over its objectives) holds a `Map` of child
refs alongside its `Map` of dirty counts and sums both on the way up; the
page's `handleSaveAll` calls whichever refs are actually dirty, awaits them
together, and only then refetches. Delete/Move/Add/upload stayed immediate —
uploads now say so explicitly in both `VideoUploader` and the shared
`ThumbnailUploader` ("saves immediately... unlike the rest of this page").
`ThumbnailUploader` gained `label`/`placementNote` props so the course and
lesson thumbnail sections read as what they are ("Course thumbnail — shown on
the course card in the catalog" vs "Lesson thumbnail — the poster frame shown
before this segment's video plays"); `CourseDetailsForm`'s description field
is now labelled "Course description" with a hint naming it the 8.01.1
pre-enrollment disclosure, and `DetailsForm`'s lesson description got its own
hint. In `QuestionEditor`, choices moved into a `.choicesBlock` — indented,
left-ruled, surface-tinted — so they read as belonging to their question
instead of just trailing it, and `QuestionsEditor` moved "Add question" (now
a textarea, matching a prompt's shape rather than a choice's single-line
input) into a dashed full-width block above the question list instead of
below the last one, so it can no longer sit directly under an "Add choice"
input. Objectives have no nested add-control, so no equivalent adjacency
existed there and `ObjectivesPanel` is unchanged in that respect.
`AdminLessonEditor` gained a "Next" section — reusing `checkAdminCoursePublish`
(previously course-editor-only) filtered to messages starting with `Lesson
'<this lesson's title>'`, stripped of that prefix — showing what's still
outstanding or confirming the lesson is publish-ready, plus a repeated "Back
to course" link, both above the danger zone. `CoursePublishPanel`'s per-lesson
failure messages now match that same `Lesson '<title>'` pattern against
`course.lessons` and render as links to `/admin/lessons/{id}` when a match is
found; its publish-blocked reasoning generalized from a details-only
`detailsDirty` prop to `hasUnsavedWork`, since unsaved objective edits are
just as stale-publish-worthy as unsaved details now. `LessonsPanel` shows
orientation text — what a lesson is, and that a course is one or more of them
in order — only while `course.lessons.length === 0`, replaced by the list
once one exists. Verified against a live dev database via a scripted
Playwright session covering both editors end to end: created a course,
confirmed the empty-lessons orientation text, edited a detail field and an
objective and saved both with one click, confirmed the unsaved-changes dialog
fires on a dirty question prompt and a dirty choice and clears after save,
confirmed a hard-reloaded page shows the persisted values (not just local
state), watched the lesson's "Next" section drop "must have at least one
question" once a question with two choices and a correct answer existed,
and clicked a lesson-named publish-checklist failure through to that lesson's
editor. `npm run lint` and the full backend `pytest` suite (183 tests,
unchanged — no backend file touched) both pass. This feature is entirely
presentation and client state in the admin tool; `ThumbnailUploader`, the one
shared component touched, is never used on the public course page, so no
participant-facing disclosure changed. COMPLIANCE.md gains no row: the
8.01.1 and 3.02.1 mappings from feature 020 are unchanged and still accurate
against `docs/2026-Statement-on-Standards-for-CPE-Programs.pdf`, and Part 2's
relabelling did not surface any field mapped in 020 that turned out to be
unrendered. 020a's three dirty-tracking defects, background/resumable
upload, bulk question import, and certificate design remain out of scope, as
specified.

## 2026-08-18, Feature 020c, Authoring hotfix
Three of the four defects reported after 020a/020b were real; the fourth —
"the course description does not persist" — was not reproducible against the
shipped code and nothing changed for it beyond a regression test. Before
touching anything, the described mechanism (batched save assembling its
payload from a dirty-tracking path that skips the description textarea) was
checked directly: `CourseDetailsForm`'s `dirty` computation and its `save()`
already include `description` unconditionally, and a live round trip — API
calls straight against `TestClient` and a full scripted Playwright session
against the real dev server (fresh course creation, a second edit on an
existing course, human-paced typing, SPA back-navigation instead of a hard
reload, an objective added mid-edit, a hard reload) — persisted the field
correctly every time, for every field on both the course and lesson details
forms. `tests/test_admin_content.py` gained
`test_update_course_round_trips_every_field_on_the_details_form_in_one_batch`
as the regression guard the feature asked for regardless. COMPLIANCE.md's
8.01.1 row needs no Gap update: the pre-enrollment disclosure it points at
works, and nothing suggests it stopped working between 020b and this feature.

Bug 2, quiz numbering, was real and was never fixed despite 020a's changelog
entry implying otherwise — 020a's actual entry (see above) covers only the
dirty-tracking defects, not this. The mechanism was exactly as suspected but
in a different layer than the hypothesis in this file guessed: `GET
/courses/{slug}/quiz` (`app/routers/courses.py`) built each `QuestionPublic`
with `position=question.position`, the question's authored/DB position,
even though the *list* it was iterating had already been reordered by
`shuffle_questions` — so `QuestionCard.jsx`, which has always rendered
`question.position` faithfully, was correctly displaying an incorrect number.
Fixed by numbering from the served order instead:
`enumerate(questions, start=1)` supplies `position` now, so it's 1..N in
whatever order (shuffled or not) the questions actually went out in — no
frontend change needed. `tests/test_shuffle.py` gained
`test_shuffled_question_position_matches_served_order_not_authored_order`,
using seed 7 (confirmed to reorder these five questions) as a regression
guard that fails against the pre-fix code. Verified in a browser as a signed
in non-admin: took a five-question quiz end to end, and the card's leading
number matched the progress bar's "Question N of 5" on every question.

Bug 3, the add-question control: kept it above the list (020b's fix for the
"Lava" mis-entry adjacency stands, unmoved). `QuestionEditor` now exposes
`focusPrompt()` via its imperative handle — scrolls its prompt textarea into
view and focuses it — and `QuestionsEditor` remembers the id `createAdminQuestion`
just returned, then calls that method once the refreshed `lesson.questions`
prop actually contains it. No workaround was needed for the page's scroll
container; plain `scrollIntoView` was sufficient. Verified in a browser:
adding a fifth question to a lesson that already had four scrolled the page
and left the new question's prompt textarea focused.

Bug 4, the vacuous publish check: `CoursePublishPanel` rendered its one
per-lesson rule ("every lesson has a video, at least one question...") as a
green check whenever `course.lessons` produced no per-lesson error messages —
true both when every lesson actually passed and when there were no lessons to
fail. Now branches on `course.lessons.length === 0` first and renders that
line `○` (neutral) in that case, `✓` only when there's at least one lesson and
none of them produced an error. Verified in a browser against a freshly
created, lesson-less course: the checklist showed `○` for both "at least one
lesson" and the per-lesson rule, no green check on either.

Backend: `app/routers/courses.py` (quiz numbering).
Frontend: `QuestionEditor.jsx`, `QuestionsEditor.jsx` (scroll/focus),
`CoursePublishPanel.jsx` (neutral checklist state). Tests:
`tests/test_admin_content.py`, `tests/test_shuffle.py`. `npm run lint` and
the full backend `pytest` suite (185 tests: 183 unchanged + 2 new) both pass.
COMPLIANCE.md gains no row and no Gap update: bug 1 turned out not to be a
defect, and bugs 2 through 4 are assessment-taking and admin-tool display/UX
correctness with no Standards locator to map to — confirmed against
`docs/2026-Statement-on-Standards-for-CPE-Programs.pdf`, not assumed.
Background/resumable upload, collapsing single-lesson courses, bulk question
import, certificate design, and any schema change remain out of scope, as
specified.

## 2026-08-18, Feature 020d, The save affordance
A shared `Button` component (`primary`/`secondary`/`danger`, plus a `disabled`
modifier that wins over every variant via the native `disabled` attribute) now
backs every button in the admin — no shared button module existed yet despite
the feature assuming one, so this feature created it rather than editing one.
The bottom save bar (`StickySaveBar`) is hidden when the page is clean and
slides in under 200ms when it becomes dirty, with `aria-live="polite"`; a
second Save button now sits in the page header next to the title, sharing the
same dirty/saving state and handler as the bar so there is one source of
truth. Course and lesson detail forms, and each objective/question/choice
row, mark the individual field that changed with a left border accent, using
the already-loaded server snapshot each form compares against (no new client
state was needed — 020b's batched state already held per-field original
values, not just a boolean). Cmd/Ctrl+S saves when dirty and is bound only on
the two editor pages. Leaving an editor with unsaved changes now blocks
in-app navigation via react-router's `useBlocker` (which required migrating
`main.jsx` from `BrowserRouter` to `createBrowserRouter`/`RouterProvider`,
since `useBlocker` only works under a data router) and `beforeunload` for tab
close/reload, as before. Video and thumbnail uploads remain outside the
batched save and do not dirty the bar. Verified in a live browser session
(Playwright driving a dev server): disabled Save renders grey/`not-allowed`
next to a light-purple enabled `Add lesson`, editing a field turns the header
Save solid purple and marks the field, dismissing the nav-guard confirm
keeps you on the page, Cmd+S saves and clears every marker, and the Publish
checklist reflects the save on a fresh fetch. Backend untouched;
`pytest` (185 tests) passes unchanged.
COMPLIANCE.md gains no row: this is an authoring-tool rendering and
interaction fix with no Standards locator to map to. Content silently
failing to save would touch Section 9's documentation requirements, but
that was never the defect here — the data was always saved correctly on
click, the author just couldn't tell.

## 2026-08-18, Feature 019a, The single-lesson course
A course with one lesson is now authored on one page and taken on one page,
with no schema change: whether a course renders collapsed is derived from
`len(course.lessons) == 1` on every render, never stored. `admin_content.create_course`
now creates lesson 1 in the same transaction (one `db.flush()` to get the
course id, one `db.commit()` at the end) — title copied from the course
title, position 1, and its slug generated by a new `_unique_slug` helper
that appends `-2`, `-3`, ... on collision, since the author never sees or
picks this slug and a 409 for something they didn't type would be worse than
the atomicity problem this feature exists to fix. `delete_lesson` now raises
a new `LastLessonError` (409, "This is the only lesson in its course. Delete
the course instead.") before it ever looks at completed attempts, mirroring
the existing attempts-based 409. **Backend task 3's finding:**
`validate_for_publish`'s per-lesson rules only ever check `lesson.video_key`
and `lesson.questions`/their choices — never `lesson.description` or
`lesson.thumbnail_key` — so nothing the collapsed page hides is something
publish requires. No rule needed to change, and none did.
Task 4's finding: no public payload change was needed either —
`LessonInCourse` already omits `video_key`, so `course.lessons[0].slug` from
the existing `GET /courses/{slug}` response is all the inline player needs;
it still fetches the actual video through the same gated `/video-url`
endpoint every segment page has always used. Extended the leak test
(`tests/test_courses.py`) with a dedicated single-lesson published course
asserting the payload carries the 020 disclosures and that no key on its one
lesson contains "video" in its name.

Frontend: `AdminCourseEditor` has exactly one branch, at the top, on
`course.lessons.length === 1` — everything else about which layout renders
follows from that single `singleLesson` value, not scattered conditionals.
Collapsed courses render a new `CollapsedLessonEditor` (reusing
`VideoUploader` and `QuestionsEditor` from the lesson editor unchanged, plus
a new `LessonVideoFields` for duration and required-watch-percentage and a
new `AddSecondSegmentControl`) in place of `LessonsPanel`; its one control's
label states the consequence before the click, verbatim: "Add a second
segment — this course will split into a course page and a page for each
segment." Clicking it creates lesson 2 (titled "Untitled segment," since the
control is a single click with no text field) and navigates straight to its
editor. `CourseDetailsForm`'s "Course description" label — the one 020b
disambiguation label that was hardcoded rather than prop-driven — now reads
plain "Description" when `collapsed` is true, since a collapsed page has
only one description field to disambiguate from nothing.
`CoursePublishPanel` drops the `Lesson 'X'` prefix from checklist messages
and stops linking them to a lesson editor when the course is collapsed, since
there's nowhere else to go and nothing left to name. `CourseDetail` renders
`VideoPlayer` inline for a single-lesson course in the same slot the lesson
list used to occupy — the objectives/program-level/prerequisites/advance-prep
block feature 020 placed above stays above it unmoved — and derives the
assessment gate directly from that player's own live progress rather than
the separate `watch-status` fetch, so it unlocks on the same page with no
navigation. `LessonSegment` now fetches the course first and redirects to
the course page when it has exactly one lesson, before ever calling the
segment endpoint, so old bookmarks and certificate links to
`/courses/:slug/lessons/:lessonSlug` land somewhere real instead of 404ing;
this is one extra fetch on both the single- and multi-lesson path, accepted
as cheap per the feature brief rather than pushed into a backend schema
change.

Existing `test_admin_content.py` tests that assumed a freshly created course
had zero lessons were updated to use the auto-created lesson instead of
adding a redundant second one (`_make_publishable_course` in particular);
`test_publish_with_no_lessons_returns_422` now deletes the auto-created
lesson directly via the DB first, since a zero-lesson course can no longer
be reached through the API and the rule is now purely defensive. New tests:
course creation yields exactly one lesson at position 1 with the course's
title; deleting the only lesson is refused and leaves both course and lesson
in place; deleting one of two lessons succeeds and leaves the right one
behind. No new backend test was added for "progress posted from the course
page satisfies the gate" specifically — `test_watch.py`'s `GATED_COURSE_SLUG`
fixture is already a single-lesson course, and its existing
`test_starting_an_attempt_at_the_threshold_succeeds` already proves a
heartbeat against a one-lesson course's lesson-watch endpoint opens that
course's gate; the watch gate itself is unchanged by this feature, so that
coverage already existed. Verified live in a browser end to end (Playwright
against the real dev server): creating a course landed on the collapsed page
with no Lessons panel and no link to a lesson editor; the publish checklist
showed unprefixed, unlinked messages; clicking "Add a second segment"
created and navigated to lesson 2 titled "Untitled segment," after which the
course editor showed a two-lesson `LessonsPanel`; deleting that second lesson
collapsed the editor back to one page automatically; deleting the sole
remaining lesson was refused inline with "This is the only lesson in its
course. Delete the course instead."; and a signed-out visit to a published
single-lesson course showed objectives, program level, field of study,
prerequisites, and advance preparation above an inline player, with the old
segment URL redirecting to the course page. `npm run lint` and `npm run
build` pass; the full backend suite passes at 189 tests (185 + 4 new).

COMPLIANCE.md gains no row: this feature changes where the player renders,
not what's disclosed or when. The 8.01.1 and 3.02.1 rows already cite
`CourseDetail.jsx` showing objectives, level, field of study, prerequisites,
and advance preparation before enrollment; the live-browser check above
confirms that's still exactly the render order on a collapsed page (the
disclosure block, then the player, then the gated assessment button) and no
Gap update is needed. This feature did not re-render
`docs/2026-Statement-on-Standards-for-CPE-Programs.pdf` locally to re-diff
its 8.01.1/3.02.1 wording byte-for-byte against those rows — the PDF-render
toolchain (`poppler`) isn't available in this environment and installing it
would have pulled a system-wide dependency upgrade for a documentation
double-check unrelated to the code change — but the docs directory is
untouched by this feature and those two rows already carry verbatim
quotes transcribed from that PDF by feature 020, so the only thing that
could have gone stale is the render order, which was verified directly.
Multi-lesson authoring, background/resumable upload, bulk question import,
the development/review chain, credit calculation, and certificate
content/design remain out of scope, as specified.

## 2026-08-18, Feature 021, Development and review chain
A published course now names who developed it, who reviewed it, and when -
and a course whose content has changed since its review cannot be
re-published until it is reviewed again. New `subject_matter_experts` table
(`app/models/subject_matter_expert.py`), deliberately with no FK to `users`
(see current-feature.md's reasoning: the reviewer is often an outside CPA
with no reason to ever hold an account, and the record answers a different,
longer-lived question than auth does): name, credentials, affiliation, bio,
`license_jurisdiction`, and the three booleans `is_licensed_cpa`/
`is_tax_attorney`/`is_enrolled_agent` that map one-to-one onto 4.02's own
sentence rather than a tidier derived enum. New `sources` table (course_id
FK cascade, position-ordered, reusing the existing two-phase `_renumber`
unchanged) for the citations a course was built from - recorded, not
required for publish. Six new columns on `courses`: `developer_id`/
`reviewer_id` (both FK subject_matter_experts, nullable), `reviewed_at`,
`review_notes`, `content_updated_at` (server-defaulted `now()` so the one
existing course in the dev database, unpublished, got a value rather than
breaking), and `review_cycle` (CHECK `'annual'`/`'biennial'`). Migration
`561ad5e4ce3d` hand-adds two CHECK constraints past what autogenerate wrote:
`reviewer_id <> developer_id` (unless either is null) and the review_cycle
enum; `downgrade -1` verified. The dev database's one existing course was
already unpublished, so nothing was left retroactively failing the new
publish rules.

`app/services/admin_content.py` gained one choke point,
`touch_content_updated_at`, called from every write path that changes what
a participant would see - course fields, objectives, lessons, questions,
choices, and (from the two upload routes in `app/routers/admin.py`, which
write directly rather than through this service) video and thumbnails - and
called from nowhere else: not developer/reviewer/reviewed_at/review_notes,
not sources, not publish/unpublish. That exclusion is the feature; getting
it wrong makes `reviewed_at < content_updated_at` true the instant after
every review and publish refuses forever. `validate_for_publish` gained
seven rules: developer required, reviewer required, they must differ (the
database CHECK is the backstop, this produces the message), review date
required, `reviewed_at >= content_updated_at` ("This course has changed
since it was reviewed"), and the 4.02 CPA/tax-credential participation
rules for accounting-and-auditing and taxes courses, reading a
`credential_tag` now carried on each `FieldOfStudy` entry in
`app/constants/fields_of_study.py` (a dataclass replacing the old flat
string lists, so the tag lives on the field itself instead of a second list
that could drift) via a new `credential_tag_for()` lookup.
`/meta/fields-of-study` now serves `{name, credential_tag}` objects instead
of bare strings, which required updating `CourseDetailsForm.jsx`'s
field-of-study `<option>` rendering - missed on the first pass and caught
live in browser verification as a hard crash ("Objects are not valid as a
React child"), not by lint or pytest. SME CRUD sits under `require_admin`
at `/admin/smes`; deleting one in use as a developer or reviewer is refused
with a 409 rather than a raw FK violation. Source CRUD is nested under a
course. `GET /courses/{slug}` now carries `reviewed_at` and `developer`/
`reviewer` (name and credentials only - bio and affiliation stay internal),
served via a small `SMESummary` dataclass in `app/services/courses.py`
rather than exposing the ORM row.

Frontend: a new `/admin/smes` page (`AdminSMEList`/`SMERow`/`SMEForm`) is
plain list/create/edit, immediate-effect like the rest of this codebase's
admin CRUD, not part of any batched save. `ReviewPanel.jsx` joins the
course editor's existing single `StickySaveBar`/header-Save batch exactly
like `CourseDetailsForm`/`ObjectivesPanel` do (verified live: one Save
click persists a content-field edit and a developer/reviewer/date change
together) and renders `SourcesPanel` beside it per the placement decision
in current-feature.md - a reviewer signing off next to an empty source
list should have to notice. `ReviewPanel` sits directly on
`AdminCourseEditor`, above the branch between `LessonsPanel` and
`CollapsedLessonEditor`, so both course layouts get it for free. The stale
state renders inline in the Review panel, not only in the publish
checklist, which gained three permanent rows (Developer/Reviewer/Review
date) alongside the existing conditional-message pattern the same-person,
staleness, and credential rules already fit without a frontend change (the
019a/020 checklist design held again). `CourseDetail.jsx` renders "Last
reviewed <date>" plus "Developed by"/"Reviewed by" lines with name and
credentials, above the assessment button.

Verified live against a real dev database end to end via a scripted
Playwright session (this environment has no `chromium-cli`; a throwaway
local `npm install playwright` sufficed): created two subject matter
experts, watched the publish checklist show Developer/Reviewer/Review date
as outstanding, filled in the Review panel and a source, saved with one
click, watched all three turn green while the video/question rules stayed
outstanding, uploaded a video and a two-choice question, watched the
checklist correctly go stale ("This course has changed since it was
reviewed") because those edits postdated the recorded review, re-recorded
the review, published, and confirmed the public course page rendered the
last-reviewed date and both experts' names and credentials. That session
caught two real bugs before they shipped: the field-of-study crash above,
and a second one worth calling out because current-feature.md warned
about its exact shape without naming this cause - `ReviewPanel.jsx`'s
`save()` sends `review_cycle` in the same request as `reviewed_at` (it
sends the whole panel, matching every other batched form in this
codebase), so leaving `review_cycle` out of `REVIEW_CHAIN_FIELDS` meant
every single review-save re-bumped `content_updated_at` a moment after
writing `reviewed_at`, staling the review that same request created.
Fixed by adding `review_cycle` to the excluded set; the existing
`content_updated_at`-stability test was strengthened to PATCH all five
review fields together, the way the real panel does, rather than only
three of them, so it would have caught this. Confirmed the strengthened
test fails against the pre-fix code and passes after.

The overdue-review dashboard (feature 026), instructor qualifications
(4.03, no instructor exists for a self study program), program evaluations
(4.04, feature 025), purchased-content review (4.06, nothing is purchased),
credit measurement (feature 022), and an approval workflow beyond the
recorded developer/reviewer fact remain out of scope, as specified.

## 2026-08-20, Video pipeline 01, Narration generation with measured reveals
`video/scripts/generate-audio.ts` is now wired in as `npm run generate`,
replacing the manual ElevenLabs-plus-`npm run measure` flow. Narration may
contain `[[r]]` reveal markers, stripped before TTS and located in
ElevenLabs' character-level alignment data to produce exact reveal seconds.
`video/src/audio-meta.json` (replacing `durations.json`) carries measured
duration, reveals, and a content hash per block; `lesson-01.ts`'s
`durationOf`/`revealsOf` fall back to the hand-written estimate/`reveals`
array until a block has been generated. Fixed a bug where `usingEstimates`
counted the narration-less title sheet, which made the estimated-duration
warning in `Root.tsx` permanently unable to clear. `AUDIO_PRESENT`
(`Lesson.tsx`'s hand-maintained map) and `measure-audio.mjs` are retired.
Only block-01 is marked up with markers, as a proof of the approach; blocks
02-07 are unchanged, deliberately. This is build tooling in `video/`, not
an app feature — it produces the accurate A/V runtime that feature 022's
credit calculation will eventually consume, but does not compute or store
credit itself.

## 2026-08-21, Video pipeline 02, Multi-lesson support and data-driven slides
The `video/` package renders more than one lesson now. `video/src/lessons.ts`
maps a lesson id to its module (`{ "01": lesson01, "02": lesson02 }`);
`Lesson.tsx` takes `lessonId` as a prop and resolves through that map instead
of importing `lesson-01` by name, `Root.tsx` registers `Lesson01` and
`Lesson02` as separate compositions with durations derived from each lesson's
own `totalSeconds`, and `npm run render:02`/`generate:02` drive lesson 02
the same way the existing scripts drive lesson 01. `generate-audio.ts` gained
`--lesson <id>` (default `01`), selecting which module's blocks to read,
which `audio-meta*.json` to write, and which `public/audio/<id>/` directory
to write into; lesson 01's seven existing mp3s moved to `public/audio/01/`
via `git mv` (renames, not delete-plus-add) and lesson 02 gets its own
`audio-meta-02.json` (currently `{}` — one file per lesson, not a nesting
level inside the existing one).

`slides.tsx` gained six generic, data-driven components — `Statement`,
`Facts`, `Calc`, `List`, `Compare`, plus `Title` extended to take `meta` as a
prop instead of importing lesson-01's — each reading a `figure` payload off
its block and revealing its elements one per `reveals` entry via the existing
`revealAt` helper; a row or item past the end of the marker count reveals
alongside the last one that has its own marker, rather than needing a marker
per row. `Sheet.tsx` also takes `meta` as a prop now instead of importing it.
**Lesson 01's own slide components (`Misconception`, `LegacyBranch`,
`FiveSteps`, `Fork`, `Criteria`, `Methods`, `Summary`) were deliberately not
migrated onto the generic set** — their reveals are indexed positionally
against measured audio already captured in `audio-meta.json`, and
re-rendering lesson 01 against different components would invalidate that
timing and change a video that is already correct. Both sets of components
live side by side in `SLIDES`. No lesson-01 audio was regenerated.

`lesson-02.ts`, committed earlier but wrong in four ways, is fixed: the
separate `speech` field is gone (`narration` is now the only copy of the
transcript and carries the `[[r]]` markers, moved over at the same word
positions), every block gained a `reveals` fallback array sized to its
marker count and evenly distributed across `estimatedSeconds` as a preview
placeholder only, `estimatedSeconds` is recomputed at 130 wpm (the constant
`lesson-01.ts` documents; these blocks were originally written at 145), and
the file exports `transcriptOf`/`speechOf`/`hasAudio`/`durationOf`/
`revealsOf`/`usingEstimates`/`totalSeconds` reading from a new
`audio-meta-02.json`, matching lesson-01's module shape closely enough for
`Lesson.tsx`/`Root.tsx`/`generate-audio.ts` to treat either lesson
generically. `lesson-02.ts` stays `DRAFT — NOT REVIEWED`; its audio was not
generated as part of this feature, pending a licensed CPA's read of the
narration and arithmetic (4.01.1, 4.02).

Verified: `npx tsc --noEmit` clean; `npm run generate -- --dry-run` reports
7 unchanged blocks for lesson 01; `npm run generate:02 -- --dry-run` reports
11 narrated blocks (title has no narration) and spends nothing; `npm run
render` was diffed frame-by-frame against the pre-feature `out/lesson-01.mp4`
at eleven timestamps spanning S-01 through S-07 (`ffmpeg`'s `ssim` filter,
`All:1.000000` at every sample — pixel-identical, matching frame count and
duration) rather than judged by reading the diff; `npm run render:02`
produces a silent twelve-sheet MP4 with every figure element visible by the
end of its block; `npx remotion compositions` shows the estimated-duration
warning firing for `Lesson02` and not `Lesson01`; `git status` shows the
seven moved lesson-01 audio files as renames.

Out of scope, flagged rather than built: the `Title` slide's "LESSON 1 OF 5"
caption is still a hardcoded string (no lesson-number field exists in
`meta`), so it reads the same on lesson 02's title card — neither
`current-feature.md` nor lesson-01's `meta` shape asked for one, so no field
was invented for it here.

COMPLIANCE.md gains no row: this is build tooling (lesson selection,
generic slide rendering, script plumbing), and the 7.02.7 mapping recorded
under Video pipeline 01 is unchanged — `durationOf`/`totalSeconds` still
measure real narration length ahead of the estimate, per lesson, and
`Root.tsx` still warns per composition rather than gating render or publish.

## 2026-08-23, Feature 022, Credit measurement

A course now knows how many CPE credits it is worth, with the arithmetic
that produced the number stored and visible, not just the answer. Two new
`lessons` columns (`av_is_additional_learning`, default true; `word_count`,
default 0) and seven new nullable `courses` columns
(`credit_award`/`credit_raw_minutes`/`credit_word_count`/`credit_av_seconds`/
`credit_question_count`/`credit_formula_version`/`credit_computed_at`), added
via migration `d204728bf964` (`downgrade -1` verified). `app/constants/credit.py`
names every number the 2026 Standards chose (`WORDS_PER_MINUTE = 180`,
`MINUTES_PER_QUESTION = Decimal("1.85")`, `MINUTES_PER_CREDIT = 50`,
`MIN_AWARDABLE = Decimal("0.2")`) plus `CREDIT_FORMULA_VERSION`, so a stored
credit always records which formula produced it. `app/services/credit.py`
holds the whole formula: `compute()` is pure and read-only, `round_down()`
floors to the finest legal self study increment (one-fifth, 7.01) and never
rounds up, and `store()` writes the seven columns and stamps
`credit_computed_at` only when explicitly called — never from a content edit,
so a course's credit doesn't shift mid-edit the way 021's review date
doesn't either. Confirmed feature 017's auto-fill (`VideoUploader.jsx`
reading the browser's own `video.duration` off the uploaded file) is what
populates `duration_seconds`, not a typed estimate — the one place the app
can defend the "actual" in "actual audio/video duration time."

`validate_for_publish` gained three rules: credit must be computed and not
stale (`credit_computed_at is None or credit_computed_at < content_updated_at`,
derived exactly like 021's review staleness — no stored boolean), the award
must be at least 0.2 with a message naming the shortfall in seconds rather
than "too short," and every lesson whose runtime counts toward credit must
have a duration. The seven `credit_*` fields joined 021's
`REVIEW_CHAIN_FIELDS` exclusion set (now covering review-chain and credit
fields alike) so recomputing never itself makes the credit stale; extended
021's `content_updated_at`-stability test to PATCH all seven credit fields
together, per current-feature.md's note about exactly this class of bug.
`GET`/`POST /admin/courses/{id}/credit` read the last-stored breakdown and
recompute-and-store one, respectively; `GET /courses/{slug}` now carries
`credit_award` as a pre-enrolment disclosure, alongside program level and
field of study.

**Deviation from the letter of current-feature.md's Task 4:** the question
count (and the word/A-V terms) sum over every lesson of the course, not
`courses_service.published_question_count`'s `Lesson.is_published`-gated
count as instructed. `publish_course()` only flips lessons to published
after `validate_for_publish` passes, so gating credit's own inputs on that
same flag would make a course's first-ever publish permanently unreachable
and would compute 0 credit for the feature's own worked example (486s +
8 questions). Resolved with the user's explicit sign-off; documented at the
count's call site in `app/services/credit.py::compute` and in COMPLIANCE.md's
Gap column for 7.02.6.

Frontend: a new `CreditPanel.jsx` in `AdminCourseEditor` shows a per-segment
table (runtime, additional-learning flag, word count) then every term of
the arithmetic — words ÷ 180, A/V minutes, questions × 1.85, the sum, ÷ 50,
the raw credit, and the rounded award — sourced from the dedicated GET/POST
endpoints, with a stale banner worded like 021's ("this course has changed
since credit was last computed") and its own Recompute button, outside the
page's batched save since credit is derived, not typed. `LessonVideoFields.jsx`
and `DetailsForm.jsx` (multi-lesson courses duplicate this logic rather than
sharing it, matching the codebase's existing pattern) both gained the
additional-learning checkbox, labelled "This segment's audio teaches
something the slides don't say" rather than the Standard's own wording, plus
a word-count field that appears only when unchecked. `CoursePublishPanel.jsx`
gained a "Credit is up to date" checklist line and an extended per-lesson
message covering the new duration requirement. `CourseDetail.jsx` shows the
credit alongside program level and field of study.

Verified against a real dev database end to end in a browser (Playwright):
authored a course with a 486-second video and 8 questions, watched the
Credit panel compute 0.4 credit matching the arithmetic on screen exactly,
confirmed Publish was blocked until credit was computed and un-stale,
published, and confirmed the public course page showed "0.4 credit" to a
signed-in visitor's disclosure block. Unchecked a segment's
additional-learning flag, confirmed the word-count field appeared and a
large duration on that segment was correctly excluded from the A/V term
(covered as a pytest case too, since narration segments are easy to get
backwards). Backend: 235 tests pass, including new `tests/test_credit.py`
(all-video and mixed narration cases, rounding never rounding up, the
below-0.2 refusal message, staleness appearing after a question edit and
clearing after recompute, publish refused when a counted segment has no
duration, and the public payload carrying the credit) and the extended
review/credit `content_updated_at`-stability test. `npm run lint` and
`npm run build` pass.

Pilot testing (7.02.1–7.02.4), adaptive-path averaging (7.02.6's second
paragraph), splitting review from assessment questions (023 — this feature
deliberately counts every question, and the call site carries a comment
warning against narrowing that when 023 lands), certificate content (024),
and reading the technical/non-technical field-of-study tag for a per-state
cap remain out of scope, as specified.

## 2026-08-23, Feature 023, Review questions, assessment questions, and thresholds
Questions now come in two kinds. `questions.kind` (migration `19665ec864ab`,
hand-added CHECK `ck_questions_kind_valid`, default `'assessment'`) and a
nullable `questions.feedback` (shown only after a review question is
answered) join a new `courses.pass_ratio` column (`numeric(3,2)`, default
`0.70`, floored by CHECK `ck_courses_pass_ratio_floor` at `>= 0.70` — 6.01.2's
minimum, not a default a sponsor can relax below). The migration backfills
existing rows with `kind = 'review' WHERE position <= 3`, the exact
convention both seed scripts in `backend/scripts/` were written to; the real
database had zero rows in `questions` at migration time, so the backfill
typed nothing and the position convention's fitness was never actually
exercised against live data — `tests/test_question_kind_backfill.py`
verifies the backfill SQL itself against a synthetic 8-question lesson
shaped like `seed_asc606_construction_intro.sql`. `downgrade -1` verified
both on an empty database and one with rows. A new `review_responses` table
records a participant's review answers, keyed by the same
(`viewer_id`, `user_id`) identity pair `watch_progress` uses; that
resolution rule (`app/services/identity.py`) was pulled out of
`app/services/watch.py`'s previously-private `_identity_filter`
into a small shared, column-parameterized helper so `app/services/review.py`
reuses it instead of writing a second one, with `watch.py`'s own call sites
unchanged.

`app/services/quiz.py` filters to `kind='assessment'` questions only.
`app/services/attempts.py` lost the module-level `PASS_RATIO` constant
entirely; `_pass_threshold` now takes the course's own `pass_ratio` and is
applied to an assessment-only question count (`courses_service
.published_question_count` gained an optional `kind` filter, used here and
in `certificates.py` — `credit.py`'s own count is deliberately untouched,
per the comment 022 left there, and `tests/test_credit.py`'s new
`test_credit_is_unchanged_by_the_review_assessment_type_split` pins that).
An in-attempt answer response now carries only `answered_count` and
`question_count` — no `correct` or `correct_choice_id` — because the
application cannot know mid-attempt whether the participant will pass, and
6.01.2's no-test-bank arm forbids feedback on a failed assessment. On
completion, `AttemptResultData.answers` is populated only when the attempt
passed; a failed attempt never even builds the per-question data, so there
is nothing to leak by omission. This is the no-test-bank arm of 6.01.2
specifically — a future test-bank feature would need to revisit this branch,
since that arm of the Standard allows feedback either way, gated on bank
size rather than on pass/fail; the branch carries that comment.

`app/services/review.py` and `app/routers/review.py` serve and grade review
questions: `GET /courses/{slug}/lessons/{lessonSlug}/review` returns the
segment's review questions with choices and no `is_correct`, no `feedback`
(both withheld until answered, and the feature 015/006 leak-test pattern was
extended to cover them — `tests/test_review.py`);
`POST .../review/{question_id}` grades server-side and returns the verdict
plus feedback, writes to `review_responses` only, and re-answering
overwrites rather than accumulating (no minimum passing rate applies here,
unlike the assessment's replay guard). The leak test carried forward from
015: two users sharing a browser get two separate `review_responses` rows,
and neither overwrites the other's.

`app/constants/question_minimums.py` transcribes both 5.01.2.1's and
6.01.2's one-fifth-credit charts from the PDF (not from current-feature.md)
and implements the above-one-credit case as
`whole * PER_CREDIT + CHART[remainder]` — an interpretation of "additional
questions ... required based on the chart above," not a quoted rule, but one
that reproduces 6.01.2's own worked examples exactly
(`test_five_credit_worked_example_requires_25_assessment_questions`,
`test_five_and_a_half_credit_worked_example_requires_29_assessment_questions`).
`validate_for_publish` (`app/services/admin_content.py`) gained: the review
and assessment floors for the course's computed credit (skipped entirely
when credit hasn't been computed yet, rather than enforced against zero);
`MIN_CHOICES_ASSESSMENT = 3` beside the existing global
`MIN_CHOICES_PER_QUESTION = 2`, since forced-choice (two-option) responses
are not permissible on the qualified assessment; and a same-course exact
duplicate-prompt check between a review and an assessment question
(whitespace/case normalized, exact matches only — the message says so
explicitly, since near-duplicates stay 021's reviewer-judgment territory).
A two-choice question is valid content but does not count toward the review
floor, proven by
`test_two_choice_review_question_is_allowed_but_does_not_count_toward_the_floor`.

Frontend: `QuestionsEditor.jsx` groups questions into "Review questions" and
"Assessment questions" sections instead of interleaving them by position,
each question gaining a type selector and (for review questions) a feedback
textarea, both joining the existing batched save. A new `ReviewPanel.jsx`
component appears on `LessonSegment.jsx` once that segment's watch gate
closes, reusing the progress state `VideoPlayer.jsx`'s `onProgressChange`
already produces rather than fetching watch status a second time (and, for
symmetry, on `CourseDetail.jsx`'s collapsed single-lesson rendering too,
since 019a made that a real code path). `QuestionCard.jsx`/`Quiz.jsx` no
longer render or track per-answer correctness. `Result.jsx` shows a new
`AnswerBreakdown.jsx` component on a pass and an explicit "answers aren't
shown" line on a fail, instead of an empty area. `CourseDetailsForm.jsx`
gained a pass-threshold percentage input with helper text naming the 70
percent floor.

**The placement gap this feature does not close:** 5.01.2.1 requires review
questions "placed throughout the program in sufficient intervals," which
segment-boundary placement satisfies for a multi-segment course but cannot
for a one-lesson course above the 0.2-credit tier — a single lesson has
exactly one seam, and it is the end. This collides with feature 019a's
collapsed single-lesson editor. No publish warning was added for this case
(current-feature.md phrased it as "consider," not "build"); the gap is
recorded in COMPLIANCE.md's Gap column for 5.01.2.1 instead, with the
one-lesson case named explicitly rather than implied.

Verified end to end against the real dev database in a browser
(Playwright): authored a two-lesson course with a review and an assessment
question per lesson, published it, answered a review question and saw the
verdict and feedback render immediately, took the assessment and confirmed
no correctness of any kind appeared between questions, and confirmed the
Result page showed the certificate plus a per-question breakdown on a pass
and an explicit no-breakdown message with a 0-of-2 score on a fail. Backend:
261 tests pass, including the new `tests/test_review.py`,
`tests/test_question_minimums.py`, `tests/test_question_kind_backfill.py`,
and the extended `tests/test_attempts.py`,
`tests/test_admin_content.py`/`tests/test_credit.py` publish-floor and
credit-unchanged cases. Two pre-existing tests changed for the right
reason, not the wrong one: the fifteen-question pass-mark boundary moved
from 12 to 11 (`ceil(0.70 * 15)`, not the old hardcoded `ceil(0.80 * 15)`),
and `_make_publishable_course`/`_publishable_course`'s fixture courses
needed enough review/assessment questions to clear the new floors, which
they didn't before. `npm run lint` and `npm run build` pass.

Mid-video review cues, question banks with randomized selection, simulations
as content-reinforcement tools, and exercises as a type distinct from
questions all remain out of scope, as specified — each is left named at its
relevant call site (`quiz.py`'s no-test-bank branch, `admin_content.py`'s
duplicate check) so the feature that eventually builds it knows what to
revisit.

## 2026-08-23, Feature 023a, Question feedback, objective coverage, and assessment integrity
This file was written without seeing 023's shipped code, so the first step
was reconciling the two against `current-feature_23.md` (023's own spec,
not present in the repo — reconciled against 023's changelog entry and
code instead). Most of what this file assumed was still open had already
shipped: `questions.feedback` (nullable, shown after a review question),
`questions.kind`/`courses.pass_ratio` (023 named them `kind`/`pass_ratio`,
not `question_type`/`pass_threshold` as this file guessed — left untouched
beyond reading, per scope), the per-one-fifth charts in
`question_minimums.py` (already the chart form, not a flat floor — task 2
deleted from this file rather than rebuilt), the same-course duplicate
review/assessment-prompt check, and the true/false rules (023 got both
right: two-choice review questions are allowed but don't count toward the
floor; forced choice is banned outright only on the assessment — neither
needed fixing).

What was actually missing: `objective_id`. Added to `questions`
(`app/models/question.py`, migration `f86fae9d0a77`), nullable, indexed,
FK `ondelete SET NULL` — hand-named
(`fk_questions_objective_id`) and hand-set, not autogenerate's default;
`downgrade -1` verified on a database with rows. Deleting a learning
objective now untags its questions instead of deleting them.
`app/services/objective_coverage.py` computes the 75% figure (6.01.2) —
covered objective ids intersected against the course's own, pure and
read-only alongside `credit.py`'s shape. `validate_for_publish`
(`app/services/admin_content.py`) gained two rules: the coverage
percentage, naming uncovered objectives by their own text rather than a
number, and non-blank feedback on every review question (5.01.2.2) —
023 had shipped the *column* but never required it be filled in.
`QuestionEditor.jsx` gained a "Learning objective" select, populated from
the course's own objectives, shown for assessment questions only (the
feedback textarea already existed for review questions); the lesson-page
editor didn't have the course's objectives available for this, so it now
fetches them the same way it already scopes `checkAdminCoursePublish` off
`lesson.course_id`. `ObjectivesPanel.jsx` shows a live per-objective count
of assessment questions testing it, with a "not yet covered" flag at
zero — 021's stale-review lesson (surface the problem where the author is
already looking) applied to coverage.

The visible product change: 023's `AttemptResultData.answers` already
withheld all per-question data on a failed assessment and included
correctness on a passed one, but never carried the *feedback text* either
way — `AnsweredQuestionResult`/`AnsweredQuestion` now carry `feedback`,
populated only when the attempt passed (`app/services/attempts.py::get_result`,
unchanged branch, new field), and `AnswerBreakdown.jsx` renders it. A
passed assessment's breakdown can now say something beyond "correct" or
"incorrect" — 6.01.2 sub-ii b's actual permission, not the more
conservative no-feedback-ever 023 had implemented pending this file. A
second, smaller regression this feature fixes: 023's confetti-stripping
pass over `QuestionCard.jsx`/`Quiz.jsx` (correctly, for the assessment)
left `ReviewPanel.jsx` (`components/ReviewPanel/`, the participant-facing
one) with no confetti at all, though nothing required removing it there —
5.01.2.1 has no passing rate to protect and 5.01.2.2 asks for
reinforcement, not restraint. `smallBurst` (`lib/confetti.js`, unused
since 023) is now wired back in on a correct review answer, the same
`useEffect`-on-result pattern feature 005 originally shipped.

The leak surface needed no code change — `QuestionPublic`
(`app/schemas/quiz.py`) already omits `feedback` entirely rather than
filtering it at serialization, 004's precedent — but the guard test
(`test_quiz_response_never_leaks_correct_answer`, `tests/test_quiz.py`)
was meaningless against a fixture with no feedback text to leak; its
questions now carry feedback and the test asserts the word doesn't appear
in the payload at all.

Tests: extended the shared "complete course" fixtures
(`_make_publishable_course`/`add_complete_questions`,
`tests/test_admin_content.py`; `_publishable_course`/`add_questions`,
`tests/test_credit.py`) to tag their assessment questions and write review
feedback, since every course they build now needs both to clear the new
publish rules — the same kind of fixture update 023 itself needed when it
added the count floors. New: the hazardous waste fixture
(`_build_hazardous_waste_course`) — 5 lessons, 5 objectives, 4/3/3/3/2
questions (5 review, 10 assessment, objectives 1,1,1/2,2/3,3/4,4/5),
parametrized to publish at both 1.0 and 1.2 credit (27 and 33 minutes of
video against the fixed 27.75-minute question term), proving the charts'
above-one-credit addition rule rather than just their base case; a
0.4-credit course publishing at exactly its 1-review/3-assessment floor;
a 1.2-credit course refused for 6 of the required 7 assessment questions;
dropping the coverage from 100% to 80% (still publishes) and then to 60%
(refused, naming both uncovered objectives by text); a blank-feedback
review question refused; deleting an objective leaving a 33%-covered
course still failing after its tagged question is untagged, not silently
passing; and editing feedback or retagging an objective each bumping
`content_updated_at`. `tests/test_attempts.py`'s fixture now writes
feedback per question and asserts it on a pass, absent (with the rest of
the payload) on a fail. 270 backend tests pass; `npm run lint` and
`npm run build` pass.

Verified end to end against the real dev database in a browser
(Playwright): as admin, confirmed the objective select appears only on
assessment questions and the coverage readout updates live, including the
"not yet covered" state; as a participant, answered a review question
correctly and saw the verdict, feedback text, and a small confetti burst;
failed a qualified assessment and saw only the score with no breakdown;
passed a retake and saw the full per-question breakdown with feedback
text plus the big confetti burst.

Test banks, simulations/other content-reinforcement tools, and the
recall-as-learning-strategy exception to the duplicate-prompt rule remain
out of scope, as specified — the feedback-gating branch in
`attempts.py::get_result` carries a comment naming the test-bank arm it
would need to revisit.

## 2026-08-23, Feature 024, Completion documents and participant records
A certificate now carries the fields Section 9.01 of
`docs/2026-Statement-on-Standards-for-CPE-Programs.pdf` actually requires,
frozen at claim time so a later course or sponsor edit can never change a
certificate already issued.

Section 9.01's own 11-item list was checked against the working list in
current-feature.md, not copied: kept sponsor name, NASBA sponsor registry
ID, state registry ID(s) where the sponsor holds any, participant name,
course title, field of study, delivery method ("type of formal learning
program"), CPE credit amount, and date of completion. **Dropped "program
knowledge level"** — it's a Section 8.01 pre-enrollment disclosure item
(course announcements/descriptive materials), not one of 9.01's 11
certificate-documentation items; abacadaba still computes and stores it on
the course (feature 020) for that disclosure purpose, it's just not part of
the certificate or its snapshot. **Added item 10**, the NASBA time
statement ("CPE credit has been granted based on a 50-minute hour, per
NASBA Standards.") — missing from the working list entirely — as fixed
boilerplate text on the PDF and the verify page (`NASBA_TIME_STATEMENT` in
`app/services/certificates.py`); it's identical on every certificate, so it
needed no snapshot column. Item 5 ("if applicable, location") is N/A —
self study has no location, it's asynchronous by definition. Item 11
("any other statements required by boards of accountancy") has nothing
concrete to add; no per-state statement requirement is modeled anywhere in
this application, so nothing was built for it.

9.02's retention period — "a minimum of five years" — is
`RETENTION_YEARS = 5` in the new `app/constants/retention.py`, cited rather
than guessed. Nothing purges or otherwise acts on it yet; recording it was
the scope, per current-feature.md.

New `sponsor_profile` table (`app/models/sponsor_profile.py`), a singleton
enforced by a hand-added `CHECK (id = 1)`, seeded with one empty-string row
in the same migration (`051cc63bc6c9`) that adds it, so the admin page
always has something to edit. Nine new nullable columns on `attempts`,
written once at claim time by `claim_certificate` and never after:
`cert_course_title`, `cert_field_of_study`, `cert_delivery_method`,
`cert_credit_award`, `cert_sponsor_name`, `cert_sponsor_registry_id`,
`cert_issued_at`, plus two not in current-feature.md's own column list,
added because leaving them out would have broken the feature's own stated
rule — `cert_question_count` (the assessment total behind "scored X out of
Y", which the file's own "problem this feature solves" section names as
exactly the kind of live-course read this feature exists to close) and
`cert_sponsor_state_registry_ids` (9.01 item 9, the sponsor's state
registry IDs, needed frozen for the same reason the sponsor name and NASBA
ID are). `cert_program_level` from the file's list was not added — nothing
would ever read it once program knowledge level was dropped from the
certificate above, and this codebase doesn't carry unused columns.
`downgrade -1`
verified clean.

`app/services/certificates.py::_to_data` now reads the snapshot columns,
not `attempt.course`, whenever a snapshot exists (`cert_course_title is not
None`) — `claim_certificate` writes it inside the same transaction as
`certificate_code`, so a code with no snapshot is a state nothing can
render. A second claim (feature 007's rule) still only updates the
recipient name; the snapshot is untouched. **A certificate claimed before
this feature has no snapshot and renders from the live course and the
current sponsor row instead, permanently** — chosen over backfilling,
because backfilling would mean fabricating a frozen snapshot for data that
was never actually frozen (the sponsor concept did not exist before this
feature, and an old course may have changed since); staying honest that
pre-024 certificates keep reading live data, as they always have, beat
pretending otherwise. `course_slug` is the one field every certificate
still reads live off the course regardless of snapshot — it's routing
metadata for the download filename, never asserted certificate content.
`render_pdf` lays the new fields out as a labelled two-column block in the
lower third (`_draw_field`, reusing `_fit_font_size` per field so a long
sponsor name can't overflow its column) rather than more centred lines, per
current-feature.md's own instruction now that the page is fairly full.
`verify_code` returns the same `CertificateData`, so the PDF and the verify
page agree on every field by construction — there's only one function that
assembles this data.

`validate_for_publish` (`app/services/admin_content.py`) gained a sponsor-
completeness rule: publish is refused, naming the missing fields, unless
the sponsor profile has a name and a NASBA registry ID — the two fields a
certificate can't be compliant without (9.01 items 1 and 8). State registry
ID is correctly excluded (9.01 item 9 is conditional, "if required by the
state boards" — a sponsor with none is still complete) and so are contact
details (website, email, address are part of the identity record an admin
edits, but never appear on a certificate). New `GET`/`PATCH /admin/sponsor`
(`app/routers/admin_sponsor.py`) behind `require_admin`. Every existing
test that publishes a course needed the sponsor profile populated to keep
passing — added `tests/conftest.py`, a repo-first top-level conftest, whose
autouse `reset_sponsor_profile` fixture resets the singleton row to a
complete default before each test, the same way a course-scoped fixture
resets its own rows, since this one row is shared across the whole test
database.

`app/services/completions.py` is read-only aggregate SQL, one query
(feature 012's rule), joining `attempts`/`courses`/`users`: every completed
attempt (`completed_at is not null`, pass or fail) with course title,
participant name (account display name, falling back to the self-reported
`recipient_name`), participant email when signed in, credit (only for a
passed attempt — a failed one earned none; the snapshot wins once claimed,
else the course's current award), completion date, pass/fail, and
certificate code. Filterable by course, date range, and passed. `GET
/admin/completions` and `GET /admin/completions.csv`
(`app/routers/admin_completions.py`) share the one query; the CSV streams
row-by-row (`stream_csv`, a generator) rather than building the file in
memory, with a stable header and column order.

Frontend: `AdminSponsorSettings` (new page at `/admin/sponsor`) edits the
singleton and shows which fields are missing; `AdminCompletions` (new page
at `/admin/completions`) is a plain filterable table plus a CSV download
link — no charts, feature 012 settled that. Both are reachable from
`AdminCourseList`'s header nav, next to "Subject matter experts," not
buried inside a course. `Verify` renders the new snapshot fields (field of
study, delivery method, credit, sponsor name/NASBA ID/state registry IDs)
plus the 50-minute-hour statement; the existing self-reported-name wording
from feature 007 is unchanged. `Result` needed no changes — it only links
to claim/download, it doesn't render certificate content itself.

**Anonymous attempts and 6.01**: checked, not assumed. Feature 016
(2026-08-11) already made `POST /courses/{slug}/attempts` require a signed-
in user, so every attempt created since then has a verified account behind
it — 6.01's "self-certification of attendance/completion alone is not
sufficient" concern doesn't apply to anything new. `claim_certificate`
still lets a *pre-016* anonymous attempt (`attempt.user_id is None`) claim
with a typed-in name, exactly as feature 016 decided to preserve for
certificate links already handed out. That typed name is self-certification
in the plain sense of the term, so **this feature does not mark 6.01
satisfied on the strength of a passed assessment alone where the identity
is self-asserted** — see COMPLIANCE.md's Gap column on that row. The scope
of the gap is fixed and shrinking (only attempts created before 2026-08-11
can ever hit it) rather than open-ended, which is why current-feature.md's
instruction not to fix it by removing the anonymous path was followed as
written.

Tests: 288 backend tests pass (up from 270), including new coverage in
`tests/test_certificates.py` (snapshot written at claim time and verified
against the fixture course/sponsor; editing the course or sponsor after
claiming changes neither the PDF nor the verify page; claiming twice keeps
the original snapshot even if the course changes in between; the PDF
contains every Section 9 field, asserted against text extracted with
`pypdf` rather than eyeballing bytes — new dependency, `pypdf==6.16.*`,
declared in `requirements.txt`; a long name against a long course title
against a long sponsor name still produces a valid, readable PDF; a
pre-024 certificate with no snapshot still renders),
`tests/test_sponsor_profile.py`, `tests/test_completions.py`, and one new test in
`tests/test_admin_content.py` proving publish is refused and names the
missing fields. Verified end to end against the real dev database in a
browser (Playwright, driven directly — `chromium-cli` wasn't available in
this environment): registered an admin, confirmed the new nav links,
confirmed the sponsor page's missing-fields warning and that it clears and
persists on save, confirmed publish is refused with an incomplete sponsor
profile and succeeds once it's complete, completed a real assessment as a
signed-in participant, claimed and downloaded a certificate whose extracted
PDF text carried every required field, confirmed the verify page agreed,
and confirmed the completions table and CSV download both reflected the
new completion. Test data cleaned up from the dev database afterward.

Emailing certificates, certificate templates/branding, revocation and
expiry, and publishing the retention policy as a participant-facing page
remain out of scope, as specified.

## 2026-08-23, Feature 025, Evaluations

Every participant is now offered a program evaluation on the Result page
after their attempt completes, passed or failed, and an admin can review
the aggregated results per course. 4.04 and 4.04.1 govern this
(`docs/2026-Statement-on-Standards-for-CPE-Programs.pdf`); 4.04.2 is
addressed below.

New `evaluations` table, one row per attempt (`attempt_id` unique FK,
CASCADE), one nullable integer column per dimension (1-5, hand-added CHECK
constraints — `alembic revision --autogenerate` picked them up directly
from the model's `__table_args__` on this brand-new table, so nothing had
to be hand-edited into the generated migration this time), plus a free-text
`comments` column and `submitted_at`. Columns, not a rows-per-answer table
— see the model's own docstring for the reasoning. `downgrade -1` verified
clean.

The five dimensions 4.04.1 enumerates live once, as ordered records, in
`app/constants/evaluation_dimensions.py` — key, participant-facing
question text, and an `applies_to_self_study` flag — served through a new
unauthenticated `GET /meta/evaluation-dimensions` (`app/routers/
evaluations.py`) rather than duplicated in the frontend, the same pattern
feature 020 established for fields of study. **Item 5, instructor
effectiveness, is filtered out of that response and never rendered or
collected** — self study has no instructor a participant met, so asking
would produce noise, not quality data. The dimension stays in the constant
with `applies_to_self_study = False` rather than being deleted, and its
`instructor_effective` column stays on the table, both ready for
superCPE's group programs. This is a deliberate, recorded gap against
4.04.1, not a silent omission — see the COMPLIANCE.md row.

`app/services/evaluations.py`: `submit()` refuses an incomplete attempt
(409) and a second submission for the same attempt (409, translated from
the unique constraint's `IntegrityError` rather than leaking a 500 — the
same pattern `attempts.py::record_answer` already uses for duplicate
answers); a partial submission (some dimensions null) is accepted, since a
participant who answers four of five has still given four useful data
points. `course_summary()` computes response count, response rate
(against *completed* attempts, not started ones), and a mean per
dimension in one query — an outer join from `attempts` to `evaluations` so
an attempt with no evaluation still counts toward the denominator, and
`AVG()` already ignores nulls for the per-dimension means. `course_comments
()` returns non-blank comments newest first. Three new endpoints:
`POST`/`GET /attempts/{id}/evaluation` (public — an attempt's own
completion page needs no admin session to see or submit its evaluation)
and `GET /admin/courses/{id}/evaluations` (added to `admin_analytics.py`,
next to the existing stats endpoint, both behind `require_admin`).

Frontend: `components/EvaluationForm/EvaluationForm.jsx`, dropped onto
both branches of `Result.jsx` (passed and failed) below the certificate/
retry section — it builds its five-or-fewer questions entirely from
`GET /meta/evaluation-dimensions`, never hand-coding them in JSX. It
fetches the attempt's existing evaluation on mount and shows a submitted
summary instead of the form when one exists, so a reload never looks like
the submission failed. A new admin page, `pages/Admin/Evaluations/
Evaluations.jsx`, shows response count, response rate, a mean per
dimension (flagging any mean below 3 with the same `flaggedRow`/`badge`
treatment feature 012's Stats page uses for a question under 40 percent,
reused rather than reinvented), and the comments; a course with zero
responses shows a plain message instead of an empty table. Linked as
"View evaluations" next to "View stats" on both `AdminCourseList` and
`AdminCourseEditor`.

**On 4.04.2** ("CPE program sponsors must periodically review evaluation
results ... and should inform developers and instructors of evaluation
results"): this feature makes results available to review — the admin
evaluations page — and stops there. It does not schedule, remind, or track
that a periodic review happened, and nothing connects a result to the
course's `developer_id`/`reviewer_id` (feature 021) to notify anyone.
Treated as a human obligation the software makes possible rather than one
it performs — recorded as an open gap in COMPLIANCE.md, not silently
assumed. Read the results: this is also the first feature that produces
real signal on whether the AI-drafted course content is any good, which is
the thing abacadaba exists to test.

Tests: 304 backend tests pass (up from 288), 16 new in
`tests/test_evaluations.py` — every dimension stored on submission, an
incomplete attempt refused, a duplicate submission refused cleanly (409,
not a 500), a partial submission accepted, a rating of 0 or 6 refused
(422), the instructor dimension absent from the served list, an unsubmitted
evaluation returning `null` rather than 404, a submitted evaluation
round-tripping on GET, course-summary means computed over submitted values
only, response rate using completed attempts as the denominator, a
zero-response course, comments ordered newest first, and the admin
endpoint requiring admin. `npm run lint` passes. Verified end to end in a
real browser (Playwright, driven directly — `chromium-cli` wasn't
available in this environment): registered a participant, completed a
seeded course's assessment, confirmed the evaluation form rendered exactly
four dimensions (no instructor) built from the live API response, submitted
ratings and a comment, confirmed the submitted summary replaced the form,
reloaded the result page and confirmed it still showed the submission
instead of the form, then logged in as a promoted admin and confirmed the
course list and course editor both link to "View evaluations," the admin
page showed the correct response count/rate/means/comment, and a
freshly-created empty course showed the plain no-responses message instead
of an empty table. Seeded course, attempts, and users cleaned up from the
dev database afterward.

## 2026-08-23, Feature 026, Policies, disclosures, and content currency
Refund/cancellation, complaint resolution, records retention, and program
cancellation now exist as real editable `policies` rows (migration
`c101e414d784`, seeded with an unmistakable placeholder rather than invented
text) served at `GET /policies`/`GET /policies/{slug}` and edited via
`PATCH /admin/policies/{slug}`; `validate_for_publish` refuses to publish any
course while any of the four is still placeholder, naming which, and the
public pages render at `/policies/{slug}`, linked from a new site footer and,
for the two 8.01.1 names, from `CourseDetail`'s pre-enrollment disclosure
block. Rendered through a small hand-rolled markdown subset
(`frontend/src/lib/markdown.js`) rather than a new dependency or a rich text
editor. Courses gained `expires_on` (9.02.2): required to publish, disclosed
beside credit and last-reviewed date, defaulted client-side to the review
date plus one year the first time a review is recorded but always editable,
and excluded from `content_updated_at`'s bump (joining the review-chain
fields) so extending it doesn't force a re-review. An expired course is
excluded from the public catalog but stays reachable and published rather
than being pulled out from under anyone; `start_attempt` now checks expiry
before authentication (a property of the course, not the participant) and
refuses a new attempt with the expiration date named, never a 404. A new
`GET /admin/currency` dashboard (`app/services/currency.py`, four read-only
queries) reports courses overdue for review, due within 60 days, published
but edited since their last review (021's recorded-but-unenforced gap), and
expired or expiring within 60 days - each sorted worst first, a course
appearing in more than one section when it qualifies, reusing `Stats.jsx`'s
table treatment rather than a second one. Confirmed by reading the codebase,
not assumed, that 8.01.1's "schedule of events for concurrent/bundled
programs" clause is not applicable: abacadaba has no concept of bundling
several programs or non-CPE activities together. Verified live against a
real dev database via a scripted Playwright session: edited a policy and
watched it appear at its public URL and clear a publish refusal for two
courses at once, created a course and watched the publish checklist show
both new rules, set an expiration date and saved it, and confirmed the
currency dashboard's four sections render with no console errors. Backend
suite: 329 tests (304 existing + 25 new) pass; `npm run lint` and
`npm run build` pass. A draft-and-version model for courses, emailing anyone
about anything overdue, and a complaint intake workflow remain out of scope,
as specified.

## 2026-08-24, Feature 027, Sponsor registration state
abacadaba is not a registered NASBA CPE sponsor, and its certificates no
longer imply otherwise. `sponsor_profile` gained `registry_status`
(`'not_registered'`/`'registered'`, `NOT NULL`, server default
`'not_registered'`, migration `2f6c9b1a4d3e`) - stored, not derived, as a
deliberate exception to the derived-not-stored rule 019a/022/026 followed:
whether abacadaba is on the National Registry is a fact about the world, and
no amount of inspecting `national_registry_id`'s text can determine it, so
the sponsor has to state it (see the model's own docstring). `attempts`
gained the matching snapshot column, `cert_registry_status`, written once at
claim time by `claim_certificate` alongside the other `cert_*` columns 024
added; `_to_data` falls back to a live read of the sponsor's current
`registry_status` only for the narrow window of certificates claimed after
024 shipped but before this feature did (every other field on those was
already frozen) - the dev database had zero claimed certificates at
migration time, so nothing actually renders under that fallback today, but
the code path is real and tested. A certificate issued while unregistered
omits the NASBA time statement and the registry ID field outright (absent,
not blank, not "N/A") and instead prints, in the same bold weight as the
participant's name rather than as fine print, that the program is not
offered by a NASBA-registered sponsor and completion does not earn CPE
credit (`app/services/certificates.py`'s `render_pdf`, gated on
`registry_status` alone - not on whether `national_registry_id` happens to
be blank, since an admin can still type a number while unregistered and the
suppression must not depend on them not doing that). `Verify.jsx` and the
`/certificates/{code}` payload branch on the same `registry_status` field
`render_pdf` does, proven with a dedicated agreement test rather than
assumed. `sponsor_profile.py`'s `REQUIRED_FIELDS` module constant is now
`required_fields(profile)`: `name` stays required unconditionally (9.01 item
1), `national_registry_id` only once `registry_status` is `"registered"` -
today's gate had it backwards, compelling an unregistered sponsor to invent
a registry ID just to publish, which is a worse outcome than the missing
field it was written to prevent. `AdminSponsorSettings.jsx` gained a plain
two-option "NASBA registry status" select (not a checkbox - a checkbox
labelled "registered" invites an idle click) with a hint explaining what
registered means, placed before the registry ID field, which now shows a
required marker only while registered. Frontend task 3's judgment call: yes,
`CourseDetail.jsx` shows the same not-registered notice before enrollment,
not only after - a participant deciding whether to spend an hour deserves to
know before, the same "before, not after" reasoning 8.01's disclosure
already rests on. This needed one new field on the public course payload,
`sponsor_registry_status` (`CourseWithLessons`/`CourseDetail` schema) - a
live read from `courses_service.get_with_lessons`, not a snapshot, since a
course page describes the sponsor's current state rather than a historical
claim the way a certificate does. Verified end to end against a live dev
database via a scripted Playwright session plus direct PDF inspection (no
`poppler` in this environment, so `sips`/QuickLook rendered the PDFs to PNG
instead): the sponsor settings select toggling the registry-ID required
marker live; a course published under each `registry_status` rendering the
correct pre-enrollment notice (or its absence) on `CourseDetail`; and both
the resulting certificate PDF and its `/verify/:code` page for each state,
confirming the registered path is pixel-for-pixel unchanged from 024's
original layout and the unregistered path cleanly omits both NASBA fields
in favor of the bold notice. Backend suite: 343 tests (329 existing + 14
new) pass; `npm run lint` and `npm run build` pass.

Two things this feature deliberately did not touch, per current-feature.md's
own scope. First, whether the program-cancellation policy's stated grace
period matches what unpublishing actually does to in-progress attempts -
read, not built, per current-feature.md's instruction: `unpublish_course`
(`app/services/admin_content.py`) does nothing but flip `is_published` to
`False`; `start_attempt` (`app/services/attempts.py`) refuses a *new*
attempt on an unpublished course immediately (no grace window), but nothing
anywhere - answering a question, completing an attempt, claiming a
certificate - checks `is_published` at all, so an attempt already
in progress when a course is unpublished is completely unaffected and can
run to completion and claim a certificate whenever the participant likes.
The dev database's `program-cancellation` policy is still unwritten
placeholder/test content with no stated grace period to compare against, so
there is nothing to disagree with yet; if an admin later writes a policy
promising a specific grace window, the code above is the actual behavior to
check it against. Second, the NASBA escalation paragraph in the complaint
resolution policy body, which is human-written text in a table row this
feature has no business generating or rewriting.

## 2026-08-24, Feature 028, The completion path
A testing walkthrough found BUG-001 (now `BUGS.md`, which this feature also
created): a participant who watched every segment and answered every review
question reported the course "just ends." He had actually never reached the
qualified assessment - `LessonSegment.jsx`'s footer `<nav>` rendered "Next
segment →" when `next_lesson_slug` was present and rendered nothing at all
on the last segment, so the only way forward from there was `CourseDetail`'s
own "Take the assessment" button, which nothing on the segment page pointed
back to. Fixed at the last segment: the same slot now renders "Take the
assessment" (linking to `/courses/{slug}/quiz`, the destination
`CourseDetail.jsx` has used since feature 019) once the assessment is
reachable, or the name of the still-locked segment otherwise. Every segment
page, not only the last, also carries a quiet one-line status
("The assessment is unlocked." / `Watch "{lesson}" to unlock the
assessment.`), sourced from a single new predicate,
`app/services/courses.py::get_assessment_gate_status`, built specifically so
this page cannot disagree with what `CourseDetail.jsx` already shows via
`/watch-status` or with what `attempts_service.start_attempt` already
enforces - an admin bypasses the watch gate in all three places for the same
reason. `GET /courses/{slug}/lessons/{lesson_slug}` gained
`assessment_unlocked`/`assessment_outstanding_lesson`
(`LessonSegmentDetail`/`LessonSegmentData`); `LessonSegment.jsx` refetches
the segment when its own watch gate transitions closed→open, since that is
exactly the moment the whole-course gate can also change and the terminal
action would otherwise sit stale until reload. `CourseDetail.jsx` gained a
"How this course works" section stating the segment count, that segments
carry practice review questions, that one qualified assessment covers the
whole course, and the pass threshold - every number read from the course
(`pass_ratio`, `assessment_question_count` added to `GET /courses/{slug}`)
rather than hardcoded, so it cannot drift from the course it describes.
`ReviewPanel.jsx` gained one sentence distinguishing its ungraded practice
questions from the graded assessment, since the walkthrough's tester had
mistaken the two. `Result.jsx`'s post-assessment screen gained "My
progress"/"Browse courses" links alongside "Back to course," and
`Progress.jsx`'s empty state now says "assessment," not "quiz," to match.
Backend: 4 new tests plus one correction to an existing one -
`test_answering_a_review_question_writes_no_attempt_row` asserted the
attempts table was empty before and after, which only held because dev and
test point at the same database and happened to be empty at the time; this
feature's walkthrough used that same database and left rows behind, so the
assertion is now a delta (`before == after`) rather than a global-emptiness
claim. 347 tests pass (343 existing + 4 new, none modified in expected
outcome except the correction above); `npm run lint` and `npm run build`
pass.

While reviewing evaluations for this walkthrough, found a second unread
data source alongside them: `review_responses` (feature 023's ungraded
practice-question answers) has nine rows in the dev database and nothing
anywhere queries them, the same shape of gap as 4.04.2's evaluation-review
gap. Recorded against 4.04.2 in COMPLIANCE.md rather than opening a new
locator, since no clause of the Standards specifically names review-question
data. Not built here.

No model or schema change, so no Alembic migration. `BUGS.md` created (did
not exist before this feature) - see its own note on why BUG-001 and BUG-002
are reconstructed from current-feature.md's account rather than moved from
prior text.

## 2026-08-24, Feature 029, General programs
A course can now be offered as ordinary education instead of as a CPE
program - abacadaba's first real teacher-and-students use case, and the
reason every compliance feature built through 028 stays built rather than
being torn out: `program_kind` (`'cpe'`/`'general'`, `NOT NULL`, CHECK,
server default `'cpe'`, migration `7a3f9c2e5b1d`) on `Course`, editorial and
per-course, deliberately not folded into 027's `sponsor_profile
.registry_status` - two different facts with two different owners, see
current-feature.md's "Two facts, two fields." `attempts.cert_program_kind`
snapshots it at claim time alongside 024/027's other `cert_*` columns; a
null value (a certificate claimed before this feature shipped) reads as
`'cpe'`, since nothing else was possible before today.

`GET /courses/{slug}` now returns one of two Pydantic shapes -
`CourseDetail` (general) or `CourseDetailCPE`, which adds `field_of_study`,
`credit_award`, `expires_on`, and `sponsor_registry_status` back -
constructed in the router and served with `response_model=None` so a
general course's JSON has no key for the omitted fields at all, not a null
one (same reasoning 023a's `QuestionPublic` already established for
`feedback`). The certificate and verify endpoints follow the same pattern
(`CertificateInfo`/`CertificateInfoGeneral`,
`CertificateVerification`/`CertificateVerificationGeneral`): a general
certificate's `sponsor_name` field doesn't exist either, renamed
`issued_by`, since the guard test checks for the substring "sponsor"
anywhere in the payload, key or value. `render_pdf` (`app/services
/certificates.py`) branches the same way: a general certificate prints only
the participant name, course title, completion date, score, "Issued by,"
and the verification code - no Field of Study, CPE Credit Awarded, Type of
Formal Learning Program, registry ID, NASBA time statement, or 027's
not-registered notice (there is no CPE claim on it to contradict).
`CourseDetail.jsx` reads a new label module (`constants/programLabels.js`)
so a general course's page says Level, What you should know first, Before
you start, Length (summed from `lessons[].duration_seconds`, not
`credit_award` multiplied back out - that arithmetic is confidently wrong by
up to nine minutes past a floored one-fifth credit increment), and Quiz
instead of Program level, Prerequisites, Advance preparation, CPE credit,
and Qualified assessment; Field of study and Expires are omitted from the
page entirely, matching the payload. `Verify.jsx` follows the same branch.

`validate_for_publish` (`app/services/admin_content.py`) gained an
`is_general` branch, one relaxation at a time with the Standards reason
attached in a comment rather than a blanket skip: field of study, the whole
developer/reviewer/review-date/licensed-credential chain, credit computed
and its 0.2 floor, per-lesson duration, credit-derived review/assessment
question minimums, 75% objective coverage, review-question feedback, the
assessment's forced-choice ban, and sponsor-profile completeness (narrowed
to the name only - the one field a general certificate still prints). Still
enforced for both kinds: at least one learning objective, `pass_ratio >=
0.70`, the four real policies, sponsor name, and - newly, since the
credit-derived floor was the only thing requiring it before - at least one
qualified assessment question, added as its own unconditional check so a
general course can't publish with an empty quiz just because nothing else
was gating it. `program_kind` may not change while a course is published
(`ProgramKindChangeWhilePublishedError`, 409) - a published general course
switched to `'cpe'` would claim CPE status without ever having cleared the
CPE gate. `CourseDetailsForm.jsx` gained the "Offered as" select, first on
the form and disabled with an explanation while published;
`CoursePublishPanel.jsx`'s checklist simply omits the relaxed items for a
general course rather than showing them pre-checked (020c's Bug 4); the
Credit panel stays visible and computable but its staleness warning no
longer claims the course can't publish while stale, for a general course.

The site footer's four policy links are now gated on `show_policy_footer`
(`app/services/courses.py`, exposed at `GET /meta/site-status`) - one
`EXISTS` against `is_published AND program_kind = 'cpe'`, not a second
site-wide flag that could disagree with the per-course field. A site of
general-only courses shows no footer; publishing one CPE-presented course
again brings it back with no configuration. `COMPLIANCE.md`: no new rows -
every row in the matrix already describes a `program_kind = 'cpe'` course,
made explicit in an extension to 027's scope note, and the 8.01.1 row's Gap
column now explains that the footer's policy links moved onto that derived
condition while the per-course disclosure block (shown only for a CPE
course) is the actual surface satisfying "made available to participants."

Verified against a live dev database via a scripted Playwright session: a
minimal general course (one objective, one assessment question, a video, no
reviewer, no computed credit) published; its public page rendered with the
relabelled fields and no Field of study/Expires row, no not-registered
notice, and no per-course policy links, while the real published CPE course
in the same database kept every CPE field untouched and the site footer
kept showing (correctly derived from that course, not the general one); a
completed attempt's certificate PDF and `/verify/:code` page carried only
the five general fields plus "Issued by," confirmed by direct PDF
inspection. Backend suite: 378 tests (347 existing + 31 new in
`tests/test_program_kind.py`, none of the 347 modified) pass; `npm run
lint` and `npm run build` pass.

Numbering note: this is Feature 029, not 028 - Feature 028 ("The completion
path," above) was built in the interim from a different current-feature.md
than the one that specified this feature, and had already claimed 028
before this one's own numbering note ("not `027a`, so the next whole
number") was written. See current-feature.md's own numbering note for the
full account.

## 2026-08-25, Video pipeline 03, Lesson meta completeness
`LessonMeta` (`slides.tsx`) has required `position`, `deliveryMethod`,
`fieldOfStudy`, `revision`, and `revisionDate` since Video pipeline 02, and
`Title`/`Sheet.tsx` render them - but `Lesson.tsx` reads each lesson's `meta`
through `as unknown as LessonMeta`, a double cast that suppresses structural
checking entirely, so `tsc` never verified the individual lesson modules
actually supplied those fields. Most didn't: only lesson-06 had `revision`/
`revisionDate` (added when it was written), and none had `position` or
`deliveryMethod` - exactly the gap lesson-06's trailing comment already
diagnosed as finding 1, "`Title` is not generic... every lesson since 02 has
been rendering lesson 02's position and lesson 02's field of study." A new
`npm run check` (`scripts/check-lessons.ts`) surfaces this class of defect
going forward by validating each lesson's blocks and reveals independent of
the `as unknown as` cast; it now reports 0 errors across all six lessons (1
expected warning: lesson 01 block-02 sitting exactly on the 40s sheet-window
boundary).

Added the four missing fields to `meta` in `lesson-01.ts` through
`lesson-05.ts`, and `position`/`deliveryMethod` to `lesson-06.ts` (which
already had `revision`/`revisionDate`). `deliveryMethod` is "Self study" for
all six; `position` is course-relative ("Lesson N of 5"), matching each
lesson's existing `eyebrow` - except lesson-06, whose `eyebrow` and
`position` both read "Lesson 1 of 5" while `lessonId` stays "06", the
package-position/course-position split its header comment already documents
and this feature does not reconcile. `revisionDate` for lessons 01, 02, and
06 came from existing narration/audio-pipeline dates already in this file;
CHANGELOG.md had no recorded authorship date for lessons 03-05, so their
`revisionDate` (2026-08-24) was confirmed with the user against each
module's git commit date rather than guessed, per the note in lesson-01.ts
that `revisionDate` is a 4.01 disclosure, not decoration.

No blocks, narration, reveals, `estimatedSeconds`, `slides.tsx`, or
`Sheet.tsx` changed, and no audio was regenerated - this is metadata only.
`revision`/`revisionDate` render only in `Sheet.tsx`'s "REV" cell
(`revisionDate` itself is not yet rendered anywhere); `position`/
`deliveryMethod`/`fieldOfStudy` render in `Title`'s footer strip. Lessons
01-05's title sheets and lesson-06's REV cell were rendered before this
feature with the wrong or blank values described above; picking up the
fix requires a re-render, not shipped here (see next-steps note to the
user).

COMPLIANCE.md gains no row. 4.01's "most recent publication, revision, or
review date" locator is already mapped (features 021/026) against
`Course.reviewed_at` in the actual application; this `video/` package is
still the pre-application authoring/rendering tooling Video pipeline 01/02
established, not wired to that model, and its `revisionDate` field is not
yet rendered on any surface a participant sees. This feature makes the
package's own type declarations honest about a shape it already had - it
does not add new disclosure to a real course.

## 2026-08-25, Feature 030, Favicon and header identity
The bare-string `abacadaba` header and Vite's default tab icon are gone. A
full favicon set (`favicon.svg` with a dark variant, `favicon.ico`,
`apple-touch-icon.png`, `icon-192`/`icon-512`/`icon-maskable-512.png`,
`site.webmanifest`) is in `frontend/public/`, regenerable from
`tools/brand/build_icons.py`; `frontend/index.html` links them in the order
Safari needs.

The header now has three zones - brand, product nav, account - matching
current-feature.md's diagram, not one undifferentiated row. `Wordmark`
(`components/Wordmark`) renders the spelled-out wordmark itself, a's in
`--ink` and b/c/d in `--color-accent` (the app's existing purple, also used
for buttons and links elsewhere - not a second brand color to keep in sync);
the letters are `aria-hidden` with the accessible name ("abacadaba, home")
on the link itself, so screen readers don't spell the word out. Set in a
self-hosted Jost subset - glyphs a/b/c/d only, still variable (so weights
500 and 700 both resolve from the one file), ~1.9KB, built by
`tools/brand/build_jost_subset.py`; the OFL license and copyright name
records are kept in the font and `frontend/public/fonts/OFL.txt` ships
alongside it. `AccountMenu` (`components/Header/AccountMenu.jsx`) replaces
the bare `Sign out` link and inline `Admin` link with a menu-button:
`aria-haspopup="menu"`, `aria-expanded`, `role="menu"`/`role="menuitem"`,
arrow-key navigation, Escape-returns-focus, click-outside-closes. `Admin`
still only renders for `user.is_admin` - this is presentation, the
server-side check that actually gates `/admin` is unchanged.

current-feature.md's original design paired the wordmark with a separate
mark (a circle beside a stem, doubling as a constructed lowercase `a`) and a
"Short CPE lessons" descriptor beside it. Both are gone, cut after the
initial build at the user's direction: the mark read as an unwanted "ball
and a line" logo, and abacadaba is an experiment on the way to a different
product (superCPE) rather than actually a short-CPE-lessons product, so that
copy was inaccurate rather than just unwanted. Removed everywhere the mark
or that copy appeared, not just the header: the favicon/touch-icon/home-
screen-icon set is now a single Jost `a` glyph on the `--ink` tile
(`tools/brand/build_icons.py` draws it straight from the same font file
rather than system Poppins, which the previous version of that script and
`build_og_default.py` depended on and which isn't guaranteed to exist on
whatever machine regenerates these); `og-default.png` lost both the mark and
the tagline; `<title>`, `og:description`, and `site.webmanifest`'s
`description` field all lost the CPE-lessons line, with `og:description`
made optional on the default share card entirely (`app/services/og.py`)
rather than replaced with different invented copy nobody asked for. A
course's own share card is unaffected - `og:description` there is the
course's real, admin-authored description, not site tagline copy.

Active-page state (`My progress`) uses React Router's `NavLink`, which sets
`aria-current="page"` itself; the indicator dot is CSS keyed off that
attribute, not a second piece of state, so the visual and accessible states
can't drift apart. A skip link is the first focusable element on the page;
every interactive element gets a 2px `--color-accent` `:focus-visible` ring
site-wide (not header-scoped, since there was no reason to make it
narrower). The wordmark's accent-letter settle animation runs once per
`sessionStorage`-tracked session and is removed entirely under
`prefers-reduced-motion: reduce`. Below 640px product nav and the account
zone collapse behind one menu button - no second mobile nav pattern, since
the app didn't have one yet to reuse.

Brand tokens `--ink`/`--rod`/`--wash`/`--rule`/`--paper` in `global.css`
stay their own thing (structural: rules, borders, tile backgrounds) since
none of them have a `--color-*` equivalent; there's no separate `--bead`
token now that the accent role is `--color-accent` directly. `--rod` still
ships darker than current-feature.md's literal `#7A94A6` (`#56707F`) from
the original build's contrast check, even though its one remaining text use
(the account-menu caret) doesn't strictly need it - no reason to reintroduce
a value that failed 4.5:1 once already.

Part 5's link previews: `frontend/index.html` carries the static
site-default Open Graph tags Apple's non-JS fetcher needs, `og:url` and
`og:image` built from `%VITE_SITE_URL%` (Vite's own HTML env substitution,
already defined per environment in `frontend/.env*`) so they're correctly
absolute in every environment without hardcoding a host. Per-course previews
are `GET /api/v1/og/courses/{slug}` (`app/routers/og.py`,
`app/services/og.py`), reusing `courses_service.get_by_slug`'s existing
`is_published` filter rather than a second query, so an unpublished or
unknown slug can't leak anything - it gets the site-default card, not a 404
and not the draft's title. Six new tests in `tests/test_og.py` cover the
published, no-thumbnail, unpublished, and unknown-slug cases plus
description truncation and absolute-URL image fallback.

This is Option 2 from current-feature.md's Part 5b, not Option 1: `api` and
`web` are built and deployed completely separately (see DEPLOYMENT.md), so
`api` has no copy of `web`'s `index.html` to substitute tags into. The
routing half already existed in the repo, written ahead of the endpoint and
waiting on it: `abacadaba.conf`'s "Open Graph crawler branch" routes known
crawler User-Agents on `/courses/{slug}` to this endpoint and leaves
everyone else on the normal SPA catchall. It was commented out with a note
not to enable it before the backend endpoint existed - a 502 that a crawler
caches is worse than no tags at all - so this feature also uncomments it and
updates that file's header comment. The same file's `location =
/site.webmanifest` block (already active, unrelated to this feature) covers
current-feature.md's other nginx warning: this build's `mime.types` doesn't
know the `.webmanifest` extension and would otherwise serve it as
`application/octet-stream` with no visible error.

No COMPLIANCE.md row, per current-feature.md's own note: sponsor
identification and the four policies are 026's footer, not this feature's
header.

## 2026-09-05, Feature 023b, The objective select overflows its panel
`QuestionEditor.module.css` gets its own `.objectiveSelect`, composed from
`.kindSelect` (`composes: kindSelect`, same pattern `AdminPolicies.module.css`
already used for `.form`) plus `flex: 1`, `min-width: 0`, `max-width: 100%`,
and the closed-state ellipsis trio. `min-width: 0` is the load-bearing line:
a flex item's default `min-width: auto` sizes to its widest child content
regardless of `max-width`, which is what let the select's widest `<option>`
(a full learning objective) push it past the panel border in the first
place. `.metaRow` gets `flex-wrap: wrap` and `.kindLabel` gets
`flex-shrink: 0` so a long objective can push its row to two lines at a
narrow width instead of squeezing the label. `QuestionEditor.jsx` swaps
`styles.kindSelect` for `styles.objectiveSelect` on the objective select
only - the Type select keeps `.kindSelect` unchanged.

Same pattern, one other place: `AdminCompletions.jsx`'s course filter
populates its options from `course.title`, author-entered same as an
objective, and its `.select` had the identical no-width-constraint problem
inside `.filters`' flex row. Fixed with the same `.courseSelect` composition
in `AdminCompletions.module.css`. Every other `<select>` in the admin UI
(`ReviewPanel`, `CourseDetailsForm`, `AdminSponsorSettings`) either draws
options from a fixed enum or already lives in a column-flex `.form` with
`.input { width: 100% }`, where a plain block-level width constraint has no
`min-width: auto` fight to lose - so those were left alone.

Verified against a real question in this repo's data (`Identify the RCRA
characteristics and generator categories that determine whether and how a
waste must be managed as hazardous.`, feature 028's hazardous-waste course)
via a screenshot of the running admin UI at 1280px and 375px: the select
stays inside the panel and ellipsizes at both widths, and the Type select is
visually unchanged. The 375px screenshot also showed a pre-existing
horizontal overflow from `ChoiceRow`'s Up/Down/Delete buttons, unrelated to
any select and out of this feature's scope - noted here rather than fixed
silently.

No COMPLIANCE.md row: this changes the width of one control in the admin
tool. It does not change what is disclosed to a participant, what is
stored, or what any locator in
`docs/2026-Statement-on-Standards-for-CPE-Programs.pdf` requires.
