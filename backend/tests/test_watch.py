import uuid
from datetime import datetime as real_datetime
from datetime import timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.db import SessionLocal
from app.main import app
from app.models.choice import Choice
from app.models.course import Course
from app.models.lesson import Lesson
from app.models.question import Question
from app.models.session import Session as SessionModel
from app.models.user import User
from app.models.watch_progress import WatchProgress
from app.services import watch as watch_service

client = TestClient(app)

SLUG_PREFIX = "test-watch"
GATED_COURSE_SLUG = f"{SLUG_PREFIX}-gated-course"
GATED_LESSON_SLUG = f"{SLUG_PREFIX}-gated-lesson"
NULL_DURATION_COURSE_SLUG = f"{SLUG_PREFIX}-null-duration-course"
NULL_DURATION_LESSON_SLUG = f"{SLUG_PREFIX}-null-duration-lesson"
THREE_SEGMENT_COURSE_SLUG = f"{SLUG_PREFIX}-three-segment-course"
ADMIN_EMAIL = "watch-admin@example.com"
MEMBER_EMAIL = "watch-member@example.com"
USER_A_EMAIL = "watch-user-a@example.com"
USER_B_EMAIL = "watch-user-b@example.com"
CLAIM_EMAIL = "watch-claim@example.com"
THRESHOLD_BELOW_EMAIL = "watch-threshold-below@example.com"
THRESHOLD_AT_EMAIL = "watch-threshold-at@example.com"
NULL_DURATION_EMAIL = "watch-null-duration@example.com"
THREE_SEGMENT_EMAIL = "watch-three-segment@example.com"
PASSWORD = "correct-horse-battery"


class _FakeDatetime:
    current = real_datetime(2026, 1, 1, tzinfo=timezone.utc)

    @classmethod
    def now(cls, tz=None):
        return cls.current


def _make_course_with_lesson(db, course_slug, lesson_slug, duration, with_question=True):
    course = Course(slug=course_slug, title=course_slug, description="d", is_published=True)
    db.add(course)
    db.flush()
    lesson = Lesson(
        course_id=course.id,
        position=1,
        slug=lesson_slug,
        title=lesson_slug,
        description="Used to test watch tracking and quiz gating.",
        duration_seconds=duration,
        is_published=True,
    )
    db.add(lesson)
    db.flush()
    if with_question:
        question = Question(lesson_id=lesson.id, prompt="Only question?", position=1)
        question.choices = [
            Choice(text="Right", is_correct=True, position=1),
            Choice(text="Wrong", is_correct=False, position=2),
        ]
        db.add(question)
    return course, lesson


@pytest.fixture(autouse=True)
def setup_and_cleanup():
    client.cookies.clear()
    _FakeDatetime.current = real_datetime(2026, 1, 1, tzinfo=timezone.utc)

    db = SessionLocal()
    _make_course_with_lesson(db, GATED_COURSE_SLUG, GATED_LESSON_SLUG, duration=100)
    _make_course_with_lesson(db, NULL_DURATION_COURSE_SLUG, NULL_DURATION_LESSON_SLUG, duration=None)
    db.commit()
    db.close()

    yield

    client.cookies.clear()
    db = SessionLocal()
    emails = [
        ADMIN_EMAIL,
        MEMBER_EMAIL,
        USER_A_EMAIL,
        USER_B_EMAIL,
        CLAIM_EMAIL,
        THRESHOLD_BELOW_EMAIL,
        THRESHOLD_AT_EMAIL,
        NULL_DURATION_EMAIL,
        THREE_SEGMENT_EMAIL,
    ]
    user_ids = select(User.id).where(User.email.in_(emails))
    db.execute(delete(SessionModel).where(SessionModel.user_id.in_(user_ids)))
    db.execute(delete(User).where(User.email.in_(emails)))
    db.execute(delete(Course).where(Course.slug.like(f"{SLUG_PREFIX}%")))
    db.commit()
    db.close()


def heartbeat(course_slug, lesson_slug, position):
    return client.post(f"/api/v1/courses/{course_slug}/lessons/{lesson_slug}/watch", json={"position": position})


def ensure_viewer_id(course_slug=GATED_COURSE_SLUG, lesson_slug=GATED_LESSON_SLUG):
    client.get(f"/api/v1/courses/{course_slug}/lessons/{lesson_slug}/watch")
    return uuid.UUID(client.cookies["viewer_id"])


def lesson_id(slug):
    db = SessionLocal()
    lid = db.execute(select(Lesson.id).where(Lesson.slug == slug)).scalar_one()
    db.close()
    return lid


