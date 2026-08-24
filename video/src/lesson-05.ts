/**
 * Lesson 05 — "Not Making It in the First Place"
 * Course: Where Does It Actually Go? (hazardous waste, ESG/Sustainability)
 *
 * STATUS: DRAFT — NOT REVIEWED. Clear `meta.status` once a subject matter
 * expert has read the narration (4.01.1, 4.02), then re-render. Clearing the
 * stamp does not require regenerating audio.
 *
 * Maps to learning objective 5. One assessment question is tagged to this
 * objective — the fewest of any lesson — but this is also the lesson that
 * closes the course, so blocks 01, 02, and 09 carry the arc back through
 * lessons 1–4 explicitly.
 *
 * NINE narrated blocks, not eight. This is deliberate and it is a credit
 * decision, not an editorial one: 1.2 credits requires 32.25 minutes of A/V
 * against 27.75 minutes contributed by the 15 questions. Lessons 01–04 run
 * roughly 25.6 minutes, leaving 6:39 for this lesson. An eight-block lesson
 * lands near 6:35 and 7.02.7 rounds DOWN, which would cost 0.2 credits over
 * four seconds. Verify against the real ffprobe numbers for 01–04 before
 * accepting this; if they came in longer than assumed, block-07 is the one to
 * cut — it is the least load-bearing for objective 5.
 *
 * SLIDE NOTE: block 02 is the pollution prevention hierarchy and genuinely
 * wants the `Hierarchy` component — the inverted pyramid IS the pedagogy, and
 * a flat list deletes the argument that disposal ranks last. It is authored as
 * a numbered `List` so this can ship. When `Hierarchy` lands, swapping that
 * one figure is a re-render only; narration and reveal count are unaffected.
 *
 * Types are imported from lesson-01, which is the single definition point.
 *
 * Reveal markers: [[r]] sits in `narration`, immediately before the WORD it
 * reveals. Marker count MUST equal `reveals` length. Verify with
 * `npm run generate -- --lesson 05 --dry-run` before spending any credit.
 */

import audioMeta from "./audio-meta-05.json";
import type { Block } from "./lesson-01";

export type { Block, Figure } from "./lesson-01";

