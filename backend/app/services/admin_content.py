import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import ROUND_CEILING, Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.constants.credit import MIN_AWARDABLE, MINUTES_PER_CREDIT
from app.constants.fields_of_study import CPA_REQUIRED, TAX_CREDENTIAL_REQUIRED, credential_tag_for
from app.constants.program_kind import PROGRAM_KIND_GENERAL
from app.constants.program_levels import LEVELS_REQUIRING_PREREQUISITES, PROGRAM_LEVELS
from app.constants.question_minimums import (
    MIN_CHOICES_ASSESSMENT,
    required_assessment_questions,
    required_review_questions,
)
from app.models.attempt import Attempt
from app.models.choice import Choice
from app.models.course import Course
from app.models.learning_objective import LearningObjective
from app.models.lesson import Lesson
from app.models.question import QUESTION_KIND_ASSESSMENT, QUESTION_KIND_REVIEW, Question
from app.models.source import Source
from app.models.subject_matter_expert import SubjectMatterExpert
from app.services import objective_coverage
from app.services import policies as policies_service
from app.services import sponsor_profile as sponsor_profile_service

MIN_CHOICES_PER_QUESTION = 2

# Fields on Course that record a review or a computed credit having
# happened, not the content being reviewed or measured - excluded from the
# content_updated_at bump for exactly the reason spelled out in
# current-feature.md: bumping on these would make `reviewed_at <
# content_updated_at` (or `credit_computed_at < content_updated_at`) true
# the instant after every review or recompute. review_cycle is set from the
# same Review panel and PATCH as the rest of that group (ReviewPanel.jsx
# sends all five fields together) - excluding only four of the five would
# reintroduce that exact bug the moment a reviewer also touches the cycle,
# which was caught live in browser testing. The seven credit_* fields get
# the same treatment for the same reason (feature 022): storing a computed
# credit must not itself make the credit stale. expires_on (feature 026)
# joins the set for the same structural reason though a different rule
# motivates it: it's an administrative deadline (9.02.2), not educational
# material a content reviewer checks for accuracy, so a sponsor extending it
# shouldn't force a full re-review any more than recording the review itself
# should stale the review.
REVIEW_CHAIN_FIELDS = {
    "developer_id",
    "reviewer_id",
    "reviewed_at",
    "review_notes",
    "review_cycle",
    "expires_on",
    "credit_award",
    "credit_raw_minutes",
    "credit_word_count",
    "credit_av_seconds",
    "credit_question_count",
    "credit_formula_version",
    "credit_computed_at",
}


class CourseNotFoundError(Exception):
    """Raised when a course id does not match any course."""


class LessonNotFoundError(Exception):
    """Raised when a lesson id does not match any lesson."""


class QuestionNotFoundError(Exception):
    """Raised when a question id does not match any question."""


class ObjectiveNotFoundError(Exception):
    """Raised when a learning objective id does not match any objective."""


class ChoiceNotFoundError(Exception):
    """Raised when a choice id does not match any choice."""


class SourceNotFoundError(Exception):
    """Raised when a source id does not match any source."""


class SMENotFoundError(Exception):
    """Raised when a subject matter expert id does not match any record."""


class SMEInUseError(Exception):
    """Raised when deleting a subject matter expert who is a course's developer or reviewer."""


class SameExpertError(Exception):
    """Raised when a course's developer and reviewer would be set to the same person.

    The database CHECK constraint (ck_courses_developer_reviewer_differ) is
    the real backstop and blocks this unconditionally; this check exists so
    the API returns a clean 409 instead of a raw IntegrityError."""


class SlugTakenError(Exception):
    """Raised when a slug collides with an existing one."""


class ProgramKindChangeWhilePublishedError(Exception):
    """Raised when program_kind is changed on a published course.

    A published general course switched to 'cpe' would be presenting itself
    as a CPE program without ever having passed the CPE publish gate - see
    current-feature.md, Part 3's "matching hazard on the other side"."""


class CourseHasAttemptsError(Exception):
    """Raised when deleting a course that has completed attempts."""


class LessonHasAttemptsError(Exception):
    """Raised when deleting a lesson whose course has completed attempts."""


class LastLessonError(Exception):
    """Raised when deleting the only remaining lesson of a course."""


