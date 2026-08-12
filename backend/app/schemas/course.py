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
