from pydantic import BaseModel, ConfigDict


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

    lesson_slug: str
    lesson_title: str
    question_count: int
    questions: list[QuestionPublic]


class AnswerRequest(BaseModel):
    question_id: int
    choice_id: int


class AnswerResponse(BaseModel):
    correct: bool
    correct_choice_id: int
