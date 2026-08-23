from decimal import Decimal

# The 2026 Standards revision this formula was transcribed from - see
# docs/2026-Statement-on-Standards-for-CPE-Programs.pdf Section 7 Paragraph
# 7.02.6. Written into every computed course's credit_formula_version so a
# stored credit can be traced back to the rules that produced it; when NASBA
# revises the Standards, bump this and every course's credit becomes stale
# by definition (see the staleness comparison in app/services/credit.py).
CREDIT_FORMULA_VERSION = "2026-7.02.6"

# 7.02.6: one 50-minute period equals one full CPE credit.
MINUTES_PER_CREDIT = 50

# 7.02.6: the average adult reading speed the word term is divided by.
WORDS_PER_MINUTE = 180

# 7.02.6: the estimated average completion time per review, exercise, or
# qualified assessment question.
MINUTES_PER_QUESTION = Decimal("1.85")

# 7.01: self study programs may award one-fifth credit initially. Below
# that, no credit is awardable at all.
MIN_AWARDABLE = Decimal("0.2")
