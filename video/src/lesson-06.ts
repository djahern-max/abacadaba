/**
 * Lesson 06 — "Where the Heat Actually Went"
 * Course: Clean Ocean Energy Systems (Grade 10 Environmental Science, NOT CPE)
 *
 * STATUS: DRAFT — NOT REVIEWED. Clear `meta.status` once a subject matter
 * expert has read the narration (4.01.1, 4.02), then re-render. Clearing the
 * stamp does not require regenerating audio.
 *
 * LESSON NUMBERING. This is the sixth lesson module in the package but the
 * FIRST lesson of its course. `lessonId` is the package-wide id and drives the
 * audio directory; `eyebrow` is course-relative and reads "Lesson 01". They
 * disagree on purpose. Do not "fix" one to match the other.
 *
 * NOT CPE. `fieldOfStudy` is the non_cpe sentinel. This content is a high
 * school environmental science unit, deliberately non-financial, and it exists
 * to exercise the generic slide set against subject matter the package has
 * never seen. Do not let it acquire a real field of study.
 *
 * Maps to course learning objective 1: quantify the ocean's role as a global
 * heat reservoir by calculating absorbed thermal energy (Q = mcΔT) and
 * comparing water to air. One review question is tagged to this objective, and
 * it asks the student to read a temperature rise as an energy claim — so
 * block-03 has to actually do the arithmetic on screen, not gesture at it.
 *
 * SLIDE NOTE: blocks 03 and 06 are charts in the source deck — a cube-law bar
 * chart and a Carnot curve. There is no chart component, so both are authored
 * as `Calc` figures, which is arguably better here: the rows reveal one at a
 * time as the narrator reaches each number, which a static chart cannot do.
 * If a `Chart` component ever lands, swapping those figures is a re-render
 * only — narration and reveal counts are unaffected, so the audio survives.
 *
 * KNOWN DEFECT, not mine to fix here: `Title` in slides.tsx hard-codes the
 * strip "LESSON 2 OF 5 · SELF STUDY · ACCOUNTING". It will render that over
 * this lesson's title sheet. See the note at the bottom of this file.
 *
 * Types are imported from lesson-01, which is the single definition point.
 * Do not redefine Block or Figure here — two copies will drift.
 *
 * Reveal markers: [[r]] sits in `narration`, immediately before the WORD it
 * reveals. The number of markers in a block MUST equal the length of that
 * block's `reveals` array. Verify with
 * `npm run generate -- --lesson 06 --dry-run` before spending any credit.
 */

import audioMeta from "./audio-meta-06.json";
import type { Block } from "./lesson-01";

export type { Block, Figure } from "./lesson-01";

export const meta = {
  lessonId: "06",
  courseCode: "OCEAN-01",
  courseTitle: "Clean Ocean Energy Systems",
  lessonTitle: "Where the Heat Actually Went",
  title: "Where the Heat Actually Went",
  subtitle: "Ocean heat capacity, thermal inertia, and the resource they create",
  eyebrow: "Lesson 01",
  position: "Lesson 1 of 5",
  deliveryMethod: "Self study",
  fieldOfStudy: "Not CPE eligible",
  revision: "A",
  revisionDate: "2026-08-25",
  status: "DRAFT — NOT REVIEWED",
};