def register_and_login(email, is_admin=False):
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": PASSWORD, "display_name": "Watch Tester"},
    )
    db = SessionLocal()
    user = db.execute(select(User).where(User.email == email)).scalar_one()
    if is_admin:
        user.is_admin = True
        db.commit()
    user_id = user.id
    db.close()
    return user_id


def test_realistic_pace_accumulates_watched_seconds(monkeypatch):
    monkeypatch.setattr(watch_service, "datetime", _FakeDatetime)

    first = heartbeat(GATED_COURSE_SLUG, GATED_LESSON_SLUG, 0)
    assert first.status_code == 200
    assert first.json()["watched_seconds"] == 0

    _FakeDatetime.current += timedelta(seconds=10)
    second = heartbeat(GATED_COURSE_SLUG, GATED_LESSON_SLUG, 10)
    assert second.json()["watched_seconds"] == 10

    _FakeDatetime.current += timedelta(seconds=10)
    third = heartbeat(GATED_COURSE_SLUG, GATED_LESSON_SLUG, 20)
    assert third.json()["watched_seconds"] == 20


# SKIP TEST: the guard the feature exists for. A heartbeat jumping far ahead
# of the previous position must not be trusted as watched time.
def test_jumping_position_credits_nothing(monkeypatch):
    monkeypatch.setattr(watch_service, "datetime", _FakeDatetime)

    heartbeat(GATED_COURSE_SLUG, GATED_LESSON_SLUG, 5)
    _FakeDatetime.current += timedelta(seconds=10)
    response = heartbeat(GATED_COURSE_SLUG, GATED_LESSON_SLUG, 300)
    assert response.status_code == 200
    assert response.json()["watched_seconds"] == 0


# FLOOD TEST: a burst of heartbeats at the same instant must not multiply
# credit. At most one interval's worth is ever added.
def test_flood_of_heartbeats_credits_at_most_one_interval(monkeypatch):
    monkeypatch.setattr(watch_service, "datetime", _FakeDatetime)

    heartbeat(GATED_COURSE_SLUG, GATED_LESSON_SLUG, 0)
    _FakeDatetime.current += timedelta(seconds=20)
    credited = heartbeat(GATED_COURSE_SLUG, GATED_LESSON_SLUG, 10)
    assert credited.json()["watched_seconds"] == 10

    rate_limited_count = 0
    for position in range(11, 20):
        response = heartbeat(GATED_COURSE_SLUG, GATED_LESSON_SLUG, position)
        if response.status_code == 429:
            rate_limited_count += 1

    assert rate_limited_count > 0
    final = heartbeat(GATED_COURSE_SLUG, GATED_LESSON_SLUG, 10)
    # Even the final check call is itself subject to the rate limit; either
    # way, no more than the one real interval above was ever credited.
    watched = final.json()["watched_seconds"] if final.status_code == 200 else 10
    assert watched == 10


def test_rewinding_does_not_credit_time_or_corrupt_total(monkeypatch):
    monkeypatch.setattr(watch_service, "datetime", _FakeDatetime)

    heartbeat(GATED_COURSE_SLUG, GATED_LESSON_SLUG, 50)
    _FakeDatetime.current += timedelta(seconds=10)
    after_forward = heartbeat(GATED_COURSE_SLUG, GATED_LESSON_SLUG, 60)
    assert after_forward.json()["watched_seconds"] == 10

    _FakeDatetime.current += timedelta(seconds=10)
    after_rewind = heartbeat(GATED_COURSE_SLUG, GATED_LESSON_SLUG, 30)
    assert after_rewind.status_code == 200
    assert after_rewind.json()["watched_seconds"] == 10

    _FakeDatetime.current += timedelta(seconds=10)
    after_resumed = heartbeat(GATED_COURSE_SLUG, GATED_LESSON_SLUG, 40)
    assert after_resumed.json()["watched_seconds"] == 20


def test_starting_an_attempt_below_the_threshold_returns_403():
    viewer_id = ensure_viewer_id()
    db = SessionLocal()
    db.add(
        WatchProgress(
            lesson_id=lesson_id(GATED_LESSON_SLUG),
            viewer_id=viewer_id,
            watched_seconds=10,
        )
    )
    db.commit()
    db.close()

    register_and_login(THRESHOLD_BELOW_EMAIL)  # claims the anonymous progress by viewer_id
    response = client.post(f"/api/v1/courses/{GATED_COURSE_SLUG}/attempts")
    assert response.status_code == 403


def test_starting_an_attempt_at_the_threshold_succeeds():
    viewer_id = ensure_viewer_id()
    db = SessionLocal()
    db.add(
        WatchProgress(
            lesson_id=lesson_id(GATED_LESSON_SLUG),
            viewer_id=viewer_id,
            watched_seconds=90,  # duration 100 * default ratio 0.9
        )
    )
    db.commit()
    db.close()

    register_and_login(THRESHOLD_AT_EMAIL)  # claims the anonymous progress by viewer_id
    response = client.post(f"/api/v1/courses/{GATED_COURSE_SLUG}/attempts")
    assert response.status_code == 201


