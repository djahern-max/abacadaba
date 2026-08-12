from pydantic import BaseModel


class FieldsOfStudyResponse(BaseModel):
    non_cpe: str
    technical: list[str]
    non_technical: list[str]


class ProgramLevelsResponse(BaseModel):
    levels: list[str]
