# Mirrors the CHECK constraint on courses.program_kind (see
# app/models/course.py). Two different facts, two different fields - see
# current-feature.md, "Two facts, two fields": this is an editorial decision
# made per course, not app/constants/registry_status.py's fact about the
# sponsor's relationship with NASBA.
PROGRAM_KIND_CPE = "cpe"
PROGRAM_KIND_GENERAL = "general"

PROGRAM_KIND_VALUES = [PROGRAM_KIND_CPE, PROGRAM_KIND_GENERAL]
