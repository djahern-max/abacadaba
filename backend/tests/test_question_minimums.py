from decimal import Decimal

from app.constants.question_minimums import required_assessment_questions, required_review_questions


def test_review_floor_matches_5_01_2_1_chart():
    assert required_review_questions(Decimal("0.2")) == 0
    assert required_review_questions(Decimal("0.4")) == 1
    assert required_review_questions(Decimal("0.5")) == 2
    assert required_review_questions(Decimal("0.6")) == 2
    assert required_review_questions(Decimal("0.8")) == 3
    assert required_review_questions(Decimal("1.0")) == 3


def test_assessment_floor_matches_6_01_2_chart():
    assert required_assessment_questions(Decimal("0.2")) == 2
    assert required_assessment_questions(Decimal("0.4")) == 3
    assert required_assessment_questions(Decimal("0.5")) == 4
    assert required_assessment_questions(Decimal("0.6")) == 4
    assert required_assessment_questions(Decimal("0.8")) == 5
    assert required_assessment_questions(Decimal("1.0")) == 5


# 6.01.2's own worked examples: "the qualified assessment for a 5-credit
# course must include at least 25 questions ... a 5 1/2 credit course must
# include at least 29 questions."
def test_five_credit_worked_example_requires_25_assessment_questions():
    assert required_assessment_questions(Decimal("5.0")) == 25


def test_five_and_a_half_credit_worked_example_requires_29_assessment_questions():
    assert required_assessment_questions(Decimal("5.5")) == 29


def test_review_floor_above_one_credit_adds_per_credit_amount():
    # whole * REVIEW_PER_CREDIT (3) + chart[remainder]
    assert required_review_questions(Decimal("2.0")) == 6
    assert required_review_questions(Decimal("2.5")) == 8
