import audioMeta from "./audio-meta-02.json";

/**
 * Lesson 02 — Measuring progress: the uninstalled materials adjustment
 *
 * DRAFT. Not reviewed. Do not generate audio until a licensed CPA has read
 * the `narration` fields and the arithmetic below and signed off (4.01.1, 4.02).
 *
 * TWO CHANGES FROM lesson-01.ts — read these before mirroring the shape.
 *
 * 1. `figure` payload. Slides no longer know their own content. A block names
 *    a generic slide TYPE and hands it data. `Misconception` and `LegacyBranch`
 *    become `statement`. This is the change that lets an LLM emit a whole
 *    lesson without anyone hand-writing React.
 *
 * 2. Shorter blocks. Lesson 01 ran 43–94 seconds per sheet. These run 8–36.
 *    A viewer's attention resets roughly every 20–30 seconds regardless of how
 *    good the content is, and a new sheet is the cheapest possible reset.
 *    block-04 is ten seconds on purpose. Do not merge it into block-03.
 *
 * Reveal markers: [[r]] sits in `narration`, immediately before the WORD it
 * reveals — not at the start of the sentence. generate-audio.ts strips the
 * markers, reads their real timestamps out of the ElevenLabs alignment stream,
 * and writes them to audio-meta-02.json. No timing number belongs in this file
 * except as a fallback: `reveals` is a preview estimate, discarded the moment
 * audio exists.
 */

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
  estimatedSeconds: number;
  wordCount: number;
  narration: string; // transcript of record, may contain [[r]] markers
  reveals: number[]; // fallback seconds from block start, used until measured
};

export const meta = {
  courseCode: "ASC606-CON-01",
  courseTitle: "Revenue Recognition for Construction Contractors",
  lessonTitle: "Measuring Progress: The Uninstalled Materials Adjustment",
  revision: "A",
  revisionDate: "2026-08-21",
  status: "DRAFT — NOT REVIEWED",
  servesObjective: 3,
};

