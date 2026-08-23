-- Seed: ASC 606 construction, lesson 2 questions
-- Course slug: asc-606-construction-over-time-intro
-- Lesson position: 2 ("Measuring Progress: The Uninstalled Materials Adjustment")
--
-- DRAFT. These questions have not been reviewed. The correct answers depend on
-- ASC 606-10-55-21(b) and on the arithmetic in the lesson-02 narration, neither
-- of which has passed SME review yet. Do not COMMIT this against a database
-- backing a published course.
--
-- Positions 1-3 are review questions (RQ1-RQ3).
-- Positions 4-8 are qualified assessment questions (AQ1-AQ5).
-- Same convention as lesson 1: position <= 3 means review, so feature 023's
-- split stays a WHERE clause rather than a judgment call.
--
-- CHECK THE COURSE SLUG BEFORE RUNNING. Lesson 1's course is
-- `asc-606-construction-over-time-intro`, whose description covers over-time
-- recognition and names two learning objectives. This lesson serves a third
-- objective (calculate revenue under a cost-to-cost input method including the
-- uninstalled materials adjustment) that is not in that course's stated
-- objectives. Two ways to resolve it, and the choice is yours:
--
--   (a) Lesson 2 belongs to the same course, and the course's description and
--       learning objectives must be updated to cover it. Under 8.01.1 the
--       description is a disclosure, and a course that teaches something its
--       description does not name is a real defect, not a tidiness issue.
--   (b) Lesson 2 belongs to a separate course. Change the slug below.
--
-- Resolve that before running, not after.
--
-- This script bypasses app/services/admin_content.py and therefore bypasses:
--   1. touch_content_updated_at        -> handled explicitly at the end
--   2. the exactly-one-correct-choice  -> handled by the verification query
--      service validation                 at the end; check it before COMMIT
--
-- Run inside a transaction. Do not COMMIT until the verification output is
-- what you expect.

\set ON_ERROR_STOP on

BEGIN;

-- ---------------------------------------------------------------------------
-- Pre-flight.
-- ---------------------------------------------------------------------------

-- Confirm the lesson exists at position 2. If this returns zero rows, create
-- the lesson in the admin editor first — the INSERT below will silently insert
-- nothing rather than error, because it joins against an empty CTE.
SELECT c.slug AS course_slug, l.id AS lesson_id, l.position, l.title
FROM lessons l
JOIN courses c ON c.id = l.course_id
WHERE c.slug = 'asc-606-construction-over-time-intro'
ORDER BY l.position;

-- Confirm lesson 2 has no questions yet:
SELECT count(*) AS existing_questions
FROM questions q
JOIN lessons l ON l.id = q.lesson_id
JOIN courses c ON c.id = l.course_id
WHERE c.slug = 'asc-606-construction-over-time-intro'
  AND l.position = 2;

-- ---------------------------------------------------------------------------
-- Insert
-- ---------------------------------------------------------------------------

