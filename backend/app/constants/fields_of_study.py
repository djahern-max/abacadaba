# NASBA "Fields of Study That Qualify for Continuing Professional Education,"
# January 2024 (docs/2024-Fields-of-Study-Document.pdf). Names are stored
# verbatim as the course's field_of_study string.
from dataclasses import dataclass

NON_CPE = "Not CPE eligible"

# Standard 4.02: at least one licensed CPA must participate in developing an
# accounting/auditing program; a CPA, tax attorney, or enrolled agent for a
# taxes program. The tag lives on the field itself so a field name is written
# exactly once - a second list keyed by field name would drift from this one.
CPA_REQUIRED = "cpa"
TAX_CREDENTIAL_REQUIRED = "tax"


@dataclass(frozen=True)
class FieldOfStudy:
    name: str
    credential_tag: str | None = None


TECHNICAL_FIELDS_OF_STUDY = [
    FieldOfStudy("Accounting", CPA_REQUIRED),
    FieldOfStudy("Accounting (Governmental)", CPA_REQUIRED),
    FieldOfStudy("Auditing", CPA_REQUIRED),
    FieldOfStudy("Auditing (Governmental)", CPA_REQUIRED),
    FieldOfStudy("Business Law"),
    FieldOfStudy("Economics"),
    FieldOfStudy("Finance"),
    FieldOfStudy("Information Technology"),
    FieldOfStudy("Management Services"),
    FieldOfStudy("Regulatory Ethics"),
    FieldOfStudy("Specialized Knowledge"),
    FieldOfStudy("Statistics"),
    FieldOfStudy("Taxes", TAX_CREDENTIAL_REQUIRED),
]

NON_TECHNICAL_FIELDS_OF_STUDY = [
    FieldOfStudy("Behavioral Ethics"),
    FieldOfStudy("Business Management & Organization"),
    FieldOfStudy("Communications and Marketing"),
    FieldOfStudy("Computer Software & Applications"),
    FieldOfStudy("Personal Development"),
    FieldOfStudy("Personnel/Human Resources"),
    FieldOfStudy("Production"),
]

# abacadaba's content is deliberately non-financial, so this sentinel is the
# default: it keeps the column non-nullable and honest instead of blank.
ALL_FIELDS_OF_STUDY = [NON_CPE, *(f.name for f in TECHNICAL_FIELDS_OF_STUDY), *(f.name for f in NON_TECHNICAL_FIELDS_OF_STUDY)]

DEFAULT_FIELD_OF_STUDY = NON_CPE

_CREDENTIAL_TAGS_BY_NAME = {
    field.name: field.credential_tag for field in (*TECHNICAL_FIELDS_OF_STUDY, *NON_TECHNICAL_FIELDS_OF_STUDY)
}


def credential_tag_for(field_of_study: str) -> str | None:
    return _CREDENTIAL_TAGS_BY_NAME.get(field_of_study)
