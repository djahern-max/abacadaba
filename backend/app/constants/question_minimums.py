"""Review and qualified-assessment question floors, transcribed from
docs/2026-Statement-on-Standards-for-CPE-Programs.pdf (5.01.2.1 for review
questions, 6.01.2 for the qualified assessment), keyed to one-fifth credit
increments.

Above one full credit, the Standards require the per-credit minimum plus the
chart's amount for the credit remaining after whole credits are removed:
"After the first full credit and the minimum of three review questions ...
additional review questions ... are required based on the chart above"
(5.01.2.1); similarly for 6.01.2's assessment chart. The
`whole * PER_CREDIT + CHART[remainder]` decomposition below is an
interpretation of that prose, not a quoted rule - but it reproduces both of
6.01.2's own worked examples (a 5-credit course needs 25 assessment
questions, a 5 1/2-credit course needs 29). See COMPLIANCE.md's Gap column
for 6.01.2.
"""

from decimal import Decimal

# 5.01.2.1: "At least three review questions or other content reinforcement
# tools with scored responses per CPE credit must be included."
REVIEW_PER_CREDIT = 3

# 5.01.2.1's chart, keyed by the credit remaining after whole credits are
# removed (0.0 covers an exact whole-credit remainder).
REVIEW_MINIMUMS = {
    Decimal("0.0"): 0,
    Decimal("0.2"): 0,
    Decimal("0.4"): 1,
    Decimal("0.5"): 2,
    Decimal("0.6"): 2,
    Decimal("0.8"): 3,
}

# 6.01.2: "At least 5 questions and scored responses per CPE credit must be
# included on the qualified assessment."
ASSESSMENT_PER_CREDIT = 5

# 6.01.2's chart, keyed the same way as REVIEW_MINIMUMS above.
ASSESSMENT_MINIMUMS = {
    Decimal("0.0"): 0,
    Decimal("0.2"): 2,
    Decimal("0.4"): 3,
    Decimal("0.5"): 4,
    Decimal("0.6"): 4,
    Decimal("0.8"): 5,
}

# 6.01.2: "Forced choice responses such as 'True or false' or 'yes or no'
# questions are not permissible on the qualified assessment." Two choices is
# the shape that makes a forced-choice response possible, so three is the
# floor. MIN_CHOICES_PER_QUESTION (app/services/admin_content.py, feature
# 010) stays as the global floor of two; this sits beside it, stricter, and
# only for assessment questions.
MIN_CHOICES_ASSESSMENT = 3


def _required(credit: Decimal, per_credit: int, chart: dict[Decimal, int]) -> int:
    whole, remainder = divmod(credit, 1)
    return int(whole) * per_credit + chart[remainder]


def required_review_questions(credit: Decimal) -> int:
    return _required(credit, REVIEW_PER_CREDIT, REVIEW_MINIMUMS)


def required_assessment_questions(credit: Decimal) -> int:
    return _required(credit, ASSESSMENT_PER_CREDIT, ASSESSMENT_MINIMUMS)
