# NASBA "Fields of Study That Qualify for Continuing Professional Education,"
# January 2024 (docs/2024-Fields-of-Study-Document.pdf). Values are stored
# verbatim as the course's field_of_study string.

NON_CPE = "Not CPE eligible"

TECHNICAL_FIELDS_OF_STUDY = [
    "Accounting",
    "Accounting (Governmental)",
    "Auditing",
    "Auditing (Governmental)",
    "Business Law",
    "Economics",
    "Finance",
    "Information Technology",
    "Management Services",
    "Regulatory Ethics",
    "Specialized Knowledge",
    "Statistics",
    "Taxes",
]

NON_TECHNICAL_FIELDS_OF_STUDY = [
    "Behavioral Ethics",
    "Business Management & Organization",
    "Communications and Marketing",
    "Computer Software & Applications",
    "Personal Development",
    "Personnel/Human Resources",
    "Production",
]

# abacadaba's content is deliberately non-financial, so this sentinel is the
# default: it keeps the column non-nullable and honest instead of blank.
ALL_FIELDS_OF_STUDY = [NON_CPE, *TECHNICAL_FIELDS_OF_STUDY, *NON_TECHNICAL_FIELDS_OF_STUDY]

DEFAULT_FIELD_OF_STUDY = NON_CPE