class PublishValidationError(Exception):
    """Raised when publishing a course that fails validate_for_publish."""

    def __init__(self, errors: list[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


@dataclass
class CourseListItem:
    id: int
    slug: str
    title: str
    is_published: bool
    lesson_count: int


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.strip().lower()).strip("-")
    return slug or "course"


def _check_slug_available(db: Session, model, slug: str, exclude_id: int | None = None) -> None:
    stmt = select(model.id).where(model.slug == slug)
    if exclude_id is not None:
        stmt = stmt.where(model.id != exclude_id)
    if db.execute(stmt).scalar_one_or_none() is not None:
        raise SlugTakenError(f"Slug '{slug}' is already in use")


def _unique_slug(db: Session, model, base_slug: str) -> str:
    # For the lesson a course creates for itself: the author never picks this
    # slug, so a collision must be resolved automatically rather than surfaced
    # as a 409 for something they didn't type.
    slug = base_slug
    suffix = 2
    while db.execute(select(model.id).where(model.slug == slug)).scalar_one_or_none() is not None:
        slug = f"{base_slug}-{suffix}"
        suffix += 1
    return slug


def touch_content_updated_at(db: Session, course_id: int) -> None:
    """The single choke point for "did this mutation change what a
    participant would see". Every write path that touches course fields,
    objectives, lessons, questions, choices, video, or thumbnails calls this
    - including the video/thumbnail upload routes in app/routers/admin.py,
    which write directly rather than through a service function here.

    Deliberately NOT called for: developer_id, reviewer_id, reviewed_at,
    review_notes, sources, or publish/unpublish - see current-feature.md.
    """
    course = db.get(Course, course_id)
    if course is not None:
        course.content_updated_at = datetime.now(timezone.utc)


def _renumber(db: Session, items: list) -> None:
    # Two-phase so no intermediate UPDATE collides with the (parent_id, position)
    # unique constraint: bump everything to a value nothing else holds, then
    # assign the final contiguous positions.
    for item in items:
        item.position = -item.id
    db.flush()
    for position, item in enumerate(items, start=1):
        item.position = position
    db.flush()


# --- courses ---------------------------------------------------------------


def _course_or_404(db: Session, course_id: int) -> Course:
    course = db.get(Course, course_id)
    if course is None:
        raise CourseNotFoundError(f"Course {course_id} not found")
    return course


def _course_with_content_or_404(db: Session, course_id: int) -> Course:
    stmt = (
        select(Course)
        .where(Course.id == course_id)
        .options(
            selectinload(Course.lessons).selectinload(Lesson.questions).selectinload(Question.choices),
            selectinload(Course.learning_objectives),
            selectinload(Course.sources),
            selectinload(Course.developer),
            selectinload(Course.reviewer),
        )
    )
    course = db.execute(stmt).scalar_one_or_none()
    if course is None:
        raise CourseNotFoundError(f"Course {course_id} not found")
    return course


def list_courses(db: Session) -> list[CourseListItem]:
    stmt = (
        select(Course, func.count(Lesson.id))
        .outerjoin(Lesson, Lesson.course_id == Course.id)
        .group_by(Course.id)
        .order_by(Course.id)
    )
    rows = db.execute(stmt).all()
    return [
        CourseListItem(id=course.id, slug=course.slug, title=course.title, is_published=course.is_published, lesson_count=lesson_count)
        for course, lesson_count in rows
    ]


def get_course(db: Session, course_id: int) -> Course:
    return _course_with_content_or_404(db, course_id)


def create_course(db: Session, title: str, slug: str | None, description: str) -> Course:
    final_slug = slug.strip().lower() if slug else slugify(title)
    _check_slug_available(db, Course, final_slug)

    course = Course(title=title, slug=final_slug, description=description)
    db.add(course)
    db.flush()

    # Every course gets its first lesson here, in the same transaction, so a
    # course with zero lessons - a state nothing in the product can render or
    # publish - never exists. See feature 019a.
    lesson_slug = _unique_slug(db, Lesson, slugify(title))
    db.add(Lesson(course_id=course.id, position=1, title=title, slug=lesson_slug, description=""))

    db.commit()
    db.refresh(course)
    return course


def update_course(db: Session, course_id: int, updates: dict) -> Course:
    course = _course_or_404(db, course_id)

    if (
        "program_kind" in updates
        and updates["program_kind"] is not None
        and updates["program_kind"] != course.program_kind
        and course.is_published
    ):
        raise ProgramKindChangeWhilePublishedError(
            "Unpublish this course before changing whether it's offered as a CPE program"
        )

    if "slug" in updates and updates["slug"] is not None:
        new_slug = updates["slug"].strip().lower()
        if new_slug != course.slug:
            _check_slug_available(db, Course, new_slug, exclude_id=course_id)
        updates["slug"] = new_slug

    for field, value in updates.items():
        setattr(course, field, value)

    if (
        course.developer_id is not None
        and course.reviewer_id is not None
        and course.developer_id == course.reviewer_id
    ):
        raise SameExpertError("Developer and reviewer must be different people")

    if set(updates.keys()) - REVIEW_CHAIN_FIELDS:
        touch_content_updated_at(db, course_id)

    db.commit()
    return _course_with_content_or_404(db, course_id)


def delete_course(db: Session, course_id: int) -> None:
    course = _course_or_404(db, course_id)

    completed_count = db.execute(
        select(func.count())
        .select_from(Attempt)
        .where(Attempt.course_id == course_id, Attempt.completed_at.is_not(None))
    ).scalar_one()
    if completed_count > 0:
        raise CourseHasAttemptsError(
            f"Course has {completed_count} completed attempt(s) and cannot be deleted"
        )

    db.delete(course)
    db.commit()


def publish_course(db: Session, course_id: int) -> Course:
    course = _course_with_content_or_404(db, course_id)
    errors = validate_for_publish(db, course)
    if errors:
        raise PublishValidationError(errors)

    # validate_for_publish already required every lesson to have a video and
    # at least one well-formed question, so publishing the course publishes
    # its lessons with it - there is no separate per-lesson publish action.
    course.is_published = True
    for lesson in course.lessons:
        lesson.is_published = True
    db.commit()
    return _course_with_content_or_404(db, course_id)


def check_publish_course(db: Session, course_id: int) -> list[str]:
    course = _course_with_content_or_404(db, course_id)
    return validate_for_publish(db, course)


def unpublish_course(db: Session, course_id: int) -> Course:
    course = _course_or_404(db, course_id)
    course.is_published = False
    db.commit()
    return _course_with_content_or_404(db, course_id)


def validate_for_publish(db: Session, course: Course) -> list[str]:
    errors = []
    is_general = course.program_kind == PROGRAM_KIND_GENERAL

    # Feature 024: a course that cannot produce a compliant certificate
    # should not be able to enrol anyone (9.01 items 1 and 8 - sponsor name
    # and NASBA registry ID). See app/services/sponsor_profile.py for why
    # contact details and the optional state registry ID don't block this.
    # Feature 029: a general certificate never prints 9.01's certificate
    # fields at all except the sponsor name ("Issued by") - see
    # current-feature.md, Part 5's table - so only that one field can block
    # a general course, regardless of registry_status.
    sponsor = sponsor_profile_service.get_sponsor_profile(db)
    if is_general:
        missing_sponsor_fields = [] if sponsor.name.strip() else [sponsor_profile_service.FIELD_LABELS["name"]]
    else:
        missing_sponsor_fields = sponsor_profile_service.missing_fields(sponsor)
    if missing_sponsor_fields:
        errors.append(
            "The sponsor profile is missing: " + ", ".join(missing_sponsor_fields) + ". "
            "Complete it on the sponsor settings page before publishing."
        )

    # 8.01.1/9.02: another site-wide condition, same reasoning as the sponsor
    # profile check above - this isn't something wrong with this particular
    # course, so the message says so and points at where to fix it rather
    # than reading like a course-content defect.
    unwritten_policies = policies_service.placeholder_titles(db)
    if unwritten_policies:
        errors.append(
            "The sponsor's policies are not yet published: " + ", ".join(unwritten_policies) + ". "
            "This isn't something wrong with this course - write them on the policies admin page "
            "before any course can publish."
        )

    if not course.title.strip():
        errors.append("Title is required")
    if not course.slug.strip():
        errors.append("Slug is required")
    if not course.description.strip():
        errors.append("Description is required")
    if not course.lessons:
        errors.append("Course must have at least one lesson")

    # Still enforced for a general course - see current-feature.md, Part 5:
    # "a course whose quiz is empty is not publishable regardless of what it
    # is offered as." A CPE course's credit-derived floor below already
    # requires more than one once credit is computed; this is the
    # unconditional backstop general courses now rely on entirely, since
    # they carry no credit for that floor to apply to.
    if not any(
        question.kind == QUESTION_KIND_ASSESSMENT for lesson in course.lessons for question in lesson.questions
    ):
        errors.append("Course must have at least one qualified assessment question")

    if not course.learning_objectives:
        errors.append("Course must have at least one learning objective")
    else:
        for objective in course.learning_objectives:
            if not objective.text.strip():
                errors.append(f"Learning objective {objective.position} cannot be blank")

    if course.program_level not in PROGRAM_LEVELS:
        errors.append("Program level must be one of: " + ", ".join(PROGRAM_LEVELS))

    # Feature 029: relaxed for a general course - not applicable. See
    # current-feature.md, Part 5's table.
    if not is_general and not course.field_of_study.strip():
        errors.append("Field of study is required")

    if course.expires_on is None:
        errors.append("An expiration date is required for self study programs (9.02.2)")

    if course.program_level in LEVELS_REQUIRING_PREREQUISITES:
        if not (course.prerequisites and course.prerequisites.strip()):
            errors.append("Prerequisites are required for intermediate, advanced, and update courses")
        if not (course.advance_preparation and course.advance_preparation.strip()):
            errors.append("Advance preparation is required for intermediate, advanced, and update courses")

    # Feature 029: the two-person SME chain, and the licensed-CPA/tax-
    # credential check downstream of it, are a CPE control - relaxed for a
    # general course. See current-feature.md, Part 5's table.
    if not is_general:
        if course.developer_id is None:
            errors.append("A developer is required")
        if course.reviewer_id is None:
            errors.append("A reviewer is required")
        if (
            course.developer_id is not None
            and course.reviewer_id is not None
            and course.developer_id == course.reviewer_id
        ):
            errors.append("Developer and reviewer must be different people")
        if course.reviewed_at is None:
            errors.append("A review date is required")
        elif course.reviewed_at < course.content_updated_at:
            errors.append("This course has changed since it was reviewed")

        credential_tag = credential_tag_for(course.field_of_study)
        if credential_tag is not None:
            experts = [expert for expert in (course.developer, course.reviewer) if expert is not None]
            if credential_tag == CPA_REQUIRED and not any(expert.is_licensed_cpa for expert in experts):
                errors.append("An accounting or auditing course needs a licensed CPA as developer or reviewer")
            elif credential_tag == TAX_CREDENTIAL_REQUIRED and not any(
                expert.is_licensed_cpa or expert.is_tax_attorney or expert.is_enrolled_agent for expert in experts
            ):
                errors.append(
                    "A taxes course needs a licensed CPA, tax attorney, or enrolled agent as developer or reviewer"
                )

    # Feature 029: relaxed for a general course - there is no credit. See
    # current-feature.md, Part 5's table.
    if not is_general:
        if course.credit_computed_at is None:
            errors.append("Credit has not been computed yet")
        elif course.credit_computed_at < course.content_updated_at:
            errors.append("This course has changed since credit was last computed")

        if course.credit_award is not None and course.credit_award < MIN_AWARDABLE:
            # 7.01: a raw credit below 0.2 is not awardable. Name the gap in
            # seconds, not just "too short" - current-feature.md's own example.
            remaining_minutes = (MIN_AWARDABLE * MINUTES_PER_CREDIT) - (course.credit_raw_minutes or Decimal(0))
            remaining_seconds = int((remaining_minutes * 60).to_integral_value(rounding=ROUND_CEILING))
            errors.append(
                f"This course computes to {course.credit_award} credit, below the {MIN_AWARDABLE} minimum "
                f"award. Add about {remaining_seconds} more seconds of qualifying audio/video, words, or "
                "questions to reach it."
            )

    for lesson in course.lessons:
        if not lesson.video_key:
            errors.append(f"Lesson '{lesson.title}' must have a video")
        # Feature 029: relaxed for a general course - an input to a formula
        # that is not running.
        if (
            not is_general
            and lesson.av_is_additional_learning
            and lesson.duration_seconds is None
        ):
            errors.append(f"Lesson '{lesson.title}' counts its runtime toward credit but has no duration")
        if not lesson.questions:
            errors.append(f"Lesson '{lesson.title}' must have at least one question")
        for question in lesson.questions:
            if len(question.choices) < MIN_CHOICES_PER_QUESTION:
                errors.append(
                    f"Lesson '{lesson.title}' question {question.position} needs at least "
                    f"{MIN_CHOICES_PER_QUESTION} choices"
                )
            # Feature 029: relaxed for a general course - true/false is a
            # legitimate item type for a general quiz.
            if (
                not is_general
                and question.kind == QUESTION_KIND_ASSESSMENT
                and len(question.choices) < MIN_CHOICES_ASSESSMENT
            ):
                errors.append(
                    f"Lesson '{lesson.title}' question {question.position} is on the qualified assessment "
                    f"and needs at least {MIN_CHOICES_ASSESSMENT} choices - forced-choice responses are not "
                    "permissible on the qualified assessment (6.01.2)"
                )
            # Feature 029: relaxed for a general course - good practice, not
            # a gate here (5.01.2.2 is a CPE rule).
            if (
                not is_general
                and question.kind == QUESTION_KIND_REVIEW
                and not (question.feedback and question.feedback.strip())
            ):
                errors.append(
                    f"Lesson '{lesson.title}' question {question.position} is a review question and needs "
                    "feedback shown after answering (5.01.2.2)"
                )
            correct_count = sum(1 for choice in question.choices if choice.is_correct)
            if correct_count != 1:
                errors.append(
                    f"Lesson '{lesson.title}' question {question.position} must have exactly one correct choice"
                )

    # 6.01.2: "the assessment ... must measure 75 percent or more of the
    # learning objectives for the program." Independent of credit - runs
    # whenever the course has objectives at all (the earlier rule above
    # already requires at least one). Names the uncovered objectives by
    # their own text rather than reporting a percentage, so an author who is
    # one objective short is told which one. Feature 029: relaxed for a
    # general course - a 6.01.2 assessment rule.
    if not is_general and course.learning_objectives:
        coverage = objective_coverage.compute(course)
        if coverage.ratio < objective_coverage.COVERAGE_THRESHOLD:
            uncovered_text = "; ".join(f'"{o.text.strip()}"' for o in coverage.uncovered)
            errors.append(
                "The qualified assessment must measure at least 75% of this course's learning objectives "
                f"(6.01.2); it measures {coverage.covered_count} of {coverage.total_objectives}. "
                f"No assessment question is tagged to: {uncovered_text}"
            )

    # 5.01.2.1 and 6.01.2's floors are per credit - enforcing them against a
    # credit that hasn't been computed yet would be enforcing them against
    # zero, so they only run once feature 022's credit exists. Feature 029:
    # relaxed for a general course regardless of whether credit happens to
    # be computed - floors expressed per credit, against a credit that does
    # not exist, are floors against zero.
    if not is_general and course.credit_award is not None:
        all_questions = [question for lesson in course.lessons for question in lesson.questions]
        review_questions = [q for q in all_questions if q.kind == QUESTION_KIND_REVIEW]
        assessment_questions = [q for q in all_questions if q.kind == QUESTION_KIND_ASSESSMENT]
        # "True or false" (two-choice) questions do not count toward the
        # review minimum (5.01.2.1) - they can still be published as review
        # content, just not counted here.
        counted_review_questions = [q for q in review_questions if len(q.choices) != 2]

        required_review = required_review_questions(course.credit_award)
        if len(counted_review_questions) < required_review:
            errors.append(
                f"This course needs at least {required_review} review question(s) counting toward the "
                f"5.01.2.1 minimum for {course.credit_award} credit (two-choice questions don't count); "
                f"it has {len(counted_review_questions)}"
            )

        required_assessment = required_assessment_questions(course.credit_award)
        if len(assessment_questions) < required_assessment:
            errors.append(
                f"This course needs at least {required_assessment} qualified assessment question(s) for "
                f"{course.credit_award} credit under 6.01.2; it has {len(assessment_questions)}"
            )

        # 6.01.2: "duplicate review and qualified assessment questions are
        # not allowed" (except where recall is the learning strategy - not
        # modeled here, so this is conservative). Exact match only, after
        # normalising whitespace and case; a near-duplicate is the
        # reviewer's judgment call under 021, not something this can catch.
        def _normalize(prompt: str) -> str:
            return " ".join(prompt.split()).strip().lower()

        review_by_prompt = {}
        for question in review_questions:
            review_by_prompt.setdefault(_normalize(question.prompt), question)
        for question in assessment_questions:
            duplicate = review_by_prompt.get(_normalize(question.prompt))
            if duplicate is not None:
                errors.append(
                    "A review question and a qualified assessment question have the exact same prompt "
                    f"(\"{duplicate.prompt.strip()}\"). Duplicate review and assessment questions are not "
                    "allowed except in courses where recall of information is the learning strategy "
                    "(6.01.2). This check catches exact matches only - a near-duplicate prompt is a "
                    "reviewer judgment call under 021."
                )

    return errors


# --- lessons -----------------------------------------------------------------


def _lesson_or_404(db: Session, lesson_id: int) -> Lesson:
    lesson = db.get(Lesson, lesson_id)
    if lesson is None:
        raise LessonNotFoundError(f"Lesson {lesson_id} not found")
    return lesson


def _lesson_with_content_or_404(db: Session, lesson_id: int) -> Lesson:
    stmt = (
        select(Lesson)
        .where(Lesson.id == lesson_id)
        .options(selectinload(Lesson.questions).selectinload(Question.choices))
    )
    lesson = db.execute(stmt).scalar_one_or_none()
    if lesson is None:
        raise LessonNotFoundError(f"Lesson {lesson_id} not found")
    return lesson


def _question_or_404(db: Session, question_id: int) -> Question:
    stmt = (
        select(Question)
        .where(Question.id == question_id)
        .options(selectinload(Question.choices))
    )
    question = db.execute(stmt).scalar_one_or_none()
    if question is None:
        raise QuestionNotFoundError(f"Question {question_id} not found")
    return question


def _choice_or_404(db: Session, choice_id: int) -> Choice:
    choice = db.get(Choice, choice_id)
    if choice is None:
        raise ChoiceNotFoundError(f"Choice {choice_id} not found")
    return choice


def get_lesson(db: Session, lesson_id: int) -> Lesson:
    return _lesson_with_content_or_404(db, lesson_id)


def create_lesson(
    db: Session, course_id: int, title: str, slug: str | None, description: str, duration_seconds: int | None
) -> Lesson:
    _course_or_404(db, course_id)
    final_slug = slug.strip().lower() if slug else slugify(title)
    _check_slug_available(db, Lesson, final_slug)

    next_position = db.execute(
        select(func.coalesce(func.max(Lesson.position), 0)).where(Lesson.course_id == course_id)
    ).scalar_one()

    lesson = Lesson(
        course_id=course_id,
        position=next_position + 1,
        title=title,
        slug=final_slug,
        description=description,
        duration_seconds=duration_seconds,
    )
    db.add(lesson)
    touch_content_updated_at(db, course_id)
    db.commit()
    db.refresh(lesson)
    return lesson


def update_lesson(db: Session, lesson_id: int, updates: dict) -> Lesson:
    lesson = _lesson_or_404(db, lesson_id)

    if "slug" in updates and updates["slug"] is not None:
        new_slug = updates["slug"].strip().lower()
        if new_slug != lesson.slug:
            _check_slug_available(db, Lesson, new_slug, exclude_id=lesson_id)
        updates["slug"] = new_slug

    for field, value in updates.items():
        setattr(lesson, field, value)

    touch_content_updated_at(db, lesson.course_id)
    db.commit()
    return _lesson_with_content_or_404(db, lesson_id)


def delete_lesson(db: Session, lesson_id: int) -> None:
    lesson = _lesson_or_404(db, lesson_id)

    sibling_count = db.execute(
        select(func.count()).select_from(Lesson).where(Lesson.course_id == lesson.course_id)
    ).scalar_one()
    if sibling_count <= 1:
        raise LastLessonError("This is the only lesson in its course. Delete the course instead.")

    completed_count = db.execute(
        select(func.count())
        .select_from(Attempt)
        .where(Attempt.course_id == lesson.course_id, Attempt.completed_at.is_not(None))
    ).scalar_one()
    if completed_count > 0:
        raise LessonHasAttemptsError(
            f"This lesson's course has {completed_count} completed attempt(s) and cannot be edited"
        )

    course_id = lesson.course_id
    db.delete(lesson)
    db.flush()

    remaining = list(
        db.execute(select(Lesson).where(Lesson.course_id == course_id).order_by(Lesson.position)).scalars()
    )
    _renumber(db, remaining)
    touch_content_updated_at(db, course_id)
    db.commit()


def move_lesson(db: Session, lesson_id: int, direction: str) -> None:
    lesson = _lesson_or_404(db, lesson_id)
    ordered = list(
        db.execute(
            select(Lesson).where(Lesson.course_id == lesson.course_id).order_by(Lesson.position)
        ).scalars()
    )
    index = next(i for i, l in enumerate(ordered) if l.id == lesson_id)
    swap_with = index - 1 if direction == "up" else index + 1
    if 0 <= swap_with < len(ordered):
        ordered[index], ordered[swap_with] = ordered[swap_with], ordered[index]
        _renumber(db, ordered)
        touch_content_updated_at(db, lesson.course_id)
    db.commit()


# --- questions and choices ---------------------------------------------------


def create_question(db: Session, lesson_id: int, prompt: str) -> Question:
    lesson = _lesson_or_404(db, lesson_id)
    next_position = db.execute(
        select(func.coalesce(func.max(Question.position), 0)).where(Question.lesson_id == lesson_id)
    ).scalar_one()

    question = Question(lesson_id=lesson_id, prompt=prompt, position=next_position + 1)
    db.add(question)
    touch_content_updated_at(db, lesson.course_id)
    db.commit()
    db.refresh(question)
    return question


def update_question(db: Session, question_id: int, updates: dict) -> Question:
    question = _question_or_404(db, question_id)
    for field, value in updates.items():
        setattr(question, field, value)
    touch_content_updated_at(db, question.lesson.course_id)
    db.commit()
    return _question_or_404(db, question_id)


def delete_question(db: Session, question_id: int) -> None:
    question = _question_or_404(db, question_id)
    lesson_id = question.lesson_id
    course_id = question.lesson.course_id
    db.delete(question)
    db.flush()

    remaining = list(
        db.execute(
            select(Question).where(Question.lesson_id == lesson_id).order_by(Question.position)
        ).scalars()
    )
    _renumber(db, remaining)
    touch_content_updated_at(db, course_id)
    db.commit()


def move_question(db: Session, question_id: int, direction: str) -> None:
    question = _question_or_404(db, question_id)
    ordered = list(
        db.execute(
            select(Question)
            .where(Question.lesson_id == question.lesson_id)
            .order_by(Question.position)
        ).scalars()
    )
    index = next(i for i, q in enumerate(ordered) if q.id == question_id)
    swap_with = index - 1 if direction == "up" else index + 1
    if 0 <= swap_with < len(ordered):
        ordered[index], ordered[swap_with] = ordered[swap_with], ordered[index]
        _renumber(db, ordered)
        touch_content_updated_at(db, question.lesson.course_id)
    db.commit()


def create_choice(db: Session, question_id: int, text: str, is_correct: bool) -> Choice:
    question = _question_or_404(db, question_id)
    next_position = db.execute(
        select(func.coalesce(func.max(Choice.position), 0)).where(Choice.question_id == question_id)
    ).scalar_one()

    choice = Choice(question_id=question_id, text=text, is_correct=is_correct, position=next_position + 1)
    db.add(choice)
    touch_content_updated_at(db, question.lesson.course_id)
    db.commit()
    db.refresh(choice)
    return choice


def update_choice(db: Session, choice_id: int, updates: dict) -> Choice:
    choice = _choice_or_404(db, choice_id)
    for field, value in updates.items():
        setattr(choice, field, value)
    touch_content_updated_at(db, choice.question.lesson.course_id)
    db.commit()
    db.refresh(choice)
    return choice


def delete_choice(db: Session, choice_id: int) -> None:
    choice = _choice_or_404(db, choice_id)
    question_id = choice.question_id
    course_id = choice.question.lesson.course_id
    db.delete(choice)
    db.flush()

    remaining = list(
        db.execute(
            select(Choice).where(Choice.question_id == question_id).order_by(Choice.position)
        ).scalars()
    )
    _renumber(db, remaining)
    touch_content_updated_at(db, course_id)
    db.commit()


def move_choice(db: Session, choice_id: int, direction: str) -> None:
    choice = _choice_or_404(db, choice_id)
    ordered = list(
        db.execute(
            select(Choice).where(Choice.question_id == choice.question_id).order_by(Choice.position)
        ).scalars()
    )
    index = next(i for i, c in enumerate(ordered) if c.id == choice_id)
    swap_with = index - 1 if direction == "up" else index + 1
    if 0 <= swap_with < len(ordered):
        ordered[index], ordered[swap_with] = ordered[swap_with], ordered[index]
        _renumber(db, ordered)
        touch_content_updated_at(db, choice.question.lesson.course_id)
    db.commit()


def _objective_or_404(db: Session, objective_id: int) -> LearningObjective:
    objective = db.get(LearningObjective, objective_id)
    if objective is None:
        raise ObjectiveNotFoundError(f"Learning objective {objective_id} not found")
    return objective


def create_objective(db: Session, course_id: int, text: str) -> LearningObjective:
    _course_or_404(db, course_id)
    next_position = db.execute(
        select(func.coalesce(func.max(LearningObjective.position), 0)).where(
            LearningObjective.course_id == course_id
        )
    ).scalar_one()

    objective = LearningObjective(course_id=course_id, text=text, position=next_position + 1)
    db.add(objective)
    touch_content_updated_at(db, course_id)
    db.commit()
    db.refresh(objective)
    return objective


def update_objective(db: Session, objective_id: int, updates: dict) -> LearningObjective:
    objective = _objective_or_404(db, objective_id)
    for field, value in updates.items():
        setattr(objective, field, value)
    touch_content_updated_at(db, objective.course_id)
    db.commit()
    db.refresh(objective)
    return objective


def delete_objective(db: Session, objective_id: int) -> None:
    objective = _objective_or_404(db, objective_id)
    course_id = objective.course_id
    db.delete(objective)
    db.flush()

    remaining = list(
        db.execute(
            select(LearningObjective)
            .where(LearningObjective.course_id == course_id)
            .order_by(LearningObjective.position)
        ).scalars()
    )
    _renumber(db, remaining)
    touch_content_updated_at(db, course_id)
    db.commit()


def move_objective(db: Session, objective_id: int, direction: str) -> None:
    objective = _objective_or_404(db, objective_id)
    ordered = list(
        db.execute(
            select(LearningObjective)
            .where(LearningObjective.course_id == objective.course_id)
            .order_by(LearningObjective.position)
        ).scalars()
    )
    index = next(i for i, o in enumerate(ordered) if o.id == objective_id)
    swap_with = index - 1 if direction == "up" else index + 1
    if 0 <= swap_with < len(ordered):
        ordered[index], ordered[swap_with] = ordered[swap_with], ordered[index]
        _renumber(db, ordered)
        touch_content_updated_at(db, objective.course_id)
    db.commit()


def set_correct_choice(db: Session, question_id: int, choice_id: int) -> None:
    question = _question_or_404(db, question_id)
    if not any(choice.id == choice_id for choice in question.choices):
        raise ChoiceNotFoundError(f"Choice {choice_id} does not belong to question {question_id}")

    for choice in question.choices:
        choice.is_correct = choice.id == choice_id
    touch_content_updated_at(db, question.lesson.course_id)
    db.commit()


# --- sources -------------------------------------------------------------------


def _source_or_404(db: Session, source_id: int) -> Source:
    source = db.get(Source, source_id)
    if source is None:
        raise SourceNotFoundError(f"Source {source_id} not found")
    return source


def create_source(
    db: Session, course_id: int, citation: str, url: str | None, retrieved_on: date | None
) -> Source:
    _course_or_404(db, course_id)
    next_position = db.execute(
        select(func.coalesce(func.max(Source.position), 0)).where(Source.course_id == course_id)
    ).scalar_one()

    source = Source(
        course_id=course_id, citation=citation, url=url, retrieved_on=retrieved_on, position=next_position + 1
    )
    db.add(source)
    # Deliberately not touch_content_updated_at: a source is a citation for
    # the reviewer's judgment, not participant-visible content - see
    # current-feature.md, "Sources are recorded, not required".
    db.commit()
    db.refresh(source)
    return source


def update_source(db: Session, source_id: int, updates: dict) -> Source:
    source = _source_or_404(db, source_id)
    for field, value in updates.items():
        setattr(source, field, value)
    db.commit()
    db.refresh(source)
    return source


def delete_source(db: Session, source_id: int) -> None:
    source = _source_or_404(db, source_id)
    course_id = source.course_id
    db.delete(source)
    db.flush()

    remaining = list(
        db.execute(select(Source).where(Source.course_id == course_id).order_by(Source.position)).scalars()
    )
    _renumber(db, remaining)
    db.commit()


def move_source(db: Session, source_id: int, direction: str) -> None:
    source = _source_or_404(db, source_id)
    ordered = list(
        db.execute(
            select(Source).where(Source.course_id == source.course_id).order_by(Source.position)
        ).scalars()
    )
    index = next(i for i, s in enumerate(ordered) if s.id == source_id)
    swap_with = index - 1 if direction == "up" else index + 1
    if 0 <= swap_with < len(ordered):
        ordered[index], ordered[swap_with] = ordered[swap_with], ordered[index]
        _renumber(db, ordered)
    db.commit()


# --- subject matter experts -----------------------------------------------------


def _sme_or_404(db: Session, sme_id: int) -> SubjectMatterExpert:
    sme = db.get(SubjectMatterExpert, sme_id)
    if sme is None:
        raise SMENotFoundError(f"Subject matter expert {sme_id} not found")
    return sme


def list_smes(db: Session) -> list[SubjectMatterExpert]:
    return list(db.execute(select(SubjectMatterExpert).order_by(SubjectMatterExpert.name)).scalars())


def get_sme(db: Session, sme_id: int) -> SubjectMatterExpert:
    return _sme_or_404(db, sme_id)


def create_sme(db: Session, **fields) -> SubjectMatterExpert:
    sme = SubjectMatterExpert(**fields)
    db.add(sme)
    db.commit()
    db.refresh(sme)
    return sme


def update_sme(db: Session, sme_id: int, updates: dict) -> SubjectMatterExpert:
    sme = _sme_or_404(db, sme_id)
    for field, value in updates.items():
        setattr(sme, field, value)
    db.commit()
    db.refresh(sme)
    return sme


def delete_sme(db: Session, sme_id: int) -> None:
    sme = _sme_or_404(db, sme_id)

    in_use = db.execute(
        select(func.count())
        .select_from(Course)
        .where((Course.developer_id == sme_id) | (Course.reviewer_id == sme_id))
    ).scalar_one()
    if in_use > 0:
        raise SMEInUseError(
            "This person is a developer or reviewer on a course and cannot be deleted"
        )

    db.delete(sme)
    db.commit()