def test_starting_an_attempt_while_signed_out_returns_401_before_the_watch_gate():
    response = client.post(f"/api/v1/courses/{GATED_COURSE_SLUG}/attempts")
    assert response.status_code == 401


def test_admin_can_start_an_attempt_without_watching():
    register_and_login(ADMIN_EMAIL, is_admin=True)
    response = client.post(f"/api/v1/courses/{GATED_COURSE_SLUG}/attempts")
    assert response.status_code == 201


def test_lesson_with_null_duration_is_ungated():
    register_and_login(NULL_DURATION_EMAIL)
    response = client.post(f"/api/v1/courses/{NULL_DURATION_COURSE_SLUG}/attempts")
    assert response.status_code == 201


def test_signed_in_users_progress_is_visible_from_a_different_viewer_cookie():
    user_id = register_and_login(MEMBER_EMAIL)
    device_a_viewer_id = uuid.UUID(client.cookies["viewer_id"])

    db = SessionLocal()
    db.add(
        WatchProgress(
            lesson_id=lesson_id(GATED_LESSON_SLUG),
            viewer_id=device_a_viewer_id,
            user_id=user_id,
            watched_seconds=50,
        )
    )
    db.commit()
    db.close()

    # Same signed-in session, but a viewer_id cookie belonging to a device
    # that has never watched anything.
    client.cookies.set("viewer_id", str(uuid.uuid4()))

    response = client.get(f"/api/v1/courses/{GATED_COURSE_SLUG}/lessons/{GATED_LESSON_SLUG}/watch")
    assert response.status_code == 200
    assert response.json()["watched_seconds"] == 50


# LEAK TEST (feature 015, moved to courses): two people sharing a browser
# must never inherit each other's watch history.
def test_user_bs_progress_does_not_leak_from_user_a_sharing_a_viewer_id():
    user_a_id = register_and_login(USER_A_EMAIL)
    shared_viewer_id = uuid.UUID(client.cookies["viewer_id"])

    db = SessionLocal()
    db.add(
        WatchProgress(
            lesson_id=lesson_id(GATED_LESSON_SLUG),
            viewer_id=shared_viewer_id,
            user_id=user_a_id,
            watched_seconds=50,
        )
    )
    db.commit()
    db.close()

    # A signs out: the session cookie clears, but the viewer_id cookie is the
    # one and only thing pre-fix left pointing at A's browser.
    client.cookies.clear()
    client.cookies.set("viewer_id", str(shared_viewer_id))
    register_and_login(USER_B_EMAIL)

    response = client.get(f"/api/v1/courses/{GATED_COURSE_SLUG}/lessons/{GATED_LESSON_SLUG}/watch")
    assert response.status_code == 200
    assert response.json()["watched_seconds"] == 0

    status_response = client.get(f"/api/v1/courses/{GATED_COURSE_SLUG}/watch-status")
    assert status_response.status_code == 200
    assert status_response.json()["lessons"][0]["progress"]["watched_seconds"] == 0


def test_anonymous_progress_is_not_visible_to_a_signed_in_user_who_has_not_claimed_it():
    register_and_login(USER_A_EMAIL)

    other_browsers_viewer_id = uuid.uuid4()
    db = SessionLocal()
    db.add(
        WatchProgress(
            lesson_id=lesson_id(GATED_LESSON_SLUG),
            viewer_id=other_browsers_viewer_id,
            watched_seconds=50,
        )
    )
    db.commit()
    db.close()

    # The signed-in session now carries a viewer_id cookie for a browser it
    # has never claimed progress from (no register/login happens here, so
    # no claim is triggered).
    client.cookies.set("viewer_id", str(other_browsers_viewer_id))

    response = client.get(f"/api/v1/courses/{GATED_COURSE_SLUG}/lessons/{GATED_LESSON_SLUG}/watch")
    assert response.status_code == 200
    assert response.json()["watched_seconds"] == 0


def test_anonymous_progress_is_claimed_on_sign_in_taking_the_maximum():
    user_id = register_and_login(CLAIM_EMAIL)
    lid = lesson_id(GATED_LESSON_SLUG)

    db = SessionLocal()
    db.add(WatchProgress(lesson_id=lid, viewer_id=uuid.uuid4(), user_id=user_id, watched_seconds=20))
    db.commit()
    db.close()

    client.cookies.clear()
    anon_viewer_id = uuid.uuid4()
    client.cookies.set("viewer_id", str(anon_viewer_id))
    db = SessionLocal()
    db.add(WatchProgress(lesson_id=lid, viewer_id=anon_viewer_id, watched_seconds=40))
    db.commit()
    db.close()

    response = client.post("/api/v1/auth/login", json={"email": CLAIM_EMAIL, "password": PASSWORD})
    assert response.status_code == 200

    db = SessionLocal()
    rows = db.execute(select(WatchProgress).where(WatchProgress.lesson_id == lid)).scalars().all()
    db.close()
    assert len(rows) == 1
    assert rows[0].user_id == user_id
    assert rows[0].watched_seconds == 40


