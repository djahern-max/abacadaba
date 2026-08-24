/**
 * Lesson 02 — "Who Makes It, and How Much"
 * Course: Where Does It Actually Go? (hazardous waste, ESG/Sustainability)
 *
 * STATUS: DRAFT — NOT REVIEWED. Clear `meta.status` once a subject matter
 * expert has read the narration (4.01.1, 4.02), then re-render. Clearing the
 * stamp does not require regenerating audio.
 *
 * Types are imported from lesson-01, which is the single definition point.
 * Do not redefine Block or Figure here — two copies will drift.
 *
 * Duration resolution order: audio-meta-02.json first, estimatedSeconds
 * second. `estimatedSeconds` is Math.round(wordCount / 130 * 60). Note that
 * lesson 01 measured at roughly 163 wpm against this 130 wpm constant, so
 * these estimates run long by about a quarter. That is harmless — measured
 * duration always wins, and no estimate may reach a credit calculation
 * (7.02.7).
 *
 * Reveal markers: [[r]] sits in `narration`, immediately before the WORD it
 * reveals. The number of markers in a block MUST equal the length of that
 * block's `reveals` array, or the slide indexes `undefined` and the element
 * never appears. Verify with `npm run generate -- --lesson 02 --dry-run`
 * before spending any API credit.
 */

import audioMeta from "./audio-meta-02.json";
import type { Block } from "./lesson-01";

export type { Block, Figure } from "./lesson-01";

