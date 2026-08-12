from pydantic import BaseModel, ConfigDict


# Public twin of AdminChoice (app/schemas/admin.py). This one omits is_correct
# on purpose — never merge them into one class.
class ChoicePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    position: int


class QuestionPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    prompt: str
    position: int
    choices: list[ChoicePublic]


class QuizPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    course_slug: str
    course_title: str
    question_count: int
    questions: list[QuestionPublic]
