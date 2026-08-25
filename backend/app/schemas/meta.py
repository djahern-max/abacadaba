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


class SiteStatusResponse(BaseModel):
    # Feature 029, Part 6: derived from whether any published course is
    # offered as a CPE program - not a second, independently settable flag.
    # See app/services/courses.py::show_policy_footer.
    show_policy_footer: bool
