from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class CourseSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    title: str
    description: str
    has_thumbnail: bool
    lesson_count: int


class LessonInCourse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    title: str
    description: str
    duration_seconds: int | None
    has_thumbnail: bool
    position: int


class LearningObjectivePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    text: str
    position: int


class SubjectMatterExpertPublic(BaseModel):
    # 4.01's course documentation, not the full SME record - bio and
    # affiliation stay internal.
    model_config = ConfigDict(from_attributes=True)

    name: str
    credentials: str


class CourseDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    title: str
    description: str
    has_thumbnail: bool
    program_level: str
    field_of_study: str
    prerequisites: str | None
    advance_preparation: str | None
    learning_objectives: list[LearningObjectivePublic]
    lessons: list[LessonInCourse]
    reviewed_at: datetime | None
    developer: SubjectMatterExpertPublic | None
    reviewer: SubjectMatterExpertPublic | None
    # 7.02.6/7.02.7 credit, disclosed before enrolment - see current-feature.md,
    # "This is a pre-enrolment disclosure". Null until an admin has computed it.
    credit_award: Decimal | None
    # 9.02.2 item 3, disclosed alongside credit and last-reviewed date - see
    # current-feature.md, Part 2.
    expires_on: date | None
    # Feature 027's pre-enrollment disclosure - see current-feature.md's
    # frontend task 3. Live, not snapshotted; see app/services/courses.py.
    sponsor_registry_status: str
    # Feature 028: "How this course works" derives its numbers from these
    # rather than hardcoding them - see current-feature.md, frontend task 4.
    pass_ratio: Decimal
    assessment_question_count: int


class LessonSegmentDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    title: str
    description: str
    duration_seconds: int | None
    video_key: str | None
    has_thumbnail: bool
    position: int
    course_slug: str
    course_title: str
    previous_lesson_slug: str | None
    next_lesson_slug: str | None
    # Feature 028: sourced from the same gate CourseDetail's /watch-status
    # call and attempts_service.start_attempt already answer - see
    # app/services/courses.py::get_assessment_gate_status.
    assessment_unlocked: bool
    assessment_outstanding_lesson: str | None
