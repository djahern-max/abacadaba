from pydantic import BaseModel, ConfigDict


class FieldOfStudyOption(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    credential_tag: str | None = None


class FieldsOfStudyResponse(BaseModel):
    non_cpe: str
    technical: list[FieldOfStudyOption]
    non_technical: list[FieldOfStudyOption]


class ProgramLevelsResponse(BaseModel):
    levels: list[str]
