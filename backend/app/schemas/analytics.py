from pydantic import BaseModel, ConfigDict


class LessonStats(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    attempts_started: int
    attempts_completed: int
    completion_rate: float
    pass_rate: float | None
    mean_score: float | None


class QuestionStat(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    question_id: int
    prompt: str
    position: int
    answered: int
    pct_correct: float | None


class ChoiceStat(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    choice_id: int
    text: str
    position: int
    is_correct: bool
    picked_count: int


class QuestionChoiceDistribution(BaseModel):
    question_id: int
    choices: list[ChoiceStat]


class DropoffPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    position: int
    attempts_reached: int


class LessonAnalytics(BaseModel):
    lesson_stats: LessonStats
    question_stats: list[QuestionStat]
    choice_distribution: list[QuestionChoiceDistribution]
    dropoff: list[DropoffPoint]