export const blocks: Block[] = [
  {
    id: "title",
    sheet: "S-00",
    citation: "",
    slide: "Title",
    narration: "",
    reveals: [0.5, 1.5, 2.5],
    estimatedSeconds: 8,
  },

  {
    id: "block-01",
    sheet: "S-01",
    citation: "IPCC AR6 WG1 Ch. 9",
    slide: "Statement",
    figure: {
      kind: "statement",
      lines: [
        "More than 90% of the excess heat went into the ocean",
        "Water stores heat like nothing else on Earth",
        "That stored heat is the resource",
      ],
    },
    narration:
      "When we talk about a warming planet, we usually picture warming air. That " +
      "picture is almost entirely wrong. Since the nineteen seventies, the excess " +
      "energy trapped by greenhouse gases has not mostly gone into the atmosphere. " +
      "[[r]]More than ninety percent of it went into the ocean. The atmosphere took " +
      "a couple of percent. The rest is in seawater, and most of that in the top " +
      "two thousand metres. The reason is a property of water itself. [[r]]Water " +
      "stores heat in a way that essentially nothing else at the planet's surface " +
      "does, which is why the ocean can swallow that much energy and warm by only a " +
      "fraction of a degree. Hold on to that, because it has a second consequence " +
      "people rarely connect to the first. [[r]]All of that stored heat is a " +
      "resource, and this course is about taking some of it back.",
    reveals: [1.0, 32.0, 63.0],
    estimatedSeconds: 66,
  },

  {
    id: "block-02",
    sheet: "S-02",
    citation: "NOAA NCEI; CRC Handbook",
    slide: "Facts",
    figure: {
      kind: "facts",
      rows: [
        { label: "Share of excess heat held by the ocean", value: "> 90 %" },
        { label: "Specific heat of water", value: "4,184 J/kg·K" },
        { label: "Specific heat of air", value: "1,005 J/kg·K" },
        { label: "Heat per unit volume, water vs. air", value: "~ 3,200 ×" },
      ],
    },
    narration:
      "Three numbers carry this lesson, and the fourth is the one that surprises " +
      "people. The first: [[r]]more than ninety percent of the excess heat in the " +
      "climate system is in the ocean. The second is why. The specific heat of " +
      "water is [[r]]four thousand one hundred eighty-four joules per kilogram per " +
      "kelvin. That is the energy it takes to raise one kilogram of water by one " +
      "degree. Compare it with air, at [[r]]one thousand and five. Water needs " +
      "roughly four times the energy per kilogram. But per kilogram is the wrong " +
      "comparison, because the ocean is not measured in kilograms of air. Water is " +
      "about eight hundred times denser, so for the same volume it holds something " +
      "like [[r]]three thousand two hundred times the heat. That factor is the " +
      "whole story.",
    reveals: [1.0, 19.7, 38.3, 57.0],
    estimatedSeconds: 60,
  },

  {
    id: "block-03",
    sheet: "S-03",
    citation: "Q = mcΔT",
    slide: "Calc",
    figure: {
      kind: "calc",
      rows: [
        { label: "Water sample, 200 mL", value: "0.200 kg" },
        { label: "Air sample, same volume", value: "0.00024 kg" },
        { label: "Water:  0.200 × 4,184 × 3 K", value: "2,510 J" },
        { label: "Air:  0.00024 × 1,005 × 12 K", value: "2.9 J", emphasis: "wrong" },
        {
          label: "Energy absorbed, water vs. air",
          value: "≈ 870 ×",
          rule: true,
          emphasis: "right",
        },
      ],
    },
    narration:
      "Here is the arithmetic, using numbers close to what a class actually gets. " +
      "Two hundred millilitres of water is [[r]]two tenths of a kilogram. The same " +
      "volume of air weighs [[r]]about a quarter of a gram — the density difference " +
      "doing its work before we even start. Put both under matched lamps for ten " +
      "minutes, and suppose the water rises three degrees while the air rises " +
      "twelve. Run Q equals m c delta T on the water and you get [[r]]roughly " +
      "twenty-five hundred joules absorbed. Run it on the air and you get " +
      "[[r]]under three joules. The air rose four times as many degrees and " +
      "absorbed about [[r]]eight hundred and seventy times less energy. This is " +
      "where the lesson lands, and it is also where students get it backwards. A " +
      "bigger temperature rise is not more energy. It is less mass and less " +
      "specific heat.",
    reveals: [1.0, 16.8, 32.5, 48.2, 64.0],
    estimatedSeconds: 67,
  },

  {
    id: "block-04",
    sheet: "S-04",
    citation: "IPCC AR6 WG1 Ch. 9",
    slide: "Compare",
    figure: {
      kind: "compare",
      columns: [
        {
          heading: "Atmosphere",
          rows: [
            { label: "Excess heat", value: "~ 1 %" },
            { label: "Mass", value: "5.1 × 10¹⁸ kg" },
            { label: "Responds in", value: "Days to weeks" },
          ],
        },
        {
          heading: "Ocean",
          emphasis: "right",
          rows: [
            { label: "Excess heat", value: "> 90 %" },
            { label: "Mass", value: "1.4 × 10²¹ kg" },
            { label: "Responds in", value: "Decades to centuries" },
          ],
        },
      ],
    },
    narration:
      "Set the two reservoirs side by side. The [[r]]atmosphere holds roughly one " +
      "percent of the excess heat, weighs about five times ten to the eighteenth " +
      "kilograms, and responds fast — days to weeks. A cold snap is the atmosphere " +
      "changing its mind. The [[r]]ocean holds more than ninety percent, weighs " +
      "nearly three hundred times as much, and responds over decades to centuries. " +
      "That last row is the one worth sitting with, because it means two things at " +
      "once. It means the ocean buys us time: heat going into seawater is heat not " +
      "raising air temperature this year. And it means the warming already " +
      "committed to the ocean will keep expressing itself long after emissions " +
      "stop. Thermal inertia is a buffer and a debt, and it is the same property " +
      "either way.",
    reveals: [1.0, 57.0],
    estimatedSeconds: 60,
  },

  {
    id: "block-05",
    sheet: "S-05",
    citation: "IPCC AR6 WG1 Ch. 5, 9",
    slide: "List",
    figure: {
      kind: "list",
      items: [
        "Thermal expansion — warm water takes up more room",
        "Carbon uptake — about a quarter of our CO₂, and falling pH",
        "Stronger gradients — more energy in waves, currents, layers",
        "A resource — the same gradients a converter harvests",
      ],
    },
    narration:
      "One reservoir, four consequences, and they are not independent. First, " +
      "[[r]]thermal expansion. Warm water occupies more volume, and a large share " +
      "of the sea level rise measured so far is the ocean getting bigger rather " +
      "than ice melting into it. Second, [[r]]carbon. The ocean has absorbed " +
      "roughly a quarter of the carbon dioxide we have emitted, and it pays for " +
      "that in acidity — surface pH has fallen measurably since the industrial " +
      "revolution. Third, [[r]]gradients. Heat differences drive wind, wind drives " +
      "waves, and temperature layers drive circulation, so more stored energy means " +
      "more energetic systems. And fourth, the one this course exists for: " +
      "[[r]]those same gradients are a resource. A wave converter, a tidal turbine, " +
      "and a thermal cycle are all machines for extracting energy the climate " +
      "system has already concentrated for us.",
    reveals: [1.0, 20.0, 39.0, 58.0],
    estimatedSeconds: 61,
  },

  {
    id: "block-06",
    sheet: "S-06",
    citation: "P ≈ ρg²H²T / 64π;  ½ρv³",
    slide: "Calc",
    figure: {
      kind: "calc",
      rows: [
        { label: "Swell, 2 m high, 8 s period", value: "16 kW/m of crest" },
        { label: "Across a 2 m capture face", value: "8.0 kW/m²" },
        { label: "Wind at 10 m/s,  ½ρv³", value: "0.61 kW/m²" },
        {
          label: "Ocean wave vs. surface wind",
          value: "≈ 13 ×",
          rule: true,
          emphasis: "right",
        },
      ],
    },
    narration:
      "Now put a number on the resource itself. A deep water swell two metres high " +
      "with an eight second period carries roughly [[r]]sixteen kilowatts through " +
      "every metre of its crest. That is a per-metre figure, so to compare it with " +
      "wind we need an area. Spread it across a two metre capture face and you get " +
      "[[r]]eight kilowatts per square metre. Wind, meanwhile: at ten metres per " +
      "second — a brisk day, not a storm — the power flux is one half rho v cubed, " +
      "or [[r]]about six hundred watts per square metre. Divide one by the other " +
      "and the ocean wave is carrying [[r]]roughly thirteen times the power through " +
      "the same area. And that is before you account for a swell arriving through " +
      "the night, and for wave conditions being forecastable days ahead. Density " +
      "and persistence are the ocean's two advantages.",
    reveals: [1.0, 21.7, 42.3, 63.0],
    estimatedSeconds: 66,
  },

  {
    id: "block-07",
    sheet: "S-07",
    citation: "",
    slide: "Statement",
    figure: {
      kind: "statement",
      lines: [
        "The ocean is where the energy went",
        "The gradients are getting stronger, not weaker",
        "The rest of this course is machines for tapping them",
      ],
    },
    narration:
      "So the picture to leave with is this. [[r]]The ocean is where the energy " +
      "went — not the air, not mostly the ice, the water. It went there because " +
      "water's heat capacity and density make it an extraordinary reservoir, and it " +
      "will come back out slowly, over decades. Second, [[r]]the gradients are " +
      "getting stronger rather than weaker. More stored heat means more energetic " +
      "waves, sharper thermal layers, and shifting currents. And third, [[r]]the " +
      "rest of this course is four machines for tapping those gradients: a wave " +
      "converter, a tidal turbine, a thermal cycle, and finally the judgement about " +
      "whether any of them belong at a particular stretch of coast. We start with " +
      "waves.",
    reveals: [1.0, 25.0, 49.0],
    estimatedSeconds: 52,
  },
];

