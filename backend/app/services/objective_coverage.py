"""Qualified-assessment objective coverage (6.01.2: "the assessment ... must
measure 75 percent or more of the learning objectives for the program").
Pure and read-only, alongside app/services/credit.py's compute() - the only
caller that turns this into a publish-blocking error is
admin_content.validate_for_publish.
"""

from dataclasses import dataclass
from decimal import Decimal

from app.models.course import Course
from app.models.learning_objective import LearningObjective
from app.models.question import QUESTION_KIND_ASSESSMENT

COVERAGE_THRESHOLD = Decimal("0.75")


@dataclass
class CoverageResult:
    total_objectives: int
    covered_count: int
    ratio: Decimal
    uncovered: list[LearningObjective]


def compute(course: Course) -> CoverageResult:
    # Intersected against the course's own objective ids rather than trusted
    # as-is: objective_id is a plain FK, not scoped to this course, so a
    # stray id from elsewhere would otherwise inflate coverage.
    objective_ids = {objective.id for objective in course.learning_objectives}
    tagged_ids = {
        question.objective_id
        for lesson in course.lessons
        for question in lesson.questions
        if question.kind == QUESTION_KIND_ASSESSMENT and question.objective_id is not None
    }
    covered_ids = objective_ids & tagged_ids

    total = len(course.learning_objectives)
    ratio = Decimal(len(covered_ids)) / Decimal(total) if total else Decimal(0)
    uncovered = [objective for objective in course.learning_objectives if objective.id not in covered_ids]

    return CoverageResult(
        total_objectives=total,
        covered_count=len(covered_ids),
        ratio=ratio,
        uncovered=uncovered,
    )