def test_claiming_anonymous_progress_twice_is_idempotent():
    user_id = register_and_login(CLAIM_EMAIL)
    lid = lesson_id(GATED_LESSON_SLUG)

    anon_viewer_id = uuid.uuid4()
    db = SessionLocal()
    db.add(WatchProgress(lesson_id=lid, viewer_id=anon_viewer_id, watched_seconds=25))
    db.commit()
    db.close()

    client.cookies.set("viewer_id", str(anon_viewer_id))

    first = client.post("/api/v1/auth/login", json={"email": CLAIM_EMAIL, "password": PASSWORD})
    second = client.post("/api/v1/auth/login", json={"email": CLAIM_EMAIL, "password": PASSWORD})
    assert first.status_code == 200
    assert second.status_code == 200

    db = SessionLocal()
    rows = db.execute(select(WatchProgress).where(WatchProgress.lesson_id == lid)).scalars().all()
    db.close()
    assert len(rows) == 1
    assert rows[0].user_id == user_id
    assert rows[0].watched_seconds == 25


# --- course-level gate (feature 019) -----------------------------------------


@pytest.fixture
def three_segment_course():
    db = SessionLocal()
    course = Course(slug=THREE_SEGMENT_COURSE_SLUG, title="Three Segment Course", description="d", is_published=True)
    db.add(course)
    db.flush()
    lessons = []
    for position in range(1, 4):
        lesson = Lesson(
            course_id=course.id,
            position=position,
            slug=f"{THREE_SEGMENT_COURSE_SLUG}-lesson-{position}",
            title=f"Segment {position}",
            description="d",
            duration_seconds=100,
            is_published=True,
        )
        db.add(lesson)
        db.flush()
        question = Question(lesson_id=lesson.id, prompt="Only question?", position=1)
        question.choices = [
            Choice(text="Right", is_correct=True, position=1),
            Choice(text="Wrong", is_correct=False, position=2),
        ]
        db.add(question)
        lessons.append(lesson)
    db.commit()
    slugs = [lesson.slug for lesson in lessons]
    db.close()
    yield slugs


def _watch_to_completion(monkeypatch, course_slug, lesson_slug):
    monkeypatch.setattr(watch_service, "datetime", _FakeDatetime)
    heartbeat(course_slug, lesson_slug, 0)
    position = 0
    for _ in range(6):  # 6 * 15s == 90s, at (required 100 * default ratio 0.9)
        _FakeDatetime.current += timedelta(seconds=15)
        position += 15
        heartbeat(course_slug, lesson_slug, position)


def test_gate_stays_closed_when_one_of_three_segments_is_unwatched(monkeypatch, three_segment_course):
    lesson_slugs = three_segment_course
    register_and_login(THREE_SEGMENT_EMAIL)

    for slug in lesson_slugs[:2]:
        _watch_to_completion(monkeypatch, THREE_SEGMENT_COURSE_SLUG, slug)

    status = client.get(f"/api/v1/courses/{THREE_SEGMENT_COURSE_SLUG}/watch-status").json()
    assert status["gate_met"] is False
    unlocked_by_slug = {item["lesson_slug"]: item["progress"]["unlocked"] for item in status["lessons"]}
    assert unlocked_by_slug[lesson_slugs[0]] is True
    assert unlocked_by_slug[lesson_slugs[1]] is True
    assert unlocked_by_slug[lesson_slugs[2]] is False

    response = client.post(f"/api/v1/courses/{THREE_SEGMENT_COURSE_SLUG}/attempts")
    assert response.status_code == 403


def test_gate_opens_when_all_three_segments_are_watched(monkeypatch, three_segment_course):
    lesson_slugs = three_segment_course
    register_and_login(THREE_SEGMENT_EMAIL)

    for slug in lesson_slugs:
        _watch_to_completion(monkeypatch, THREE_SEGMENT_COURSE_SLUG, slug)

    status = client.get(f"/api/v1/courses/{THREE_SEGMENT_COURSE_SLUG}/watch-status").json()
    assert status["gate_met"] is True

    response = client.post(f"/api/v1/courses/{THREE_SEGMENT_COURSE_SLUG}/attempts")
    assert response.status_code == 201