export const blocks: Block[] = [
  {
    id: "title",
    sheet: "S-00",
    citation: "ASC 606-10-55-21",
    slide: "Title",
    estimatedSeconds: 8,
    wordCount: 0,
    narration: "",
    reveals: [1, 3, 5],
  },

  {
    id: "block-01",
    sheet: "S-01",
    citation: "ASC 606-10",
    slide: "Facts",
    figure: {
      kind: "facts",
      rows: [
        { label: "Contract", value: "Municipal wastewater treatment plant" },
        { label: "Transaction price", value: "$10,000,000" },
        { label: "Estimated total cost", value: "$8,000,000" },
        { label: "Expected gross profit", value: "$2,000,000 (20%)" },
      ],
    },
    estimatedSeconds: 32,
    wordCount: 70,
    narration:
      "A general contractor signs a fixed-price contract to build a [[r]]municipal wastewater treatment plant. [[r]]Ten million dollars. The contractor estimates [[r]]total costs of eight million, so the job carries [[r]]two million of gross profit — twenty percent. The performance obligation is satisfied over time. That part is settled; we did it last lesson. The only question left is the one this lesson is about. How much of it is done?",
    reveals: [1, 10.3, 19.7, 29],
  },

  {
    id: "block-02",
    sheet: "S-02",
    citation: "ASC 606-10",
    slide: "Statement",
    figure: {
      kind: "statement",
      lines: [
        "Month 3 — standby generator delivered",
        "$2,000,000. Title passed. Owner insures it.",
        "Not installed. Not a bolt.",
      ],
    },
    estimatedSeconds: 28,
    wordCount: 61,
    narration:
      "Month three. A [[r]]standby generator arrives on site. Two million dollars — twenty-five percent of the entire cost budget — sitting on a gravel pad under a tarp. [[r]]Title has passed. It is the owner's generator now, the owner insures it, and if the contractor walked off the job tomorrow it would stay. Nobody has [[r]]installed anything. Not a bolt.",
    reveals: [1, 13, 25],
  },

  {
    id: "block-03",
    sheet: "S-03",
    citation: "Cost-to-cost, unadjusted",
    slide: "Calc",
    figure: {
      kind: "calc",
      rows: [
        { label: "Costs incurred to date", value: "$3,200,000" },
        { label: "Estimated total costs", value: "$8,000,000" },
        { label: "Progress", value: "40%", rule: true },
        { label: "Revenue (40% × $10,000,000)", value: "$4,000,000" },
        { label: "Costs", value: "(3,200,000)" },
        { label: "Gross profit", value: "$800,000", rule: true },
      ],
    },
    estimatedSeconds: 36,
    wordCount: 77,
    narration:
      "So the accountant opens the job cost report. [[r]]Costs incurred to date, three million two hundred thousand. [[r]]Estimated total costs, eight million. Divide. [[r]]Forty percent complete. Forty percent of ten million is [[r]]four million of revenue, against [[r]]three point two million of cost, and the job books [[r]]eight hundred thousand dollars of gross profit this quarter. Every input in that calculation came off a real ledger. The arithmetic is correct.",
    reveals: [1, 7.4, 13.8, 20.2, 26.6, 33],
  },

  {
    id: "block-04",
    sheet: "S-04",
    citation: "ASC 606-10-25-31",
    slide: "Statement",
    figure: {
      kind: "statement",
      lines: ["And the answer is wrong."],
    },
    estimatedSeconds: 10,
    wordCount: 21,
    narration:
      "And the answer is [[r]]wrong. Not by a rounding difference. The company just recognized twice the profit it earned.",
    reveals: [1],
  },

  {
    id: "block-05",
    sheet: "S-05",
    citation: "ASC 606-10-25-31",
    slide: "Statement",
    figure: {
      kind: "statement",
      lines: [
        "The objective is to depict the transfer of control.",
        "Not to depict spending.",
      ],
    },
    estimatedSeconds: 36,
    wordCount: 79,
    narration:
      "Here is the sentence that governs this. ASC 606-10-25-31: the objective when measuring progress is to depict the [[r]]transfer of control to the customer. [[r]]Not to depict spending. Cost-to-cost is popular because on most jobs spending is a fair proxy — you pour concrete, you pay for concrete, and the two move together. Buying a generator is not that. The contractor called a manufacturer and paid an invoice. What transferred to the customer? A generator. Nothing else.",
    reveals: [1, 33],
  },

  {
    id: "block-06",
    sheet: "S-06",
    citation: "ASC 606-10-55-21",
    slide: "List",
    figure: {
      kind: "list",
      items: [
        "Remove the cost from the measure of progress",
        "Recognize revenue on that item equal to its cost — zero margin",
      ],
    },
    estimatedSeconds: 29,
    wordCount: 62,
    narration:
      "So ASC 606-10-55-21 tells you to adjust the measure of progress when a cost is incurred that is not proportionate to progress. Uninstalled materials are the named example. The adjustment has two halves, and you have to do both. [[r]]Take the cost out of the measure of progress. [[r]]Then recognize revenue on that item equal to its cost. Zero margin.",
    reveals: [1, 26],
  },

  {
    id: "block-07",
    sheet: "S-07",
    citation: "ASC 606-10-55-21(b)",
    slide: "List",
    figure: {
      kind: "list",
      items: [
        "The good is not distinct from the rest of the contract",
        "The customer controls it well before the related services",
        "Its cost is significant relative to total expected costs",
        "The contractor procures it — does not design or manufacture it",
      ],
    },
    estimatedSeconds: 31,
    wordCount: 67,
    narration:
      "The zero-margin treatment applies when four conditions hold. [[r]]The good is not distinct from the rest of the contract. [[r]]The customer takes control of it significantly before receiving the services related to it. [[r]]Its cost is significant relative to total expected costs. And [[r]]the contractor procures the good rather than designing or manufacturing it. All four. Read them against the generator and every one lands.",
    reveals: [1, 10, 19, 28],
  },

  {
    id: "block-08",
    sheet: "S-08",
    citation: "Adjusted measure of progress",
    slide: "Calc",
    figure: {
      kind: "calc",
      rows: [
        { label: "Costs incurred to date", value: "$3,200,000" },
        { label: "Less: uninstalled generator", value: "(2,000,000)" },
        { label: "Adjusted costs incurred", value: "$1,200,000", rule: true },
        { label: "Estimated total costs", value: "$8,000,000" },
        { label: "Less: uninstalled generator", value: "(2,000,000)" },
        { label: "Adjusted total costs", value: "$6,000,000", rule: true },
        { label: "Progress", value: "20%", emphasis: "right", rule: true },
      ],
    },
    estimatedSeconds: 26,
    wordCount: 57,
    narration:
      "Now redo it. [[r]]Pull the two million out of costs incurred: one million two hundred thousand. [[r]]Then pull it out of estimated total costs as well — that is the half people forget — [[r]]six million. One point two over six is [[r]]twenty percent. The job is twenty percent complete, not forty.",
    reveals: [1, 8.3, 15.7, 23],
  },

  {
    id: "block-09",
    sheet: "S-09",
    citation: "Adjusted revenue",
    slide: "Calc",
    figure: {
      kind: "calc",
      rows: [
        { label: "Transaction price", value: "$10,000,000" },
        { label: "Less: generator", value: "(2,000,000)" },
        { label: "Subject to measure of progress", value: "$8,000,000", rule: true },
        { label: "20% × $8,000,000", value: "$1,600,000" },
        { label: "Generator, at cost", value: "2,000,000" },
        { label: "Revenue", value: "$3,600,000", rule: true },
        { label: "Costs", value: "(3,200,000)" },
        { label: "Gross profit", value: "$400,000", emphasis: "right", rule: true },
      ],
    },
    estimatedSeconds: 29,
    wordCount: 62,
    narration:
      "Revenue then comes in two pieces. [[r]]Twenty percent of the transaction price excluding the generator — twenty percent of eight million — is one million six hundred thousand. Then [[r]]the generator itself, at cost. Two million. Add them. [[r]]Three million six hundred thousand of revenue, against three point two million of cost. [[r]]Four hundred thousand of gross profit.",
    reveals: [1, 9.3, 17.7, 26],
  },

  {
    id: "block-10",
    sheet: "S-10",
    citation: "ASC 606-10-55-21",
    slide: "Compare",
    figure: {
      kind: "compare",
      columns: [
        {
          heading: "Unadjusted",
          emphasis: "wrong",
          rows: [
            { label: "Progress", value: "40%" },
            { label: "Revenue", value: "$4,000,000" },
            { label: "Gross profit", value: "$800,000" },
          ],
        },
        {
          heading: "Adjusted",
          emphasis: "right",
          rows: [
            { label: "Progress", value: "20%" },
            { label: "Revenue", value: "$3,600,000" },
            { label: "Gross profit", value: "$400,000" },
          ],
        },
      ],
    },
    estimatedSeconds: 30,
    wordCount: 65,
    narration:
      "[[r]]Eight hundred thousand, or [[r]]four hundred thousand. Same contract, same ledger, same quarter. The difference is four hundred thousand dollars of margin the contractor would have booked for making a phone call to a generator manufacturer. It does come back. Total profit on the job does not change. But it comes back in the periods where the contractor actually earns it.",
    reveals: [1, 27],
  },

  {
    id: "block-11",
    sheet: "S-11",
    citation: "ASC 606-10-55-21",
    slide: "Statement",
    figure: {
      kind: "statement",
      lines: ["Both sides of the fraction. Every time."],
    },
    estimatedSeconds: 34,
    wordCount: 73,
    narration:
      "This is the most commonly missed calculation in construction revenue recognition, and it is missed in a specific way. Contractors remember to strip the cost out of the numerator and leave it in the denominator. That produces a number that is wrong in the other direction. [[r]]Both sides of the fraction, every time. Next lesson we go back to something we have now assumed twice without examining. What exactly is the performance obligation you are measuring progress on?",
    reveals: [1],
  },
];

type BlockMeta = { durationSeconds: number; reveals: number[]; hash: string };
const audio = audioMeta as Record<string, BlockMeta>;

/** The transcript of record: markers stripped, nothing else changed. */
export const transcriptOf = (b: Block): string =>
  b.narration.replace(/\s*\[\[r\]\]\s*/g, " ").replace(/\s+/g, " ").trim();

/** What gets sent to ElevenLabs. Markers intact; the script strips them. */
export const speechOf = (b: Block): string => b.narration;

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