export const meta = {
  lessonId: "02",
  courseCode: "HAZWASTE-02",
  courseTitle: "Where Does It Actually Go?",
  lessonTitle: "Who Makes It, and How Much",
  title: "Who Makes It, and How Much",
  subtitle: "Generator categories and the volume that sets them",
  eyebrow: "Lesson 02",
  fieldOfStudy: "ESG/Sustainability",
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
    citation: "40 CFR §262.13",
    slide: "Statement",
    figure: {
      kind: "statement",
      lines: [
        "Counted per calendar month, per site",
        "Three categories, set by weight",
        "Your category sets every other obligation",
      ],
    },
    narration:
      "Last lesson asked what makes a waste hazardous. This one asks a different question, and it is the question that actually determines what you have to do about it: [[r]]how much of it do you make. Hazardous waste regulation is scaled to volume. A dental office producing a few kilograms of amalgam waste a month is not held to the standard a refinery is, and that is deliberate. The counting is done [[r]]per calendar month and per site — not per year, not per company. Which of [[r]]three categories you land in that month determines whether you need an identification number, whether you need a manifest, how long you may store the waste, and what training your people need.",
    reveals: [1, 26, 52],
    estimatedSeconds: 55,
  },

  {
    id: "block-02",
    sheet: "S-02",
    citation: "40 CFR §262.14",
    slide: "Facts",
    figure: {
      kind: "facts",
      rows: [
        { label: "Category", value: "Very Small Quantity Generator (VSQG)" },
        { label: "Threshold", value: "100 kg or less per month (~220 lb)" },
        { label: "EPA ID number", value: "Not required" },
        { label: "Storage limit", value: "1,000 kg on site at any time" },
      ],
    },
    narration:
      "The smallest category is the [[r]]very small quantity generator, and most businesses in the country sit here. The line is [[r]]one hundred kilograms a month — about two hundred twenty pounds, which is roughly half a fifty-five gallon drum. Below that line the obligations are remarkably light. [[r]]No EPA identification number. No manifest in most states. No accumulation time limit at all. What you do have is a duty to send the waste to a facility permitted to receive it, and a [[r]]cap of one thousand kilograms on site at any one time. Many small generators never learn they are regulated at all, because at this level the regulation barely touches them.",
    reveals: [1, 17, 33, 49],
    estimatedSeconds: 52,
  },

  {
    id: "block-03",
    sheet: "S-03",
    citation: "40 CFR §262.16",
    slide: "Facts",
    figure: {
      kind: "facts",
      rows: [
        { label: "Category", value: "Small Quantity Generator (SQG)" },
        { label: "Threshold", value: "More than 100, less than 1,000 kg/month" },
        { label: "Accumulation", value: "180 days (270 if TSDF over 200 miles)" },
        { label: "Storage limit", value: "6,000 kg on site" },
      ],
    },
    narration:
      "Cross one hundred kilograms and you become a [[r]]small quantity generator, and the obligations arrive all at once. You need an EPA identification number. Every shipment needs a manifest. You may accumulate waste for [[r]]one hundred eighty days, extended to two hundred seventy if your disposal facility is more than two hundred miles away — and that extension exists because rural generators would otherwise be forced into uneconomical partial shipments. You may hold [[r]]six thousand kilograms on site. You need a designated emergency coordinator, and your people need basic training in handling and response. Since the twenty sixteen Generator Improvements Rule you also have to [[r]]re-notify the agency every four years, which is the requirement most commonly missed.",
    reveals: [1, 18, 34, 51],
    estimatedSeconds: 54,
  },

  {
    id: "block-04",
    sheet: "S-04",
    citation: "40 CFR §262.17",
    slide: "Facts",
    figure: {
      kind: "facts",
      rows: [
        { label: "Category", value: "Large Quantity Generator (LQG)" },
        { label: "Threshold", value: "1,000 kg or more per month" },
        { label: "Acute waste", value: "More than 1 kg/month — LQG regardless" },
        { label: "Accumulation", value: "90 days, no quantity limit" },
      ],
    },
    narration:
      "At [[r]]one thousand kilograms a month you become a large quantity generator, and here the program applies in full. Accumulation drops to [[r]]ninety days, though there is no limit on how much you may hold within that window. Personnel training becomes formal and annual. You need a written contingency plan with a quick reference guide for emergency responders, and you file a biennial report by the first of March in even years. But note the [[r]]second trigger, because it catches people who are nowhere near a thousand kilograms: more than [[r]]one kilogram a month of acutely hazardous waste — the P list from lesson one — makes you a large quantity generator no matter what your total volume is. One kilogram is about two pounds.",
    reveals: [1, 19, 37, 55],
    estimatedSeconds: 58,
  },

  {
    id: "block-05",
    sheet: "S-05",
    citation: "EPA National Biennial RCRA Hazardous Waste Report",
    slide: "List",
    figure: {
      kind: "list",
      items: [
        "Chemical manufacturing and petroleum refining",
        "Metal finishing, plating, and fabrication",
        "Printing, coating, and dry cleaning",
        "Motor vehicle repair and maintenance",
      ],
    },
    narration:
      "So who actually generates it. By tonnage the answer is concentrated: [[r]]chemical manufacturing and petroleum refining together account for the majority of hazardous waste generated in the United States, and a relatively small number of facilities produce most of it. But by number of generators the picture inverts. [[r]]Metal finishing and plating shops, [[r]]printers, coating operations, and dry cleaners, and [[r]]motor vehicle repair shops — these are small businesses, they are everywhere, and collectively they are where most enforcement activity happens. Not because they are careless, but because the obligations are unfamiliar and the volume thresholds are easy to cross without noticing.",
    reveals: [1, 15, 30, 44],
    estimatedSeconds: 47,
  },

  {
    id: "block-06",
    sheet: "S-06",
    citation: "40 CFR §261.4(b)(1)",
    slide: "Statement",
    figure: {
      kind: "statement",
      lines: [
        "Household waste is excluded from Subtitle C entirely",
        "Same solvent, same drain — different rule",
        "The exclusion is a policy choice, not a safety finding",
      ],
    },
    narration:
      "Now the part that surprises nearly everyone. [[r]]Household hazardous waste is excluded from the hazardous waste program altogether. The identical can of paint thinner that is a regulated D zero zero one waste in a body shop is [[r]]not regulated waste when it comes out of a garage. The exclusion covers residences, and also hotels, campgrounds, and day-use recreation areas. This is not a finding that household chemicals are safe. [[r]]It is a policy judgment that manifesting waste from a hundred and thirty million homes is not administrable. The consequence is that household hazardous waste is managed by collection programs and voluntary participation rather than by legal obligation — which is why your town holds a collection day rather than sending you a manifest.",
    reveals: [1, 28, 54],
    estimatedSeconds: 57,
  },

  {
    id: "block-07",
    sheet: "S-07",
    citation: "40 CFR Part 273",
    slide: "List",
    figure: {
      kind: "list",
      items: [
        "Batteries",
        "Pesticides",
        "Mercury-containing equipment and lamps",
        "Aerosol cans (added 2019)",
      ],
    },
    narration:
      "Between full regulation and no regulation sits a middle path called universal waste, and it exists because some hazardous wastes are generated in small amounts almost everywhere. Four streams qualify. [[r]]Batteries. [[r]]Pesticides. [[r]]Mercury-containing equipment and lamps, which covers thermostats and fluorescent tubes. And [[r]]aerosol cans, added in twenty nineteen. Universal waste can be accumulated for a year, needs no manifest, and does not count toward your generator category — which is the point. It keeps a school district that changes out fluorescent tubes from being pushed into small quantity generator status by a lighting retrofit. The tradeoff is that it must go to a handler or destination facility, not to a landfill.",
    reveals: [1, 17, 33, 49],
    estimatedSeconds: 52,
  },

  {
    id: "block-08",
    sheet: "S-08",
    citation: "40 CFR §§262.13, 262.232",
    slide: "Statement",
    figure: {
      kind: "statement",
      lines: [
        "Count every month — category can change",
        "One episodic event per year is allowed",
        "The category is a floor, not a ceiling",
      ],
    },
    narration:
      "Two closing rules that matter in practice. First, [[r]]your category is recalculated every month, not assigned once. A shop that is normally a very small quantity generator becomes a small quantity generator in the month it clears out a storage room, and the obligations attach to that month. Second, the twenty sixteen rule added relief for exactly that situation: [[r]]one planned or unplanned episodic event per year may be managed under your normal category, provided you notify in advance and meet the conditions. And third, worth saying plainly — [[r]]nothing stops you from operating to a higher standard than your category requires. Many generators manifest everything regardless, because one consistent procedure is cheaper to run than three.",
    reveals: [1, 26, 51],
    estimatedSeconds: 54,
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
