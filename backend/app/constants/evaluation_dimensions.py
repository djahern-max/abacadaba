# 4.04.1's enumerated evaluation dimensions, in order. Served through
# GET /meta/evaluation-dimensions rather than duplicated in the frontend -
# the same reasoning behind app/constants/fields_of_study.py and feature
# 020's /meta/fields-of-study endpoint.
from dataclasses import dataclass


@dataclass(frozen=True)
class EvaluationDimension:
    key: str
    question: str
    # 4.03 defines "instructor" broadly enough that a self study program's
    # video narration could arguably qualify, but asking a participant to
    # rate an instructor they never met produces noise, not quality data.
    # Kept in the constant (not deleted) for when superCPE runs a group
    # program and the dimension applies for real - filtered at serve time
    # by dimensions_for_self_study(), never rendered or collected here.
    applies_to_self_study: bool = True


EVALUATION_DIMENSIONS = [
    EvaluationDimension("objectives_met", "Were the stated learning objectives met?"),
    EvaluationDimension(
        "prerequisites_appropriate",
        "Were the stated prerequisite requirements appropriate and sufficient?",
    ),
    EvaluationDimension(
        "materials_relevant",
        "Were the program materials, including the qualified assessment, relevant "
        "and did they contribute to achieving the learning objectives?",
    ),
    EvaluationDimension("time_allotted_appropriate", "Was the time allotted to the learning activity appropriate?"),
    EvaluationDimension("instructor_effective", "Were the instructors effective?", applies_to_self_study=False),
]

DIMENSION_KEYS = [dimension.key for dimension in EVALUATION_DIMENSIONS]


def dimensions_for_self_study() -> list[EvaluationDimension]:
    return [dimension for dimension in EVALUATION_DIMENSIONS if dimension.applies_to_self_study]
