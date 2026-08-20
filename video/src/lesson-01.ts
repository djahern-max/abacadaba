import measured from "./durations.json";

/**
 * Lesson content as data, not as markup.
 *
 * This file is the handoff point between the writing pipeline and the video
 * pipeline. When script generation is automated, this is the shape it emits —
 * so keep it free of anything React-specific.
 *
 * durationSeconds resolution order:
 *   1. durations.json, written by `npm run measure` from the real audio files
 *   2. estimatedSeconds, from word count at ~145 wpm
 *
 * Estimates let you render and judge the visuals before spending TTS credits.
 * They are not accurate enough to ship: the credit calculation depends on
 * actual runtime, so measure before you publish.
 */

export type Block = {
  id: string;
  sheet: string;          // sheet number in the drawing set
  citation: string;       // ASC paragraph shown in the title block
  slide: string;          // which slide component renders this block
  estimatedSeconds: number;
  wordCount: number;
  narration: string;      // transcript of record — plain, for the record
  reveals: number[];      // seconds from block start at which items appear
};

export const meta = {
  courseCode: "ASC606-CON-01",
  courseTitle: "Revenue Recognition for Construction Contractors",
  lessonTitle: "Why Percentage of Completion Is No Longer a Method",
  revision: "A",
  revisionDate: "2026-08-19",
  status: "DRAFT — NOT REVIEWED",
};

