# Mirrors the CHECK constraint on sponsor_profile.registry_status (see
# app/models/sponsor_profile.py). Kept as constants rather than a native
# Postgres enum for the same reason app/constants/program_levels.py is:
# editing a Python constant is far less friction than altering an enum.
REGISTRY_STATUS_NOT_REGISTERED = "not_registered"
REGISTRY_STATUS_REGISTERED = "registered"

REGISTRY_STATUS_VALUES = [REGISTRY_STATUS_NOT_REGISTERED, REGISTRY_STATUS_REGISTERED]
