-- Seed: "Where Does It Actually Go?" (hazardous waste), all 5 lessons' questions
-- Course slug: where-does-it-actually-go
--
-- Position 1 in every lesson is the review question. Positions 2+ are
-- qualified assessment questions. This is a DIFFERENT boundary than the ASC
-- 606 seed scripts (position <= 3 means review there) -- see current-feature_23a.md's
-- note on this course's positional boundary. Do not assume position <= 3 here.
--
-- 5 review questions total, 10 assessment questions total, distributed:
--   Lesson 1 (obj 1): 1 review + 3 assessment  -> 4 questions
--   Lesson 2 (obj 2): 1 review + 2 assessment  -> 3 questions
--   Lesson 3 (obj 3): 1 review + 2 assessment  -> 3 questions
--   Lesson 4 (obj 4): 1 review + 2 assessment  -> 3 questions
--   Lesson 5 (obj 5): 1 review + 1 assessment  -> 2 questions
-- 100% of the course's 5 objectives are covered by assessment questions
-- (>= the 75% floor in 6.01.2). Review questions are left untagged
-- (objective_id NULL) -- coverage is an assessment-only rule.
--
-- PREREQUISITE: the course, its 5 learning objectives, and its 5 lesson stubs
-- must already exist (see hazardous_waste_course_setup.md), matching these
-- exact slugs:
--   where-does-it-actually-go
--     -> what-makes-a-waste-hazardous              (lesson position 1)
--     -> who-makes-it-and-how-much                 (lesson position 2)
--     -> cradle-to-grave                           (lesson position 3)
--     -> love-canal-and-the-birth-of-superfund     (lesson position 4)
--     -> not-making-it-in-the-first-place          (lesson position 5)
-- and 5 learning_objectives at positions 1-5 in that same order.
--
-- This script bypasses app/services/admin_content.py and therefore bypasses:
--   1. touch_content_updated_at        -> run manually after COMMIT if your
--                                          review/publish flow checks it
--   2. the exactly-one-correct-choice  -> checked by the verification query
--      service validation                 below; confirm before COMMIT
--
-- Run inside a transaction. Do not COMMIT until the verification output at
-- the bottom is what you expect.

\set ON_ERROR_STOP on

BEGIN;

-- ---------------------------------------------------------------------------
-- Pre-flight. All five lessons and objectives should be present; question
-- count per lesson should be zero before you proceed.
-- ---------------------------------------------------------------------------

SELECT l.position, l.slug, l.title
FROM lessons l
JOIN courses c ON c.id = l.course_id
WHERE c.slug = 'where-does-it-actually-go'
ORDER BY l.position;

SELECT o.position, o.text
FROM learning_objectives o
JOIN courses c ON c.id = o.course_id
WHERE c.slug = 'where-does-it-actually-go'
ORDER BY o.position;

SELECT l.slug, count(q.id) AS existing_questions
FROM lessons l
JOIN courses c ON c.id = l.course_id
LEFT JOIN questions q ON q.lesson_id = l.id
WHERE c.slug = 'where-does-it-actually-go'
GROUP BY l.slug
ORDER BY l.slug;

-- Hard guard. The five INSERTs below are cross joins against target_lesson and
-- target_objective. If either CTE returns zero rows -- a typo'd slug, a lesson
-- stub that was never created, an objective at the wrong position -- the INSERT
-- silently writes zero rows and the script still exits 0. The eyeball check at
-- the bottom is the only thing that would catch it, and "11" reads a lot like
-- "15" at the end of a long day. Fail loudly here instead.
DO $do$
DECLARE
    course_count      int;
    lesson_count      int;
    objective_count   int;
    existing_count    int;
    missing           text;
