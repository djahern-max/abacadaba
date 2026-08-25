/**
 * Lesson 01 — "What Makes a Waste 'Hazardous'?"
 * Course: Where Does It Actually Go? (hazardous waste, ESG/Sustainability)
 *
 * STATUS: DRAFT — NOT REVIEWED. Narration has not been read by a subject
 * matter expert. Do not generate audio for participant-facing use until it
 * has been (4.01.1, 4.02).
 *
 * Content is data. No React, no JSX, no timing logic in this file.
 *
 * Duration resolution order: audio-meta.json first, estimatedSeconds second.
 * `estimatedSeconds` is Math.round(wordCount / 130 * 60) — 130 wpm is the
 * measured narration pace, not a guess. It exists only so a silent render has
 * a length; it is discarded the moment audio exists and must never reach a
 * credit calculation (7.02.7).
 *
 * Reveal markers: [[r]] sits in `narration`, immediately before the WORD it
 * reveals — not at the start of the sentence. generate-audio.ts strips the
 * markers, reads their real timestamps out of the ElevenLabs alignment
 * stream, and writes them to audio-meta.json. No timing number belongs in
 * this file except as a fallback: `reveals` is a preview estimate, discarded
 * the moment audio exists.
 *
 * The number of [[r]] markers in a block MUST equal the length of that
 * block's `reveals` array. Slide components index into it positionally; a
 * mismatch renders `undefined` and the element never appears. Verify with
 * `npm run generate -- --dry-run` before spending any API credit.
 *
 * Sheet pacing: 40–75 seconds per sheet. Attention resets every 20–30
 * seconds and a new sheet is the cheapest reset available.
 */

import audioMeta from "./audio-meta.json";

export type Figure =
  | { kind: "statement"; lines: string[] }
  | { kind: "facts"; rows: { label: string; value: string }[] }
  | {
    kind: "calc";
    rows: {
      label: string;
      value: string;
      emphasis?: "wrong" | "right";
      rule?: boolean;
    }[];
  }
  | { kind: "list"; items: string[] }
  | {
    kind: "compare";
    columns: {
      heading: string;
      rows: { label: string; value: string }[];
      emphasis?: "wrong" | "right";
    }[];
  };

export type Block = {
  id: string;
  sheet: string;
  citation: string;
  slide: "Title" | "Statement" | "Facts" | "Calc" | "List" | "Compare";
  figure?: Figure;
  narration: string; // transcript of record, may contain [[r]] markers
  reveals: number[]; // fallback seconds from block start, used until measured
  estimatedSeconds: number;
  speech?: string; // overrides narration for TTS only; rarely needed
};

