-- Seed: ASC 606 construction intro, lesson 1 questions
-- Course slug: asc-606-construction-over-time-intro
--
-- Positions 1-3 are review questions (RQ1-RQ3 in the lesson package).
-- Positions 4-8 are qualified assessment questions (AQ1-AQ5).
-- Feature 023 splits these into two types; until then the convention is
-- position <= 3 means review. Keep that convention if you seed more courses,
-- because it makes the 023 migration a WHERE clause instead of a judgment call.
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
-- Pre-flight. Both should return zero rows / zero count before you proceed.
-- ---------------------------------------------------------------------------

-- Confirm exactly one lesson exists under the course:
SELECT c.slug AS course_slug, l.id AS lesson_id, l.position, l.title
FROM lessons l
JOIN courses c ON c.id = l.course_id
WHERE c.slug = 'asc-606-construction-over-time-intro';

-- Confirm the lesson has no questions yet (position unique constraint will
-- reject the insert otherwise, but better to know now):
SELECT count(*) AS existing_questions
FROM questions q
JOIN lessons l ON l.id = q.lesson_id
JOIN courses c ON c.id = l.course_id
WHERE c.slug = 'asc-606-construction-over-time-intro';

-- ---------------------------------------------------------------------------
-- Insert
-- ---------------------------------------------------------------------------