BEGIN
    SELECT count(*) INTO course_count
    FROM courses WHERE slug = 'where-does-it-actually-go';
    IF course_count <> 1 THEN
        RAISE EXCEPTION 'pre-flight: expected exactly 1 course with slug '
            'where-does-it-actually-go, found %', course_count;
    END IF;

    -- Every slug this script looks up must resolve, by name, not just by count.
    SELECT string_agg(want.slug, ', ' ORDER BY want.slug) INTO missing
    FROM (VALUES
        ('what-makes-a-waste-hazardous'),
        ('who-makes-it-and-how-much'),
        ('cradle-to-grave'),
        ('love-canal-and-the-birth-of-superfund'),
        ('not-making-it-in-the-first-place')
    ) AS want(slug)
    WHERE NOT EXISTS (
        SELECT 1 FROM lessons l
        JOIN courses c ON c.id = l.course_id
        WHERE c.slug = 'where-does-it-actually-go' AND l.slug = want.slug
    );
    IF missing IS NOT NULL THEN
        RAISE EXCEPTION 'pre-flight: lesson slug(s) not found: %. '
            'Check the admin editor against hazardous_waste_course_setup.md.', missing;
    END IF;

    SELECT count(*) INTO lesson_count
    FROM lessons l JOIN courses c ON c.id = l.course_id
    WHERE c.slug = 'where-does-it-actually-go';
    IF lesson_count <> 5 THEN
        RAISE EXCEPTION 'pre-flight: expected 5 lessons, found % (an extra stub '
            'will not break the inserts, but it will break the counts below)', lesson_count;
    END IF;

    SELECT count(*) INTO objective_count
    FROM learning_objectives o JOIN courses c ON c.id = o.course_id
    WHERE c.slug = 'where-does-it-actually-go' AND o.position BETWEEN 1 AND 5;
    IF objective_count <> 5 THEN
        RAISE EXCEPTION 'pre-flight: expected 5 learning objectives at positions '
            '1-5, found %', objective_count;
    END IF;

    SELECT count(*) INTO existing_count
    FROM questions q
    JOIN lessons l ON l.id = q.lesson_id
    JOIN courses c ON c.id = l.course_id
    WHERE c.slug = 'where-does-it-actually-go';
    IF existing_count <> 0 THEN
        RAISE EXCEPTION 'pre-flight: course already has % question(s). This script '
            'is not idempotent -- it appends. ROLLBACK and clear them first.', existing_count;
    END IF;
END
$do$;

-- ---------------------------------------------------------------------------
-- Lesson 1 -- What Makes a Waste "Hazardous"?  (objective 1)
-- ---------------------------------------------------------------------------