type BlockMeta = { durationSeconds: number; reveals: number[]; hash: string };
const audio = audioMeta as Record<string, BlockMeta>;

/** The transcript of record: markers stripped, nothing else changed. */
export const transcriptOf = (b: Block): string =>
  b.narration.replace(/\s*\[\[r\]\]\s*/g, " ").replace(/\s+/g, " ").trim();

/** What gets sent to ElevenLabs. Markers intact; the script strips them. */
export const speechOf = (b: Block): string => b.speech ?? b.narration;

export const hasAudio = (b: Block): boolean => audio[b.id] !== undefined;

export const durationOf = (b: Block): number =>
  audio[b.id]?.durationSeconds ?? b.estimatedSeconds;

/** Measured reveals when we have them, hand-written estimates when we do not. */
export const revealsOf = (b: Block): number[] =>
  audio[b.id]?.reveals ?? b.reveals;

/**
 * Blocks with empty narration have no audio by design — the title sheet is the
 * only one. Counting it here would make this permanently true and the warning
 * in Root.tsx permanently useless.
 */
export const usingEstimates = blocks.some(
  (b) => b.narration.trim().length > 0 && !hasAudio(b)
);

export const totalSeconds = blocks.reduce((sum, b) => sum + durationOf(b), 0);

/*
 * WHAT THIS LESSON FOUND OUT ABOUT THE GENERIC SLIDE SET
 * ------------------------------------------------------
 * This is the first lesson written against subject matter with no relationship
 * to the ones the components were designed for. Four findings, in order of how
 * much they cost:
 *
 * 1. `Title` is not generic. It hard-codes "LESSON 2 OF 5 · SELF STUDY ·
 *    ACCOUNTING" in its footer strip. Every lesson since 02 has been rendering
 *    lesson 02's position and lesson 02's field of study. It has been invisible
 *    because every lesson so far has been lesson-02-adjacent — same course,
 *    same field. This one is neither, and the strip is simply wrong on screen.
 *    Fix: move position, delivery method, and field of study into `meta` and
 *    read them, the way `courseTitle` and `lessonTitle` already are.
 *
 * 2. `Facts` and `Calc` are the same component wearing different labels. Both
 *    are label-left, monospace-value-right, one row per reveal. The only real
 *    differences are `rule` and `emphasis`, and there is no reason `Facts`
 *    could not carry both. Not urgent, but worth knowing before a seventh kind
 *    gets added.
 *
 * 3. `Compare` assumes the two columns share a row schema and does not enforce
 *    it. Both columns here use the same three labels, which is what makes the
 *    sheet readable — but nothing in the type would have stopped a lesson from
 *    giving one column four rows and the other two, producing a comparison
 *    that compares nothing. A shared `labels: string[]` plus per-column values
 *    would make the shape honest.
 *
 * 4. `List` numbers its items 01, 02, 03 unconditionally. That is right for an
 *    ordered process and wrong for an unordered set. Block-05 is genuinely
 *    ordered so it does not bite here, but the hazardous waste lessons authored
 *    unordered content as `List` too, and those are numbered as though sequence
 *    means something.
 *
 * None of the four are fixed in this file. Fixing 1 changes every existing
 * lesson's title sheet, which is a re-render of four videos and belongs in its
 * own feature with its own frame diff.
 */