WITH target_lesson AS (
    SELECT l.id
    FROM lessons l
    JOIN courses c ON c.id = l.course_id
    WHERE c.slug = 'asc-606-construction-over-time-intro'
      AND l.position = 2
),
inserted_questions AS (
    INSERT INTO questions (lesson_id, prompt, position)
    SELECT target_lesson.id, v.prompt, v.position
    FROM target_lesson,
    (VALUES
        (1, $q$Under ASC 606-10-25-31, what is the objective when measuring progress toward complete satisfaction of a performance obligation?$q$),
        (2, $q$A cost incurred by a contractor is not proportionate to the contractor's progress in satisfying its performance obligation. Which two steps does ASC 606-10-55-21 require?$q$),
        (3, $q$A contractor excludes the cost of uninstalled materials from a cost-to-cost measure of progress. Where must that exclusion be made?$q$),
        (4, $q$A contractor has a fixed-price contract with a transaction price of $10,000,000 and estimated total costs of $8,000,000. Costs incurred to date are $3,200,000, which includes a $2,000,000 standby generator delivered to the site but not yet installed. The generator meets all four conditions in ASC 606-10-55-21(b). What is the contractor's measure of progress?$q$),
        (5, $q$Using the same facts, what total revenue should the contractor recognize to date?$q$),
        (6, $q$What is the effect of the uninstalled materials adjustment on the contractor's gross profit over the full life of the contract?$q$),
        (7, $q$A contractor designs and fabricates a custom pressure vessel in its own shop for a refinery project. The vessel is delivered to the site and the customer obtains control of it, but it has not been installed. Its cost is significant relative to total expected contract costs, and it is not distinct from the rest of the contract. Which condition for zero-margin treatment under ASC 606-10-55-21(b) is NOT met?$q$),
        (8, $q$A contractor removes the $2,000,000 cost of an uninstalled generator from costs incurred to date but leaves it in estimated total costs. Costs incurred to date before the adjustment are $3,200,000 and estimated total costs are $8,000,000. What measure of progress does this produce, and how does it compare with the correct result?$q$)
    ) AS v(position, prompt)
    RETURNING id, position
)
INSERT INTO choices (question_id, text, is_correct, position)
SELECT iq.id, v.text, v.is_correct, v.choice_position
FROM inserted_questions iq
JOIN (VALUES
    -- Q1 / RQ1
    (1, 1, $c$To depict the transfer of control of goods or services to the customer.$c$, true),
    (1, 2, $c$To match revenue with the costs the contractor incurred during the period.$c$, false),
    (1, 3, $c$To allocate the transaction price evenly across the contract term.$c$, false),
    (1, 4, $c$To ensure the contractor recovers its costs before recognizing any profit.$c$, false),

    -- Q2 / RQ2
    (2, 1, $c$Exclude the cost from the measure of progress, and recognize revenue for that item in an amount equal to its cost.$c$, true),
    (2, 2, $c$Exclude the cost from the measure of progress, and defer all revenue on that item until it is installed.$c$, false),
    (2, 3, $c$Include the cost in the measure of progress, and disclose the disproportionate effect in the notes.$c$, false),
    (2, 4, $c$Exclude the cost from costs incurred to date, and recognize the normal contract margin on it.$c$, false),

    -- Q3 / RQ3
    (3, 1, $c$From costs incurred to date only.$c$, false),
    (3, 2, $c$From estimated total costs only.$c$, false),
    (3, 3, $c$From both costs incurred to date and estimated total costs.$c$, true),
    (3, 4, $c$From neither; the adjustment is made only to the transaction price.$c$, false),

    -- Q4 / AQ1
    (4, 1, $c$40%$c$, false),
    (4, 2, $c$25%$c$, false),
    (4, 3, $c$20%$c$, true),
    (4, 4, $c$15%$c$, false),

    -- Q5 / AQ2
    (5, 1, $c$$4,000,000$c$, false),
    (5, 2, $c$$3,600,000$c$, true),
    (5, 3, $c$$2,000,000$c$, false),
    (5, 4, $c$$1,600,000$c$, false),

    -- Q6 / AQ3
    (6, 1, $c$Total gross profit is unchanged; the adjustment changes the periods in which profit is recognized.$c$, true),
    (6, 2, $c$Total gross profit is reduced by the cost of the uninstalled materials.$c$, false),
    (6, 3, $c$Total gross profit is increased, because the materials are recognized at cost.$c$, false),
    (6, 4, $c$No gross profit may be recognized on the contract until the materials are installed.$c$, false),

    -- Q7 / AQ4
    (7, 1, $c$The contractor procures the good and is not significantly involved in designing or manufacturing it.$c$, true),
    (7, 2, $c$The good is not distinct from the rest of the contract.$c$, false),
    (7, 3, $c$The customer obtains control of the good significantly before receiving the services related to it.$c$, false),
    (7, 4, $c$The cost of the good is significant relative to total expected costs.$c$, false),

    -- Q8 / AQ5
    (8, 1, $c$15%, which understates progress relative to the correct 20%.$c$, true),
    (8, 2, $c$15%, which overstates progress relative to the correct 12%.$c$, false),
    (8, 3, $c$40%, which is the same result as making no adjustment at all.$c$, false),
    (8, 4, $c$20%, which is the correct result; the second exclusion is optional.$c$, false)
) AS v(question_position, choice_position, text, is_correct)
  ON v.question_position = iq.position;

-- ---------------------------------------------------------------------------
-- The compliance step. Do not remove this.
--
-- Every participant-visible write in the app goes through
-- touch_content_updated_at so that a course edited after its review cannot
-- re-publish until it is reviewed again. Raw SQL skips that. Without this
-- UPDATE, eight questions no reviewer has seen can publish under a stale
-- reviewed_at.
-- ---------------------------------------------------------------------------

UPDATE courses
SET content_updated_at = now(),
    updated_at = now()
WHERE slug = 'asc-606-construction-over-time-intro';

-- ---------------------------------------------------------------------------
-- Verification. Read this output before COMMIT.
-- ---------------------------------------------------------------------------

-- Expect 8 rows for lesson 2, each with choice_count = 4 and correct_count = 1.
-- Lesson 1's 8 rows should also appear, unchanged.
SELECT l.position                                AS lesson_position,
       q.position                                AS question_position,
       count(ch.id)                              AS choice_count,
       count(ch.id) FILTER (WHERE ch.is_correct) AS correct_count,
       left(q.prompt, 60)                        AS prompt_start
FROM questions q
JOIN lessons l  ON l.id = q.lesson_id
JOIN courses c  ON c.id = l.course_id
LEFT JOIN choices ch ON ch.question_id = q.id
WHERE c.slug = 'asc-606-construction-over-time-intro'
GROUP BY l.position, q.id, q.position
ORDER BY l.position, q.position;

-- Confirm the dollar-quoted prompts and choices survived intact. The fact
-- patterns contain dollar signs, which is exactly what $q$ / $c$ quoting is
-- there to handle — but check rather than assume. Expect no truncation and no
-- stray $ artifacts:
SELECT q.position, ch.position AS choice_position, ch.text
FROM questions q
JOIN lessons l ON l.id = q.lesson_id
JOIN courses c ON c.id = l.course_id
JOIN choices ch ON ch.question_id = q.id
WHERE c.slug = 'asc-606-construction-over-time-intro'
  AND l.position = 2
  AND q.position = 5
ORDER BY ch.position;

-- Expect reviewed_at to be NULL, or earlier than content_updated_at:
SELECT slug, reviewed_at, content_updated_at,
       (reviewed_at IS NOT NULL AND reviewed_at < content_updated_at)
           AS needs_re_review
FROM courses
WHERE slug = 'asc-606-construction-over-time-intro';

-- COMMIT;
-- ROLLBACK;

-- ---------------------------------------------------------------------------
-- To undo lesson 2's questions only (choices cascade from questions):
--
-- DELETE FROM questions q
-- USING lessons l, courses c
-- WHERE q.lesson_id = l.id
--   AND l.course_id = c.id
--   AND c.slug = 'asc-606-construction-over-time-intro'
--   AND l.position = 2;
-- ---------------------------------------------------------------------------
