# Bugs

Append-only, like CHANGELOG.md and COMPLIANCE.md. This file did not exist
before feature 028; current-feature.md referred to entries in it (BUG-001,
BUG-002) that were never actually committed here. The two entries below are
reconstructed from current-feature.md's own account of each bug rather than
moved from prior text, since there was no prior text to move. Say so rather
than pretending continuity that doesn't exist.

## Fixed

### BUG-001 — Course completion has no exit

**Reported:** 2026-08-24, a testing walkthrough of the one published course.

**Original report:** The tester watched all five segments of the course,
answered every question put in front of him, and reported that the course
"just ends" with no navigation afterward. He then found
`/admin/courses/2/stats` empty and asked whether there was supposed to be a
final quiz.

The row counts at the time:

```
 attempts           |  0
 attempt_answers    |  0
 evaluations        |  0
 review_responses   |  9
 watch_progress     | 11
```

**What it actually turned out to be:** Not a missing quiz — the qualified
assessment existed and worked. He never took it. He answered nine review
questions (feature 023's inline, ungraded content-reinforcement tools) and
concluded he had taken the tests, because nothing on the last segment page
led anywhere else. `LessonSegment.jsx`'s footer `<nav>` rendered a
"Next segment →" link when `next_lesson_slug` was present and rendered
*nothing* in its place when it was `null` — the only exit was a
`← Back to {course_title}` link at the top, worded and positioned as a
retreat, not as "the thing you still have to do." "Take the assessment" had
lived on `CourseDetail` since feature 019 moved the assessment from lesson
scope to course scope; the path existed, forward motion never reached it.
The reported symptom (no final quiz) and the real cause (a dead-end
navigation link plus an unlabelled practice panel that reads like a test)
were different problems, and the difference is what feature 028 fixed.

**Fixed by:** Feature 028, "The completion path". See CHANGELOG.md.

## Open

### BUG-002 — Cross-account watch state

Real, open, and an identity bug rather than a navigation one — explicitly
out of scope for feature 028. `tests/test_watch.py`'s leak test
(`test_user_bs_progress_does_not_leak_from_user_a_sharing_a_viewer_id`)
passes at the API boundary while the browser appears to disagree; feature
028's walkthrough is the second finding of this same pattern (see
CHANGELOG.md's feature 028 entry) — this codebase's automated verification
is strong at the API boundary and thin above it. Not touched here.
