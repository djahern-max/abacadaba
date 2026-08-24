# 8.01.1: "The CPE program sponsor's registration and attendance policies
# and procedures must be formalized, published, and made available to
# participants and include refund and cancellation policies as well as
# complaint resolution policies." Records retention is 9.02. See
# current-feature.md, feature 026.
#
# Seeded verbatim by the migration that creates the policies table, and
# compared against verbatim by app/services/policies.py::is_placeholder - do
# not edit this string without updating both.
PLACEHOLDER_BODY = "This policy has not been written yet."

# (slug, title) - the four documents 8.01.1 and 9.02 require a sponsor to
# formalize and publish. Every course's publish gate refuses to proceed
# while any of these still carries PLACEHOLDER_BODY - see validate_for_publish
# in app/services/admin_content.py.
SEEDED_POLICIES = [
    ("refund-and-cancellation", "Refund and Cancellation Policy"),
    ("complaint-resolution", "Complaint Resolution Policy"),
    ("records-retention", "Records Retention Policy"),
    ("program-cancellation", "Program Cancellation Policy"),
]
