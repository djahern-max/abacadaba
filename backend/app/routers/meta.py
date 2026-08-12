from fastapi import APIRouter

from app.constants.fields_of_study import NON_CPE, NON_TECHNICAL_FIELDS_OF_STUDY, TECHNICAL_FIELDS_OF_STUDY
from app.constants.program_levels import PROGRAM_LEVELS
from app.schemas.meta import FieldsOfStudyResponse, ProgramLevelsResponse

router = APIRouter()


@router.get("/meta/fields-of-study", response_model=FieldsOfStudyResponse)
def get_fields_of_study():
    return FieldsOfStudyResponse(
        non_cpe=NON_CPE,
        technical=TECHNICAL_FIELDS_OF_STUDY,
        non_technical=NON_TECHNICAL_FIELDS_OF_STUDY,
    )


@router.get("/meta/program-levels", response_model=ProgramLevelsResponse)
def get_program_levels():
    return ProgramLevelsResponse(levels=PROGRAM_LEVELS)