WITH target_lesson AS (
    SELECT l.id FROM lessons l JOIN courses c ON c.id = l.course_id
    WHERE c.slug = 'where-does-it-actually-go' AND l.slug = 'what-makes-a-waste-hazardous'
),
target_objective AS (
    SELECT o.id FROM learning_objectives o JOIN courses c ON c.id = o.course_id
    WHERE c.slug = 'where-does-it-actually-go' AND o.position = 1
),
inserted_questions AS (
    INSERT INTO questions (lesson_id, prompt, kind, feedback, objective_id, position)
    SELECT target_lesson.id, v.prompt, v.kind, v.feedback,
           CASE WHEN v.kind = 'assessment' THEN target_objective.id ELSE NULL END,
           v.position
    FROM target_lesson, target_objective,
    (VALUES
        (1, $q$A metal finishing shop generates a rinse water with a pH of 1.4. It contains no listed chemicals. Is it hazardous waste?$q$,
            'review',
            $q$A waste is hazardous if it's listed or if it exhibits any characteristic. A pH of 1.4 falls below the corrosivity threshold of 2.0, so the rinse water is a characteristic hazardous waste on its own. It doesn't need to appear on a list, and it doesn't need to fail any additional test.$q$),
        (2, $q$A waste liquid has a flash point of 118°F. Under RCRA it is:$q$,
            'assessment',
            $q$The ignitability threshold for liquids is a flash point below 140°F (60°C). At 118°F the waste falls under that limit and is a characteristic hazardous waste. Listing is a separate, independent route to the same result — a waste needs only one.$q$),
        (3, $q$What does the Toxicity Characteristic Leaching Procedure simulate?$q$,
            'assessment',
            $q$The TCLP recreates the acidic, wet conditions of a landfill to determine whether regulated contaminants would leach out of the waste and reach groundwater. This is why a waste can be stable, non-flammable, and pH-neutral, yet still be hazardous by the toxicity characteristic.$q$),
        (4, $q$Why can't a generator dilute a listed waste to escape regulation?$q$,
            'assessment',
            $q$The two doors into Subtitle C work differently. Characteristic wastes are defined by how the waste behaves, so treatment can in principle change that. Listed wastes are hazardous by identity, and remain so through dilution — which is precisely why the listing system exists alongside the characteristics.$q$)
    ) AS v(position, prompt, kind, feedback)
    RETURNING id, position
)
INSERT INTO choices (question_id, text, is_correct, position)
SELECT iq.id, c.text, c.is_correct, c.position
FROM inserted_questions iq
JOIN (VALUES
    (1, 1, $q$No — it isn't on any EPA list$q$, false),
    (1, 2, $q$Yes — it exhibits the corrosivity characteristic$q$, true),
    (1, 3, $q$No — pH is not a regulated property$q$, false),
    (1, 4, $q$Yes — but only if it also fails the TCLP test$q$, false),

    (2, 1, $q$Non-hazardous, because the threshold is 100°F$q$, false),
    (2, 2, $q$Hazardous — it exhibits the ignitability characteristic$q$, true),
    (2, 3, $q$Hazardous only if it also appears on the F-list$q$, false),
    (2, 4, $q$Regulated under Subtitle D as municipal solid waste$q$, false),

    (3, 1, $q$Combustion of waste in an incinerator$q$, false),
    (3, 2, $q$Absorption of waste through human skin$q$, false),
    (3, 3, $q$Conditions inside a landfill, where water percolates through buried waste$q$, true),
    (3, 4, $q$Long-term atmospheric weathering of exposed waste$q$, false),

    (4, 1, $q$Dilution always raises the pH above 12.5$q$, false),
    (4, 2, $q$A listed waste remains hazardous regardless of concentration$q$, true),
    (4, 3, $q$Dilution is only prohibited for large quantity generators$q$, false),
    (4, 4, $q$Diluted wastes automatically become P-listed$q$, false)
) AS c(q_position, position, text, is_correct)
ON c.q_position = iq.position;

-- ---------------------------------------------------------------------------
-- Lesson 2 -- Who Makes It, and How Much  (objective 2)
-- ---------------------------------------------------------------------------

WITH target_lesson AS (
    SELECT l.id FROM lessons l JOIN courses c ON c.id = l.course_id
    WHERE c.slug = 'where-does-it-actually-go' AND l.slug = 'who-makes-it-and-how-much'
),
target_objective AS (
    SELECT o.id FROM learning_objectives o JOIN courses c ON c.id = o.course_id
    WHERE c.slug = 'where-does-it-actually-go' AND o.position = 2
),
inserted_questions AS (
    INSERT INTO questions (lesson_id, prompt, kind, feedback, objective_id, position)
    SELECT target_lesson.id, v.prompt, v.kind, v.feedback,
           CASE WHEN v.kind = 'assessment' THEN target_objective.id ELSE NULL END,
           v.position
    FROM target_lesson, target_objective,
    (VALUES
        (1, $q$A university chemistry building generates 400 kg of hazardous waste in March, including 3 kg of an acutely hazardous P-listed compound. Which generator category applies?$q$,
            'review',
            $q$The 400 kg total would ordinarily place the building in the small quantity generator tier. But acutely hazardous waste carries its own much lower threshold — more than 1 kg in a month pushes a generator into the large quantity category regardless of total volume. There is no educational exemption; the household exclusion applies to homes, not to laboratories.$q$),
        (2, $q$A machine shop generates 60 kg of hazardous waste per month, none of it acutely hazardous. Its generator category is:$q$,
            'assessment',
            $q$The very small quantity generator tier covers generators producing 100 kg or less per month. At 60 kg the shop falls in this tier, which carries the lightest regulatory obligations. It is a reduced set of requirements, not an exemption.$q$),
        (3, $q$Why did Congress exempt household hazardous waste from RCRA Subtitle C?$q$,
            'assessment',
            $q$The exemption is a practical judgment, not a scientific one. The same paint thinner is chemically identical whether it sits in a factory or a garage, and household volumes do cause real harm in aggregate. Inspecting a hundred and thirty million homes simply isn't achievable, so Congress excluded the household stream.$q$)
    ) AS v(position, prompt, kind, feedback)
    RETURNING id, position
)
INSERT INTO choices (question_id, text, is_correct, position)
SELECT iq.id, c.text, c.is_correct, c.position
FROM inserted_questions iq
JOIN (VALUES
    (1, 1, $q$Very small quantity generator$q$, false),
    (1, 2, $q$Small quantity generator, based on the 400 kg total$q$, false),
    (1, 3, $q$Large quantity generator, triggered by the acute waste$q$, true),
    (1, 4, $q$The university is exempt as an educational institution$q$, false),

    (2, 1, $q$Very small quantity generator$q$, true),
    (2, 2, $q$Small quantity generator$q$, false),
    (2, 3, $q$Large quantity generator$q$, false),
    (2, 4, $q$Exempt from RCRA entirely$q$, false),

    (3, 1, $q$Household chemicals are chemically different from industrial ones$q$, false),
    (3, 2, $q$Household volumes are too small to cause environmental harm$q$, false),
    (3, 3, $q$Enforcing the rules across every household would be impractical$q$, true),
    (3, 4, $q$States were given exclusive authority over residential waste$q$, false)
) AS c(q_position, position, text, is_correct)
ON c.q_position = iq.position;

-- ---------------------------------------------------------------------------
-- Lesson 3 -- Cradle to Grave  (objective 3)
-- ---------------------------------------------------------------------------

WITH target_lesson AS (
    SELECT l.id FROM lessons l JOIN courses c ON c.id = l.course_id
    WHERE c.slug = 'where-does-it-actually-go' AND l.slug = 'cradle-to-grave'
),
target_objective AS (
    SELECT o.id FROM learning_objectives o JOIN courses c ON c.id = o.course_id
    WHERE c.slug = 'where-does-it-actually-go' AND o.position = 3
),
inserted_questions AS (
    INSERT INTO questions (lesson_id, prompt, kind, feedback, objective_id, position)
    SELECT target_lesson.id, v.prompt, v.kind, v.feedback,
           CASE WHEN v.kind = 'assessment' THEN target_objective.id ELSE NULL END,
           v.position
    FROM target_lesson, target_objective,
    (VALUES
        (1, $q$A generator ships waste solvent to a permitted TSDF and receives no signed manifest copy back after seven weeks. What is the generator required to do?$q$,
            'review',
            $q$Cradle-to-grave liability means the generator never stops being responsible. When the signed copy doesn't return within roughly 45 days, the generator must file an exception report documenting the missing shipment. This requirement is the enforcement backbone of the manifest system — it makes losing track of a shipment the generator's problem.$q$),
        (2, $q$What is the primary function of the Uniform Hazardous Waste Manifest?$q$,
            'assessment',
            $q$The manifest is a chain of custody record — it establishes where a shipment came from, who handled it, and where it ended up. Note what it specifically does not do: liability never transfers. Under cradle-to-grave the generator remains responsible even after signing the waste over.$q$),
        (3, $q$Which statement about hazardous waste incineration is accurate?$q$,
            'assessment',
            $q$High-temperature incineration achieves 99.99% destruction of target organic compounds — and 99.9999% for dioxin-bearing wastes, so it is required rather than prohibited there. But combustion cannot destroy an element. Metals concentrate into ash that becomes its own disposal problem, and incineration sits near the bottom of the pollution prevention hierarchy.$q$)
    ) AS v(position, prompt, kind, feedback)
    RETURNING id, position
)
INSERT INTO choices (question_id, text, is_correct, position)
SELECT iq.id, c.text, c.is_correct, c.position
FROM inserted_questions iq
JOIN (VALUES
    (1, 1, $q$Nothing — liability transferred when the transporter signed$q$, false),
    (1, 2, $q$Contact the transporter, but no filing is required$q$, false),
    (1, 3, $q$File an exception report with EPA$q$, true),
    (1, 4, $q$Re-ship an equivalent quantity to a different facility$q$, false),

    (2, 1, $q$To certify that a waste has been treated to land disposal standards$q$, false),
    (2, 2, $q$To document the chain of custody from generator to disposal facility$q$, true),
    (2, 3, $q$To calculate the generator's monthly volume category$q$, false),
    (2, 4, $q$To transfer liability from the generator to the transporter$q$, false),

    (3, 1, $q$It eliminates both organic compounds and heavy metals$q$, false),
    (3, 2, $q$It is preferred over source reduction under federal policy$q$, false),
    (3, 3, $q$It destroys organic compounds but concentrates metals into ash requiring disposal$q$, true),
    (3, 4, $q$It is prohibited for any waste containing dioxins$q$, false)
) AS c(q_position, position, text, is_correct)
ON c.q_position = iq.position;

-- ---------------------------------------------------------------------------
-- Lesson 4 -- Love Canal and the Birth of Superfund  (objective 4)
-- ---------------------------------------------------------------------------

WITH target_lesson AS (
    SELECT l.id FROM lessons l JOIN courses c ON c.id = l.course_id
    WHERE c.slug = 'where-does-it-actually-go' AND l.slug = 'love-canal-and-the-birth-of-superfund'
),
target_objective AS (
    SELECT o.id FROM learning_objectives o JOIN courses c ON c.id = o.course_id
    WHERE c.slug = 'where-does-it-actually-go' AND o.position = 4
),
inserted_questions AS (
    INSERT INTO questions (lesson_id, prompt, kind, feedback, objective_id, position)
    SELECT target_lesson.id, v.prompt, v.kind, v.feedback,
           CASE WHEN v.kind = 'assessment' THEN target_objective.id ELSE NULL END,
           v.position
    FROM target_lesson, target_objective,
    (VALUES
        (1, $q$Under CERCLA's strict, joint and several liability standard, a company that legally disposed of waste at a site in 1968 is:$q$,
            'review',
            $q$"Strict" liability means legality at the time of disposal is not a defense. "Joint and several" means any one responsible party can be held accountable for the entire cost when others cannot pay. Congress wrote the standard this way deliberately, so that cleanups would not stall while parties litigated over shares.$q$),
        (2, $q$What legal gap did CERCLA fill that RCRA had left open?$q$,
            'assessment',
            $q$RCRA is forward-looking — it tracks and controls waste from creation onward. When Love Canal surfaced, the federal government discovered it had neither the authority nor the money to address decades of contamination that had been perfectly legal when it occurred. CERCLA created both.$q$),
        (3, $q$Why did Congress eventually pass separate brownfields legislation?$q$,
            'assessment',
            $q$Strict, joint and several liability worked as intended for enforcement but produced an unintended consequence: purchasing contaminated land could mean inheriting the entire cleanup bill, so nobody bought it. Thousands of urban industrial parcels sat abandoned until the 2002 brownfields law created protections for innocent purchasers.$q$)
    ) AS v(position, prompt, kind, feedback)
    RETURNING id, position
)
INSERT INTO choices (question_id, text, is_correct, position)
SELECT iq.id, c.text, c.is_correct, c.position
FROM inserted_questions iq
JOIN (VALUES
    (1, 1, $q$Not liable, because disposal was legal at the time$q$, false),
    (1, 2, $q$Liable only for its proportional share of the waste$q$, false),
    (1, 3, $q$Potentially liable for the full cleanup cost, even though disposal was legal$q$, true),
    (1, 4, $q$Liable only if it still owns the property$q$, false),

    (2, 1, $q$RCRA did not regulate hazardous waste transportation$q$, false),
    (2, 2, $q$RCRA applied only to federal facilities$q$, false),
    (2, 3, $q$RCRA governed waste going forward but provided no authority or funding to clean up already-contaminated sites$q$, true),
    (2, 4, $q$RCRA did not define which wastes were hazardous$q$, false),

    (3, 1, $q$Superfund cleanups were completing faster than expected$q$, false),
    (3, 2, $q$CERCLA liability made buyers unwilling to purchase contaminated property$q$, true),
    (3, 3, $q$The Hazard Ranking System was ruled unconstitutional$q$, false),
    (3, 4, $q$States refused to participate in the National Priorities List$q$, false)
) AS c(q_position, position, text, is_correct)
ON c.q_position = iq.position;

-- ---------------------------------------------------------------------------
-- Lesson 5 -- Not Making It in the First Place  (objective 5)
-- ---------------------------------------------------------------------------

WITH target_lesson AS (
    SELECT l.id FROM lessons l JOIN courses c ON c.id = l.course_id
    WHERE c.slug = 'where-does-it-actually-go' AND l.slug = 'not-making-it-in-the-first-place'
),
target_objective AS (
    SELECT o.id FROM learning_objectives o JOIN courses c ON c.id = o.course_id
    WHERE c.slug = 'where-does-it-actually-go' AND o.position = 5
),
inserted_questions AS (
    INSERT INTO questions (lesson_id, prompt, kind, feedback, objective_id, position)
    SELECT target_lesson.id, v.prompt, v.kind, v.feedback,
           CASE WHEN v.kind = 'assessment' THEN target_objective.id ELSE NULL END,
           v.position
    FROM target_lesson, target_objective,
    (VALUES
        (1, $q$A manufacturer replaces a chlorinated degreasing solvent with an aqueous cleaning system. Where does this fall on the pollution prevention hierarchy?$q$,
            'review',
            $q$Substituting a benign input for a hazardous one means the hazardous waste is never generated. That is source reduction — the highest tier of the hierarchy established by the Pollution Prevention Act of 1990. Treatment and disposal address waste that already exists; source reduction prevents its existence.$q$),
        (2, $q$Which household item should specifically not be placed in curbside trash or recycling because of fire risk?$q$,
            'assessment',
            $q$Lithium-ion batteries ignite when crushed in collection trucks or sorting facilities, and battery-caused fires are among the fastest-growing hazards reported by waste handlers. Retail take-back programs are widely available. Fully dried latex paint is the notable exception that generally is acceptable in regular trash.$q$)
    ) AS v(position, prompt, kind, feedback)
    RETURNING id, position
)
INSERT INTO choices (question_id, text, is_correct, position)
SELECT iq.id, c.text, c.is_correct, c.position
FROM inserted_questions iq
JOIN (VALUES
    (1, 1, $q$Treatment$q$, false),
    (1, 2, $q$Recycling$q$, false),
    (1, 3, $q$Source reduction$q$, true),
    (1, 4, $q$Disposal$q$, false),

    (2, 1, $q$Latex paint that has been fully dried$q$, false),
    (2, 2, $q$Lithium-ion batteries$q$, true),
    (2, 3, $q$Empty steel food cans$q$, false),
    (2, 4, $q$Cardboard packaging$q$, false)
) AS c(q_position, position, text, is_correct)
ON c.q_position = iq.position;

-- ---------------------------------------------------------------------------
-- Verification. Check every row of this before COMMIT.
-- ---------------------------------------------------------------------------

-- Total counts: expect 15 questions (5 review, 10 assessment), 60 choices
-- (15 questions × 4 choices each).
SELECT
    count(*) FILTER (WHERE q.kind = 'review')      AS review_questions,
    count(*) FILTER (WHERE q.kind = 'assessment')  AS assessment_questions,
    count(*)                                       AS total_questions
FROM questions q
JOIN lessons l ON l.id = q.lesson_id
JOIN courses c ON c.id = l.course_id
WHERE c.slug = 'where-does-it-actually-go';

SELECT count(*) AS total_choices
FROM choices ch
JOIN questions q ON q.id = ch.question_id
JOIN lessons l ON l.id = q.lesson_id
JOIN courses c ON c.id = l.course_id
WHERE c.slug = 'where-does-it-actually-go';

-- Exactly-one-correct-choice check: expect ZERO rows back.
SELECT q.id, q.prompt, count(*) FILTER (WHERE ch.is_correct) AS correct_count
FROM questions q
JOIN choices ch ON ch.question_id = q.id
JOIN lessons l ON l.id = q.lesson_id
JOIN courses c ON c.id = l.course_id
WHERE c.slug = 'where-does-it-actually-go'
GROUP BY q.id, q.prompt
HAVING count(*) FILTER (WHERE ch.is_correct) != 1;

-- Every review question has feedback: expect ZERO rows back.
SELECT q.id, q.prompt
FROM questions q
JOIN lessons l ON l.id = q.lesson_id
JOIN courses c ON c.id = l.course_id
WHERE c.slug = 'where-does-it-actually-go' AND q.kind = 'review' AND (q.feedback IS NULL OR q.feedback = '');

-- Objective coverage: expect all 5 objectives, each with >= 1 assessment question.
SELECT o.position, o.text, count(q.id) AS assessment_questions_covering
FROM learning_objectives o
JOIN courses c ON c.id = o.course_id
LEFT JOIN questions q ON q.objective_id = o.id AND q.kind = 'assessment'
WHERE c.slug = 'where-does-it-actually-go'
GROUP BY o.id, o.position, o.text
ORDER BY o.position;

-- ---------------------------------------------------------------------------
-- Hard post-check. Same rules validate_for_publish will apply later, asserted
-- now so a shape problem surfaces here rather than at publish time. Every rule
-- below is question-side only -- credit, video duration, and the per-credit
-- floors in 5.01.2.1 / 6.01.2 cannot be checked until the segments are recorded
-- and feature 022's credit_award exists.
-- ---------------------------------------------------------------------------

DO $do$
DECLARE
    n         int;
    detail    text;
BEGIN
    SELECT count(*) INTO n
    FROM questions q JOIN lessons l ON l.id = q.lesson_id
    JOIN courses c ON c.id = l.course_id
    WHERE c.slug = 'where-does-it-actually-go';
    IF n <> 15 THEN RAISE EXCEPTION 'post-check: expected 15 questions, found %', n; END IF;

    SELECT count(*) INTO n
    FROM questions q JOIN lessons l ON l.id = q.lesson_id
    JOIN courses c ON c.id = l.course_id
    WHERE c.slug = 'where-does-it-actually-go' AND q.kind = 'review';
    IF n <> 5 THEN RAISE EXCEPTION 'post-check: expected 5 review questions, found %', n; END IF;

    SELECT count(*) INTO n
    FROM questions q JOIN lessons l ON l.id = q.lesson_id
    JOIN courses c ON c.id = l.course_id
    WHERE c.slug = 'where-does-it-actually-go' AND q.kind = 'assessment';
    IF n <> 10 THEN RAISE EXCEPTION 'post-check: expected 10 assessment questions, found %', n; END IF;

    SELECT count(*) INTO n
    FROM choices ch JOIN questions q ON q.id = ch.question_id
    JOIN lessons l ON l.id = q.lesson_id JOIN courses c ON c.id = l.course_id
    WHERE c.slug = 'where-does-it-actually-go';
    IF n <> 60 THEN RAISE EXCEPTION 'post-check: expected 60 choices, found %', n; END IF;

    -- Service-layer validation this script bypasses: exactly one correct choice.
    SELECT string_agg(x.prompt, ' | ') INTO detail FROM (
        SELECT q.prompt FROM questions q
        JOIN choices ch ON ch.question_id = q.id
        JOIN lessons l ON l.id = q.lesson_id JOIN courses c ON c.id = l.course_id
        WHERE c.slug = 'where-does-it-actually-go'
        GROUP BY q.id, q.prompt
        HAVING count(*) FILTER (WHERE ch.is_correct) <> 1
    ) x;
    IF detail IS NOT NULL THEN
        RAISE EXCEPTION 'post-check: question(s) without exactly one correct choice: %', detail;
    END IF;

    -- 5.01.2.2: feedback is mandatory on review questions.
    SELECT string_agg(q.prompt, ' | ') INTO detail
    FROM questions q JOIN lessons l ON l.id = q.lesson_id
    JOIN courses c ON c.id = l.course_id
    WHERE c.slug = 'where-does-it-actually-go' AND q.kind = 'review'
      AND (q.feedback IS NULL OR btrim(q.feedback) = '');
    IF detail IS NOT NULL THEN
        RAISE EXCEPTION 'post-check: review question(s) with blank feedback (5.01.2.2): %', detail;
    END IF;

    -- 6.01.2: forced-choice responses are not permissible on the assessment.
    -- MIN_CHOICES_ASSESSMENT = 3 in app/constants/question_minimums.py.
    SELECT string_agg(x.prompt, ' | ') INTO detail FROM (
        SELECT q.prompt FROM questions q
        JOIN choices ch ON ch.question_id = q.id
        JOIN lessons l ON l.id = q.lesson_id JOIN courses c ON c.id = l.course_id
        WHERE c.slug = 'where-does-it-actually-go' AND q.kind = 'assessment'
        GROUP BY q.id, q.prompt HAVING count(*) < 3
    ) x;
    IF detail IS NOT NULL THEN
        RAISE EXCEPTION 'post-check: assessment question(s) with fewer than 3 choices (6.01.2): %', detail;
    END IF;

    -- 6.01.2: duplicate review and assessment questions are not allowed.
    -- Same normalisation admin_content.py uses: whitespace and case folded.
    SELECT string_agg(x.p, ' | ') INTO detail FROM (
        SELECT lower(regexp_replace(btrim(q.prompt), '\s+', ' ', 'g')) AS p
        FROM questions q JOIN lessons l ON l.id = q.lesson_id
        JOIN courses c ON c.id = l.course_id
        WHERE c.slug = 'where-does-it-actually-go'
        GROUP BY 1 HAVING count(*) > 1
    ) x;
    IF detail IS NOT NULL THEN
        RAISE EXCEPTION 'post-check: duplicate question prompt(s) (6.01.2): %', detail;
    END IF;

    -- 6.01.2: the assessment must measure >= 75% of the course's objectives.
    -- This course targets 100%; anything less means an objective lost its tag.
    SELECT string_agg(o.text, ' | ' ORDER BY o.position) INTO detail
    FROM learning_objectives o JOIN courses c ON c.id = o.course_id
    WHERE c.slug = 'where-does-it-actually-go'
      AND NOT EXISTS (
        SELECT 1 FROM questions q
        WHERE q.objective_id = o.id AND q.kind = 'assessment'
      );
    IF detail IS NOT NULL THEN
        RAISE EXCEPTION 'post-check: objective(s) with no assessment question (6.01.2): %', detail;
    END IF;

    -- Coverage is an assessment-only rule; review questions stay untagged.
    SELECT count(*) INTO n
    FROM questions q JOIN lessons l ON l.id = q.lesson_id
    JOIN courses c ON c.id = l.course_id
    WHERE c.slug = 'where-does-it-actually-go'
      AND q.kind = 'review' AND q.objective_id IS NOT NULL;
    IF n <> 0 THEN
        RAISE EXCEPTION 'post-check: % review question(s) carry an objective_id; '
            'they should be NULL', n;
    END IF;

    -- This course's positional boundary is 1, not the ASC 606 scripts' 3.
    SELECT count(*) INTO n
    FROM questions q JOIN lessons l ON l.id = q.lesson_id
    JOIN courses c ON c.id = l.course_id
    WHERE c.slug = 'where-does-it-actually-go'
      AND ((q.position = 1 AND q.kind <> 'review')
        OR (q.position > 1 AND q.kind <> 'assessment'));
    IF n <> 0 THEN
        RAISE EXCEPTION 'post-check: % question(s) violate this course''s '
            'position-1-is-review boundary', n;
    END IF;

    RAISE NOTICE 'post-check: all question-side rules pass. Safe to COMMIT.';
END
$do$;

-- If everything above looks right:
-- COMMIT;
-- Otherwise:
-- ROLLBACK;
--
-- AFTER COMMIT, in this order -- see the note in the accompanying summary:
--   1. Touch content_updated_at on the course. This script bypasses
--      app/services/admin_content.py, so nothing has moved it, and feature 021's
--      publish rule compares reviewed_at against it.
--   2. Then do the human content review, and only then set reviewed_at.
--      Setting reviewed_at first would attest to a review of content that did
--      not exist when the date was stamped.
--   3. Record the video, let duration_seconds come from the measured render,
--      and confirm av_is_additional_learning is true and word_count is 0 on all
--      five lessons before reading the credit panel.