export const blocks: Block[] = [
  {
    id: "title",
    sheet: "S-00",
    citation: "ASC 606-10",
    slide: "Title",
    estimatedSeconds: 8,
    wordCount: 0,
    narration: "",
    reveals: [0.4, 1.6, 2.8],
  },
  {
    id: "block-01",
    sheet: "S-01",
    citation: "ASC 606-10",
    slide: "Misconception",
    estimatedSeconds: 43,
    wordCount: 105,
    narration:
      "If you work with construction contractors, you have said the phrase percentage of completion a thousand times. Your clients say it. Their bonding companies say it. It shows up in loan covenants and on the face of financial statements. Here is the problem. Under ASC 606, percentage of completion is not an accounting method. It stopped being one. That is not a technicality, and it is not a name change. The old method was a single decision — use it, or use completed contract. What replaced it is a sequence of separate judgments, and each one can go a different way than you expect. Let me show you where the judgments are.",
    reveals: [1, 14, 26],
  },
  {
    id: "block-02",
    sheet: "S-02",
    citation: "ASC 605-35",
    slide: "LegacyBranch",
    estimatedSeconds: 54,
    wordCount: 130,
    narration:
      "Before ASC 606, construction accounting lived in its own neighborhood. ASC 605-35 gave contractors a purpose-built model, and the central question was which of two methods you qualified for. Percentage of completion, if you could make dependable estimates. Completed contract, if you could not. Once you chose percentage of completion, the machinery followed: measure progress, usually with cost-to-cost, recognize revenue and gross profit in proportion, and carry the difference between what you had earned and what you had billed as costs in excess of billings, or billings in excess of costs. Every contractor's balance sheet had those two lines. Every surety underwriter knew how to read them. ASC 606 took that neighborhood apart. Not because it was wrong — because it was separate.",
    reveals: [2, 10, 20, 34, 46],
  },
  {
    id: "block-03",
    sheet: "S-03",
    citation: "ASC 606-10-05-4",
    slide: "FiveSteps",
    estimatedSeconds: 50,
    wordCount: 120,
    narration:
      "The whole purpose of ASC 606 was to replace industry-specific revenue guidance with one model that applies to everyone. A software company, a franchisor, a general contractor, a hospital. One framework, five steps. That is genuinely useful. It also means construction lost its custom-fit model and got a general-purpose one, and the general-purpose one asks questions the old model never asked. The five steps are: identify the contract with the customer. Identify the performance obligations in the contract. Determine the transaction price. Allocate the transaction price to the performance obligations. And recognize revenue when — or as — the entity satisfies a performance obligation. Hold on to that last phrase. When, or as. Four words that carry the entire question.",
    reveals: [22, 25, 28, 31, 34, 43],
  },
  {
    id: "block-04",
    sheet: "S-04",
    citation: "ASC 606-10-25-27",
    slide: "Fork",
    estimatedSeconds: 72,
    wordCount: 175,
    narration:
      "Step five is where contractors feel the change, so let's be precise about what it does. Step five asks whether a performance obligation is satisfied over time or at a point in time. Point in time is the default. Over time is the exception, and you have to earn it. Notice what that is not. It is not a choice. You do not elect over-time recognition because it produces better financial statements, or because it is what you have always done, or because your bank expects it. You test the performance obligation against criteria in the standard, and the criteria decide. ASC 606-10-25-27 gives three criteria. Meeting any one of them means the obligation is satisfied over time. Fail all three, and revenue goes at a point in time — which for a two-year construction contract would mean nothing until the end. Most construction contracts do meet one of them. But most is doing real work in that sentence, and the exceptions are where practitioners get surprised.",
    reveals: [6, 12, 18, 30, 48],
  },
  {
    id: "block-05",
    sheet: "S-05",
    citation: "ASC 606-10-25-27(a)-(c)",
    slide: "Criteria",
    estimatedSeconds: 85,
    wordCount: 205,
    narration:
      "The three criteria in 25-27, briefly. The first: the customer simultaneously receives and consumes the benefits as you perform. That fits routine services — a monthly cleaning contract. It rarely fits construction, because nobody consumes a half-built bridge. The second: your performance creates or enhances an asset the customer controls as it is created. This one fits construction on the customer's own land, and it is often the cleanest fit for a general contractor building on an owner's site. The third: your performance creates an asset with no alternative use to you, and you have an enforceable right to payment for performance completed to date. This is the criterion most construction contracts land on, and it is the one worth memorizing, because both halves have to hold. No alternative use means you could not practically redirect the asset to another customer. A custom facility, yes. Speculative homes built to a standard plan, often no. Enforceable right to payment means that if the customer terminated for convenience tomorrow, you could enforce payment for work performed plus a reasonable margin — not just recover your costs. That is a contract-terms question, and it is jurisdiction-specific.",
    reveals: [4, 20, 36, 52, 66],
  },
  {
    id: "block-06",
    sheet: "S-06",
    citation: "ASC 606-10-55-16",
    slide: "Methods",
    estimatedSeconds: 77,
    wordCount: 185,
    narration:
      "Now the part that gets collapsed most often. Concluding that a performance obligation is satisfied over time does not tell you how much revenue to recognize. That is a second, separate decision: selecting a method to measure progress toward complete satisfaction of the obligation. ASC 606 offers input methods and output methods. Input methods measure your efforts — costs incurred, labor hours, machine hours. Output methods measure results — units delivered, milestones reached, surveys of performance completed. Cost-to-cost is an input method. It is the one most contractors use, and if you have been doing percentage of completion by cost-to-cost, your spreadsheet may barely change. But the reasoning underneath it changed completely, and that matters when the facts get unusual. You are no longer applying a method you elected. You are selecting a measure that faithfully depicts your progress toward transferring control — and the standard will tell you, in specific circumstances, that your familiar cost-to-cost measure does not depict it faithfully and must be adjusted. Uninstalled materials is the clearest example. That is lesson three.",
    reveals: [4, 16, 28, 40, 62],
  },
  {
    id: "block-07",
    sheet: "S-07",
    citation: "ASC 606-10-25-27 / 55-16",
    slide: "Summary",
    estimatedSeconds: 50,
    wordCount: 120,
    narration:
      "So here is the shape of it. Percentage of completion was one method you elected. What replaced it is two sequential judgments: first, does this performance obligation qualify for over-time recognition under one of the three criteria — and second, what measure of progress faithfully depicts the transfer of control. Same spreadsheet, often. Different reasoning, always. And when a contract is unusual — an odd termination clause, a spec build, a large equipment purchase sitting on site — the two judgments can pull apart in ways the old single election never could. Next lesson, we go back a step, to the question that has to be answered before either of these: what exactly is the performance obligation in a construction contract?",
    reveals: [6, 18, 34],
  },
];

const measuredMap = measured as Record<string, number>;

export const durationOf = (block: Block): number =>
  measuredMap[block.id] ?? block.estimatedSeconds;

export const usingEstimates = blocks.some((b) => measuredMap[b.id] === undefined);

export const totalSeconds = blocks.reduce((sum, b) => sum + durationOf(b), 0);