export const meta = {
  lessonId: "05",
  courseCode: "HAZWASTE-05",
  courseTitle: "Where Does It Actually Go?",
  lessonTitle: "Not Making It in the First Place",
  title: "Not Making It in the First Place",
  subtitle: "The waste hierarchy, green chemistry, and the cheapest pound of all",
  eyebrow: "Lesson 05",
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
    citation: "42 U.S.C. §13101",
    slide: "Statement",
    figure: {
      kind: "statement",
      lines: [
        "The Pollution Prevention Act of 1990",
        "A ranking, not a menu",
        "Disposal is the last resort, by statute",
      ],
    },
    narration:
      "Four lessons have followed hazardous waste from the moment it becomes a legal category to the moment somebody pays to clean it up. This one runs the film backward and asks the only question that makes any of it cheaper: what if it were never made. That is not a sentiment, it is federal policy. The [[r]]Pollution Prevention Act of nineteen ninety established a national hierarchy for how waste should be handled, and the crucial thing about that hierarchy is that it is a [[r]]ranking rather than a menu. You do not get to pick the tier you prefer. You work from the top and you move down only when the tier above is genuinely unavailable. [[r]]Disposal — the manifests, the permitted facilities, the landfills of lesson three — sits at the bottom, described in the statute itself as a last resort.",
    reveals: [1, 32, 63],
    estimatedSeconds: 66,
  },

  {
    id: "block-02",
    sheet: "S-02",
    citation: "42 U.S.C. §13101(b)",
    slide: "List",
    figure: {
      kind: "list",
      items: [
        "1. Source reduction — do not create the waste",
        "2. Recycling — use it again, safely",
        "3. Treatment — render it less hazardous",
        "4. Disposal or release — last resort",
      ],
    },
    narration:
      "Here is the hierarchy in order, and the order is the whole argument. First, [[r]]source reduction: prevent the waste from existing at all, by changing what goes into the process or how the process runs. Second, where waste is unavoidable, [[r]]recycling — use it again in an environmentally safe manner, either in your own operation or someone else's. Third, [[r]]treatment: if it cannot be reused, render it less hazardous, less mobile, or smaller in volume before it goes anywhere. And only then, fourth, [[r]]disposal or release into the environment. Notice where this course has been. Everything you have learned so far lives in tiers three and four. The regulatory apparatus is enormous and expensive, and it governs the bottom two rungs of a four-rung ladder.",
    reveals: [1, 19, 37, 55],
    estimatedSeconds: 58,
  },

  {
    id: "block-03",
    sheet: "S-03",
    citation: "42 U.S.C. §13102(5)",
    slide: "Facts",
    figure: {
      kind: "facts",
      rows: [
        { label: "Input substitution", value: "Use a less hazardous material" },
        { label: "Process change", value: "Redesign the operation to produce less" },
        { label: "Better housekeeping", value: "Prevent leaks, spills, and mixing" },
        { label: "Product reformulation", value: "Change what you sell, not just how" },
      ],
    },
    narration:
      "Source reduction sounds abstract until you break it into the four things it actually means on a shop floor. [[r]]Input substitution is replacing a hazardous raw material with a less hazardous one that does the same job. [[r]]Process change is redesigning the operation so it generates less — closed systems, tighter tolerances, a different sequence of steps. [[r]]Better housekeeping is the least glamorous and frequently the largest: preventing leaks and spills, and not mixing a small volume of hazardous waste into a large volume of non-hazardous waste, which contaminates the entire drum and converts cheap disposal into expensive disposal. And [[r]]product reformulation changes what you sell rather than merely how you make it. None of these four is a treatment technology. They are all decisions made before anything is mixed.",
    reveals: [1, 20, 38, 57],
    estimatedSeconds: 60,
  },

  {
    id: "block-04",
    sheet: "S-04",
    citation: "EPA Green Chemistry Challenge Awards",
    slide: "List",
    figure: {
      kind: "list",
      items: [
        "Aqueous cleaning replacing chlorinated degreasing",
        "Supercritical CO2 replacing perchloroethylene",
        "Water-based coatings replacing solvent-based",
        "On-site distillation returning solvent to the process",
      ],
    },
    narration:
      "These are not hypotheticals. [[r]]Aqueous and semi-aqueous cleaning has replaced chlorinated solvent degreasing across much of metal fabrication, removing an F zero zero one listed waste from the process entirely — a waste that would otherwise be manifested for the rest of that operation's life. [[r]]Supercritical carbon dioxide and hydrocarbon systems have displaced perchloroethylene across a large share of dry cleaning. [[r]]Water-based and powder coatings have replaced solvent-based coatings in furniture and automotive finishing, cutting hazardous waste and air emissions together. And [[r]]on-site distillation lets a shop recover its own solvent and return it to the process — technically tier two rather than tier one, but it converts a recurring disposal cost into a one-time piece of capital equipment, which is a very different line on a budget.",
    reveals: [1, 19, 38, 56],
    estimatedSeconds: 59,
  },

  {
    id: "block-05",
    sheet: "S-05",
    citation: "Anastas & Warner, Green Chemistry: Theory and Practice (1998)",
    slide: "Statement",
    figure: {
      kind: "statement",
      lines: [
        "Green chemistry: design the hazard out",
        "Twelve principles, published 1998",
        "Control is a recurring cost; absence is not",
      ],
    },
    narration:
      "The formal discipline behind tier one is [[r]]green chemistry, and its central claim is worth stating precisely: hazard is a design property, not an operating condition. Conventional environmental practice takes a hazardous process as given and controls exposure to it — containment, ventilation, protective equipment, permits, manifests. Green chemistry asks whether the hazard needs to be in the design at all. The [[r]]twelve principles published in nineteen ninety-eight formalize that: prevent waste rather than treat it, design syntheses that incorporate their inputs into the final product, use safer solvents, design products to degrade after use. And the economic argument is blunt. [[r]]Control is a permanent cost that recurs every year and can fail. Absence cannot fail, and it costs nothing to maintain.",
    reveals: [1, 27, 53],
    estimatedSeconds: 56,
  },

  {
    id: "block-06",
    sheet: "S-06",
    citation: "42 U.S.C. §9607(a)(3)",
    slide: "Facts",
    figure: {
      kind: "facts",
      rows: [
        { label: "First price", value: "You bought it as raw material" },
        { label: "Second price", value: "You pay to manifest and dispose of it" },
        { label: "Third price", value: "Arranger liability that does not expire" },
        { label: "So read a manifest as", value: "Purchased inventory that never became product" },
      ],
    },
    narration:
      "Now the accounting, because this is where the argument stops being environmental and becomes financial. Every pound of hazardous waste leaving your dock was paid for [[r]]once already, as raw material, on a purchase order. You then pay for it a [[r]]second time — in drums, transportation, manifest fees, and disposal charges that scale with quantity. And you carry a [[r]]third exposure with no expiration date: the arranger liability from lesson four, strict and retroactive, attaching to that shipment for as long as the receiving site exists. So the correct way to read a waste manifest is as a [[r]]record of purchased inventory that never became product. That reframing is what moves source reduction out of the environmental department and into the operating budget, which is where decisions actually get made.",
    reveals: [1, 20, 38, 57],
    estimatedSeconds: 60,
  },

  {
    id: "block-07",
    sheet: "S-07",
    citation: "42 U.S.C. §11023; 42 U.S.C. §13106",
    slide: "List",
    figure: {
      kind: "list",
      items: [
        "TRI reporting under EPCRA §313",
        "Form R must report source reduction activities",
        "Public and comparable across facilities",
        "You cannot reduce what you do not count",
      ],
    },
    narration:
      "None of this happens without measurement, which is what the [[r]]Toxics Release Inventory is for. Under section three thirteen of the Emergency Planning and Community Right-to-Know Act, facilities above certain thresholds report annually on the listed chemicals they release and manage. The Pollution Prevention Act then added a requirement that [[r]]Form R also report source reduction activities — so the filing is not merely how much left the site, but what was done to make less of it. The data is [[r]]public, searchable, and comparable across facilities in the same industry, and that was the actual mechanism at work: the statute did not mandate reductions, it mandated disclosure, and disclosure moved the numbers. The underlying principle is unglamorous and reliable. [[r]]You cannot reduce what you do not count.",
    reveals: [1, 19, 38, 56],
    estimatedSeconds: 59,
  },

  {
    id: "block-08",
    sheet: "S-08",
    citation: "40 CFR §261.4(b)(1); 40 CFR Part 273",
    slide: "List",
    figure: {
      kind: "list",
      items: [
        "Buy the quantity you will actually use",
        "Choose the least hazardous product that works",
        "Use collection days and retailer take-back",
        "Never the drain, the storm sewer, or the trash",
      ],
    },
    narration:
      "Which brings it home, literally. Lesson two established that household hazardous waste is excluded from the program entirely — no manifest, no obligation, nothing. That means the hierarchy is the only thing operating in a garage, and it applies unchanged. [[r]]Buy the quantity you will actually use, because a half-used container of pesticide is a disposal problem you paid full price to create. [[r]]Choose the least hazardous product that does the job. Use the [[r]]municipal collection day and retailer take-back programs for batteries, fluorescent lamps, and electronics — the same streams lesson two identified as universal waste on the commercial side. And [[r]]never the drain, the storm sewer, or the household trash. A storm drain in most towns discharges to surface water with no treatment whatsoever.",
    reveals: [1, 19, 37, 55],
    estimatedSeconds: 58,
  },

  {
    id: "block-09",
    sheet: "S-09",
    citation: "42 U.S.C. §13101(b)",
    slide: "Statement",
    figure: {
      kind: "statement",
      lines: [
        "The manifest exists because prevention did not",
        "Superfund exists because the manifest did not",
        "The cheapest pound is the one never generated",
      ],
    },
    narration:
      "So here is the whole course in three sentences, read from the bottom up. [[r]]The manifest system of lesson three exists because waste got made that nobody prevented. [[r]]Superfund and Love Canal exist because waste got buried before any manifest system existed to track it. And the four characteristics and the listings of lesson one are a legal apparatus built entirely to identify material that somebody already produced, already purchased, and now has to account for. Every layer of this is downstream of a decision made earlier and made cheaper. [[r]]The least expensive pound of hazardous waste, by an enormous margin, is the one that was never generated. That is not a slogan. It is the ranking Congress wrote into statute in nineteen ninety, and it is why this course ends here rather than at the landfill.",
    reveals: [1, 30, 60],
    estimatedSeconds: 63,
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