WITH target_lesson AS (
    SELECT l.id
    FROM lessons l
    JOIN courses c ON c.id = l.course_id
    WHERE c.slug = 'asc-606-construction-over-time-intro'
    ORDER BY l.position
    LIMIT 1
),
inserted_questions AS (
    INSERT INTO questions (lesson_id, prompt, position)
    SELECT target_lesson.id, v.prompt, v.position
    FROM target_lesson,
    (VALUES
        (1, $q$What was the primary objective of ASC 606 with respect to industry-specific revenue guidance?$q$),
        (2, $q$Under ASC 606-10-25-27, how many of the three criteria must a performance obligation meet in order to be satisfied over time?$q$),
        (3, $q$A contractor concludes that its performance obligation is satisfied over time. What does that conclusion establish about the amount of revenue to recognize in the current period?$q$),
        (4, $q$A contractor is building a specialized wastewater treatment facility on land owned by a municipality. The contract permits the municipality to terminate for convenience, in which case the contractor may recover costs incurred plus a reasonable profit margin on work performed to date. Which ASC 606-10-25-27 criterion most directly supports over-time recognition?$q$),
        (5, $q$Which statement best describes the status of the percentage-of-completion method under ASC 606?$q$),
        (6, $q$A contractor builds standard-plan single-family homes on its own land and markets them to buyers during construction. A buyer signs a purchase contract midway through construction of one home; the contractor could readily substitute a different home of the same plan. Which conclusion is most appropriate?$q$),
        (7, $q$Which of the following is an input method for measuring progress toward complete satisfaction of a performance obligation?$q$),
        (8, $q$Which of the following remains in ASC 605-35 following the adoption of ASC 606?$q$)
    ) AS v(position, prompt)
    RETURNING id, position
)
INSERT INTO choices (question_id, text, is_correct, position)
SELECT iq.id, v.text, v.is_correct, v.choice_position
FROM inserted_questions iq
JOIN (VALUES
    -- Q1 / RQ1
    (1, 1, $c$To replace industry-specific revenue models with a single framework applying to all entities.$c$, true),
    (1, 2, $c$To require all construction contractors to use the completed contract method.$c$, false),
    (1, 3, $c$To preserve ASC 605-35 as the governing model for construction contractors.$c$, false),
    (1, 4, $c$To eliminate the need for estimates in long-term contract accounting.$c$, false),

    -- Q2 / RQ2
    (2, 1, $c$All three.$c$, false),
    (2, 2, $c$Any one of the three.$c$, true),
    (2, 3, $c$At least two of the three.$c$, false),
    (2, 4, $c$None - over-time recognition is an accounting policy election.$c$, false),

    -- Q3 / RQ3
    (3, 1, $c$Revenue equals costs incurred to date.$c$, false),
    (3, 2, $c$Revenue is recognized ratably over the contract term.$c$, false),
    (3, 3, $c$Nothing - measuring progress toward satisfaction is a separate determination.$c$, true),
    (3, 4, $c$Revenue equals amounts billed to the customer during the period.$c$, false),

    -- Q4 / AQ1
    (4, 1, $c$The customer simultaneously receives and consumes the benefits of the contractor's performance as it performs.$c$, false),
    (4, 2, $c$The contractor's performance creates an asset with no alternative use and the contractor has an enforceable right to payment for performance completed to date.$c$, true),
    (4, 3, $c$The contract price exceeds the contractor's estimated total cost.$c$, false),
    (4, 4, $c$The contract term extends beyond one annual reporting period.$c$, false),

    -- Q5 / AQ2
    (5, 1, $c$It remains available as an election for contractors who can make dependable estimates.$c$, false),
    (5, 2, $c$It is prohibited, and contractors must recognize revenue at a point in time.$c$, false),
    (5, 3, $c$It is no longer a method; over-time recognition is a conclusion from criteria, and progress is then measured by a selected input or output method.$c$, true),
    (5, 4, $c$It applies only to contracts with a duration exceeding twelve months.$c$, false),

    -- Q6 / AQ3
    (6, 1, $c$Over-time recognition applies, because construction contracts always qualify.$c$, false),
    (6, 2, $c$The "no alternative use" condition is likely not met, so this criterion does not support over-time recognition.$c$, true),
    (6, 3, $c$Over-time recognition applies, because the contract term exceeds the reporting period.$c$, false),
    (6, 4, $c$The contractor should apply the completed contract method under ASC 605-35.$c$, false),

    -- Q7 / AQ4
    (7, 1, $c$Units delivered.$c$, false),
    (7, 2, $c$Milestones achieved.$c$, false),
    (7, 3, $c$Costs incurred relative to total expected costs.$c$, true),
    (7, 4, $c$Surveys of performance completed to date.$c$, false),

    -- Q8 / AQ5
    (8, 1, $c$The election between the percentage-of-completion and completed contract methods.$c$, false),
    (8, 2, $c$Guidance on provisions for losses on contracts.$c$, true),
    (8, 3, $c$The requirement to present costs in excess of billings as a separate asset caption.$c$, false),
    (8, 4, $c$The definition of a construction-type contract for revenue recognition timing.$c$, false)
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

-- Expect 8 rows, each with choice_count = 4 and correct_count = 1:
SELECT q.position,
       count(ch.id)                              AS choice_count,
       count(ch.id) FILTER (WHERE ch.is_correct) AS correct_count,
       left(q.prompt, 60)                        AS prompt_start
FROM questions q
JOIN lessons l  ON l.id = q.lesson_id
JOIN courses c  ON c.id = l.course_id
LEFT JOIN choices ch ON ch.question_id = q.id
WHERE c.slug = 'asc-606-construction-over-time-intro'
GROUP BY q.id, q.position
ORDER BY q.position;

-- Expect reviewed_at to be NULL, or earlier than content_updated_at:
SELECT slug, reviewed_at, content_updated_at,
       (reviewed_at IS NOT NULL AND reviewed_at < content_updated_at)
           AS needs_re_review
FROM courses
WHERE slug = 'asc-606-construction-over-time-intro';

-- COMMIT;
-- ROLLBACK;

-- ---------------------------------------------------------------------------
-- To undo (choices cascade from questions):
--
-- DELETE FROM questions q
-- USING lessons l, courses c
-- WHERE q.lesson_id = l.id
--   AND l.course_id = c.id
--   AND c.slug = 'asc-606-construction-over-time-intro';
-- ---------------------------------------------------------------------------