export const meta = {
  lessonId: "01",
  courseCode: "HAZWASTE-01",
  courseTitle: "Where Does It Actually Go?",
  lessonTitle: 'What Makes a Waste "Hazardous"?',
  title: 'What Makes a Waste "Hazardous"?',
  subtitle: "Four characteristics, four lists",
  eyebrow: "Lesson 01",
  position: "Lesson 1 of 5",
  deliveryMethod: "Self study",
  fieldOfStudy: "ESG/Sustainability",
  revision: "A",
  revisionDate: "2026-08-20",
  status: "",
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
    citation: "42 U.S.C. §6901 et seq.; 40 CFR Part 261",
    slide: "Statement",
    figure: {
      kind: "statement",
      lines: [
        "RCRA, 1976 — a legal definition, not a scientific one",
        "40 CFR Part 261",
        "Two doors in: characteristic, or listed",
      ],
    },
    narration:
      "In nineteen seventy-six Congress passed the [[r]]Resource Conservation and Recovery Act, and with it created something that had not existed before: a legal definition of hazardous waste. Not a scientific one. A legal one. That distinction is the whole subject. A drum of solvent sitting in the back of a shop is not hazardous because a chemist looked at it and felt uneasy. It is hazardous because it meets a definition written into [[r]]Title forty of the Code of Federal Regulations, Part two sixty-one. And there are exactly two ways for a waste to meet that definition. It either [[r]]exhibits one of four characteristics, or it appears by name on one of four lists.",
    reveals: [1, 25, 49],
    estimatedSeconds: 53,
  },

  {
    id: "block-02",
    sheet: "S-02",
    citation: "40 CFR §§261.21–261.24",
    slide: "List",
    figure: {
      kind: "list",
      items: [
        "Ignitability — D001",
        "Corrosivity — D002",
        "Reactivity — D003",
        "Toxicity — D004 through D043",
      ],
    },
    narration:
      "Start with the first door, the characteristics. There are four of them, and they are worth memorizing because they carry the whole weight of the program for any generator who is not on a list. [[r]]Ignitability — it burns. [[r]]Corrosivity — it eats through things. [[r]]Reactivity — it is unstable, or it releases something dangerous when disturbed. And [[r]]toxicity — it leaches poison into groundwater over time. Each one carries a waste code beginning with the letter D. If your waste exhibits any one of these, it is hazardous waste, and nobody has to have written it down on a list anywhere for that to be true.",
    reveals: [1, 15, 30, 45],
    estimatedSeconds: 49,
  },

  {
    id: "block-03",
    sheet: "S-03",
    citation: "40 CFR §261.21",
    slide: "Facts",
    figure: {
      kind: "facts",
      rows: [
        { label: "Waste code", value: "D001" },
        { label: "Liquids", value: "Flash point below 140°F (60°C)" },
        { label: "Test method", value: "Pensky-Martens or Setaflash closed cup" },
        { label: "Also covers", value: "Oxidizers, ignitable gases, friction hazards" },
      ],
    },
    narration:
      "[[r]]Ignitability is code D zero zero one, and it is the one most people meet first, because it covers most solvents, most paints, and most thinners. For a liquid, the test is the [[r]]flash point: if the vapor above it will ignite below one hundred forty degrees Fahrenheit, sixty degrees Celsius, the waste is ignitable. That number is not a judgment call. It comes from a [[r]]closed-cup apparatus, either Pensky-Martens or Setaflash, run to a published method. But ignitability is broader than flammable liquids. It also captures [[r]]oxidizers, compressed gases that ignite, and solids that catch fire through friction or through absorbing moisture. A rag soaked in linseed oil belongs to this category as surely as a can of acetone does.",
    reveals: [1, 18, 35, 52],
    estimatedSeconds: 56,
  },

  {
    id: "block-04",
    sheet: "S-04",
    citation: "40 CFR §261.22",
    slide: "Facts",
    figure: {
      kind: "facts",
      rows: [
        { label: "Waste code", value: "D002" },
        { label: "Aqueous", value: "pH ≤ 2.0 or pH ≥ 12.5" },
        { label: "Liquids", value: "Corrodes SAE 1020 steel > 6.35 mm/year" },
        { label: "Note", value: "Both ends of the scale — not just acids" },
      ],
    },
    narration:
      "[[r]]Corrosivity is D zero zero two, and it is the cleanest of the four, because for most wastes it reduces to a single number you can read off a meter. An aqueous waste is corrosive if its [[r]]pH is two or below, or twelve and a half or above. Note that this is both ends of the scale. Sodium hydroxide drain cleaner is corrosive waste for exactly the same regulatory reason that hydrochloric acid is, and the second half of that sentence surprises people constantly. There is also a [[r]]second test for liquids that are not aqueous: if the liquid eats through steel faster than six and a third millimeters a year, it qualifies. [[r]]Both ends. Not just acids.",
    reveals: [1, 17, 34, 51],
    estimatedSeconds: 55,
  },

  {
    id: "block-05",
    sheet: "S-05",
    citation: "40 CFR §261.23",
    slide: "Facts",
    figure: {
      kind: "facts",
      rows: [
        { label: "Waste code", value: "D003" },
        { label: "Criteria", value: "Narrative — no single laboratory test" },
        { label: "Covers", value: "Unstable, water-reactive, explosive" },
        { label: "Also", value: "Cyanide or sulfide bearing, pH 2 to 12.5" },
      ],
    },
    narration:
      "[[r]]Reactivity, D zero zero three, is the awkward one, and it is awkward for an honest reason: there is [[r]]no single laboratory test for it. The criteria are narrative. A waste is reactive if it is normally unstable, if it reacts violently with water, if it forms an explosive mixture with water, or if it is capable of detonation when heated or struck. [[r]]Cyanide and sulfide bearing wastes are named specifically, because they generate toxic gases across the ordinary pH range between two and twelve and a half. Because the criteria are narrative, reactivity is where generator knowledge matters most. [[r]]You cannot send a sample out and get a yes or no back. Somebody has to know what is in the drum.",
    reveals: [1, 18, 35, 52],
    estimatedSeconds: 56,
  },

  {
    id: "block-06",
    sheet: "S-06",
    citation: "40 CFR §261.24, Table 1",
    slide: "Facts",
    figure: {
      kind: "facts",
      rows: [
        { label: "Waste codes", value: "D004 through D043" },
        { label: "Test method", value: "TCLP — SW-846 Method 1311" },
        { label: "Contaminants", value: "40, each with its own regulatory level" },
        { label: "Examples", value: "Lead 5.0 mg/L · Mercury 0.2 · Benzene 0.5" },
      ],
    },
    narration:
      "[[r]]Toxicity covers the widest ground — codes D zero zero four all the way through D zero four three — and it asks a different question from the other three. Not is this dangerous to handle today, but will this leach something dangerous into groundwater after it is buried. The test is the [[r]]Toxicity Characteristic Leaching Procedure, the T C L P, and what it does is simulate a landfill: the waste is tumbled in a mild acid for eighteen hours, and then the liquid that comes off is analyzed. There are [[r]]forty contaminants on the table, each with its own regulatory level. [[r]]Lead at five milligrams per liter. Mercury at two tenths. Benzene at half a milligram. Exceed the level for any one of them and the waste is hazardous.",
    reveals: [1, 19, 37, 56],
    estimatedSeconds: 60,
  },

  {
    id: "block-07",
    sheet: "S-07",
    citation: "40 CFR §§261.31–261.33",
    slide: "List",
    figure: {
      kind: "list",
      items: [
        "F list — non-specific sources (spent solvents, plating)",
        "K list — specific industries (refining, wood preserving)",
        "P list — acutely hazardous discarded chemicals",
        "U list — toxic discarded commercial chemicals",
      ],
    },
    narration:
      "Now the second door. A waste can be hazardous without exhibiting any characteristic at all, simply because it appears by name on a list, and there are four of those. The [[r]]F list covers wastes from non-specific sources — spent solvents and electroplating sludges, generated across many industries. The [[r]]K list is the opposite: wastes from specific industries, named one at a time, petroleum refining and wood preserving among them. Then two lists of unused commercial chemical products that have been discarded. The [[r]]P list is the acutely hazardous ones, and it carries a far lower quantity threshold — one kilogram, not one hundred. The [[r]]U list is the merely toxic ones. If your waste is on a list, it is hazardous, full stop. No test will get you out of it.",
    reveals: [1, 19, 38, 57],
    estimatedSeconds: 61,
  },

  {
    id: "block-08",
    sheet: "S-08",
    citation: "40 CFR §261.3",
    slide: "Statement",
    figure: {
      kind: "statement",
      lines: [
        "Check both doors, every time",
        "Mixture rule · derived-from rule",
        "A listed waste stays listed",
      ],
    },
    narration:
      "So the working habit is this: [[r]]check both doors, every time. Run the characteristics, and check the lists, because a waste can walk through either one and plenty walk through both. And there is one more thing that catches people, which is what happens when hazardous waste mixes with something else or gets treated. Under the [[r]]mixture rule, a listed waste mixed into non-hazardous waste makes the whole mixture a listed waste. Under the derived-from rule, whatever comes out of treating a listed waste is still that listed waste. [[r]]Listed is sticky in a way that characteristic is not — a characteristic waste stops being hazardous once it no longer exhibits the characteristic, but a listed waste carries its code until somebody formally delists it.",
    reveals: [1, 27, 54],
    estimatedSeconds: 58,
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
