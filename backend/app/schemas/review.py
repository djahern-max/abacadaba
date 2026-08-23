from pydantic import BaseModel, ConfigDict


# is_correct never appears here, on purpose - the feature 015 leak test's
# sibling rule for review questions. Grading happens server-side on submit.
class ReviewChoicePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    position: int


class ReviewQuestionPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    prompt: str
    position: int
    choices: list[ReviewChoicePublic]


class ReviewQuestionsPublic(BaseModel):
    questions: list[ReviewQuestionPublic]


class ReviewAnswerRequest(BaseModel):
    choice_id: int


class ReviewAnswerResponse(BaseModel):
    # 5.01.2.2: the verdict is mandatory, the feedback text is optional.
    correct: bool
    feedback: str | None = None
