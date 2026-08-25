/**
 * Lesson 03 — "Cradle to Grave"
 * Course: Where Does It Actually Go? (hazardous waste, ESG/Sustainability)
 *
 * STATUS: DRAFT — NOT REVIEWED. Clear `meta.status` once a subject matter
 * expert has read the narration (4.01.1, 4.02), then re-render. Clearing the
 * stamp does not require regenerating audio.
 *
 * Maps to learning objective 3: trace a shipment of hazardous waste through
 * the cradle-to-grave manifest system from generator to treatment, storage,
 * or disposal facility. Two assessment questions are tagged to this objective,
 * so the narration must actually teach the chain of custody and the exception
 * report clock.
 *
 * SLIDE NOTE: the manifest chain wants a `Flow` component, which does not
 * exist yet. Blocks 04 and 07 are authored as ordered `List` figures instead.
 * When `Flow` lands, those two figures can be swapped without touching the
 * narration or the audio — reveal counts stay the same.
 *
 * Types are imported from lesson-01, which is the single definition point.
 * Do not redefine Block or Figure here — two copies will drift.
 *
 * Reveal markers: [[r]] sits in `narration`, immediately before the WORD it
 * reveals. The number of markers in a block MUST equal the length of that
 * block's `reveals` array. Verify with
 * `npm run generate -- --lesson 03 --dry-run` before spending any credit.
 */

import audioMeta from "./audio-meta-03.json";
import type { Block } from "./lesson-01";

export type { Block, Figure } from "./lesson-01";

export const meta = {
  lessonId: "03",
  courseCode: "HAZWASTE-03",
  courseTitle: "Where Does It Actually Go?",
  lessonTitle: "Cradle to Grave",
  title: "Cradle to Grave",
  subtitle: "The manifest, the chain of custody, and the copy that comes back",
  eyebrow: "Lesson 03",
  position: "Lesson 3 of 5",
  deliveryMethod: "Self study",
  fieldOfStudy: "ESG/Sustainability",
  revision: "A",
  revisionDate: "2026-08-24",
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
    citation: "40 CFR Part 262, Subpart B",
    slide: "Statement",
    figure: {
      kind: "statement",
      lines: [
        "One shipment, one tracking number",
        "Every custodian signs",
        "The paperwork comes back — or you report it",
      ],
    },
    narration:
      "Lesson two settled who you are. This lesson follows the waste out the door. Cradle to grave is not a slogan; it is a description of a document. When hazardous waste leaves your site it travels under a [[r]]single tracking number that stays with it from your loading dock to its final resting place. At every handoff, [[r]]each person who takes custody signs for it — you, the transporter, and the facility that finally treats or disposes of it. And critically, the signed record [[r]]comes back to you. If it does not come back within a set number of days, you have a reporting obligation. That return path is what makes the system cradle to grave rather than cradle to gate.",
    reveals: [1, 27, 53],
    estimatedSeconds: 56,
  },

  {
    id: "block-02",
    sheet: "S-02",
    citation: "40 CFR §§262.30–262.33; 49 CFR Parts 172–180",
    slide: "List",
    figure: {
      kind: "list",
      items: [
        "Containers in good condition, compatible with the waste",
        'Marked "Hazardous Waste" with the accumulation start date',
        "DOT packaging, labeling, marking, and placarding",
        "Land disposal restriction notification prepared",
      ],
    },
    narration:
      "Nothing moves until the waste is ready to move, and four things have to be true before a truck arrives. The [[r]]containers must be in good condition and made of material compatible with what is inside them — no corrosive in bare steel, no solvent in a container it will soften. Each one must be [[r]]marked with the words hazardous waste and with the date accumulation started, because that date is what an inspector counts your ninety or one hundred eighty days from. The shipment must meet [[r]]Department of Transportation rules for packaging, labeling, marking, and placarding, which are a separate body of law in title forty-nine. And a [[r]]land disposal restriction notification has to travel with it, telling the receiving facility which treatment standard applies before the waste can go into the ground.",
    reveals: [1, 20, 40, 59],
    estimatedSeconds: 62,
  },

  {
    id: "block-03",
    sheet: "S-03",
    citation: "40 CFR §262.20; EPA Form 8700-22",
    slide: "Facts",
    figure: {
      kind: "facts",
      rows: [
        { label: "Form", value: "EPA 8700-22, Uniform Hazardous Waste Manifest" },
        { label: "Tracking number", value: "Unique, printed on every copy" },
        { label: "Names three parties", value: "Generator, transporter(s), designated facility" },
        { label: "Describes the waste", value: "Shipping name, waste codes, quantity, containers" },
      ],
    },
    narration:
      "The document itself is [[r]]EPA Form eight seven zero zero dash twenty-two, the Uniform Hazardous Waste Manifest. Uniform is the operative word — before the form was standardized, states each had their own, and a shipment crossing three of them carried three sets of paperwork. Every manifest carries a [[r]]unique tracking number printed on each copy, which is how one shipment stays identifiable through the whole chain. The form [[r]]names three parties: you as the generator, every transporter who will carry it, and one designated facility that has agreed in advance to receive it. And it [[r]]describes the waste precisely — the Department of Transportation shipping name, the EPA waste codes you determined back in lesson one, the quantity, and the number and type of containers.",
    reveals: [1, 19, 37, 55],
    estimatedSeconds: 58,
  },

  {
    id: "block-04",
    sheet: "S-04",
    citation: "40 CFR §§262.23, 263.20, 264.71",
    slide: "List",
    figure: {
      kind: "list",
      items: [
        "Generator signs and keeps a copy",
        "Transporter signs on acceptance",
        "Designated facility signs on receipt",
        "Signed copy returns to the generator",
      ],
    },
    narration:
      "Now the chain itself. [[r]]You sign first, certifying that the shipment is properly described, packaged, and labeled, and you keep a copy before the truck leaves the yard. The [[r]]transporter signs on acceptance, and from that signature until the next one the waste is legally in their custody — if it spills on the highway, the immediate response obligation is theirs. At the far end the [[r]]designated facility signs on receipt, which is the moment the waste becomes theirs to treat, store, or dispose of. Then the step people forget: a [[r]]signed copy comes back to you. Each signature is a transfer of custody, and none of them is optional. A load moving without a signed manifest is an unmanifested shipment, which is a violation on its own.",
    reveals: [1, 19, 38, 56],
    estimatedSeconds: 59,
  },

  {
    id: "block-05",
    sheet: "S-05",
    citation: "40 CFR §§262.42, 262.40",
    slide: "Facts",
    figure: {
      kind: "facts",
      rows: [
        { label: "Clock starts", value: "Day the transporter accepts the shipment" },
        { label: "LQG exception report", value: "45 days, to the Regional Administrator" },
        { label: "SQG exception report", value: "60 days, manifest copy with a note" },
        { label: "Retention", value: "3 years from the date of acceptance" },
      ],
    },
    narration:
      "So what happens when the copy does not come back. You start [[r]]counting from the day the transporter accepted the shipment, not the day it was supposed to arrive. A [[r]]large quantity generator that has not received a signed copy within forty-five days must file an exception report with the Regional Administrator, describing the waste, the efforts made to locate it, and the results of those efforts. A [[r]]small quantity generator has sixty days and a lighter obligation — submit a copy of the manifest with a note saying the return copy never arrived. Either way, missing paperwork is the alarm bell. And whether or not anything goes wrong, you [[r]]keep the manifest for three years from the date the transporter took the waste.",
    reveals: [1, 19, 36, 54],
    estimatedSeconds: 57,
  },

  {
    id: "block-06",
    sheet: "S-06",
    citation: "Hazardous Waste Electronic Manifest Establishment Act; 40 CFR Part 264 Subpart FF",
    slide: "Statement",
    figure: {
      kind: "statement",
      lines: [
        "e-Manifest launched June 2018",
        "Receiving facility submits within 30 days",
        "Funded by a per-manifest user fee",
      ],
    },
    narration:
      "For decades this ran on carbon paper. In [[r]]June of twenty eighteen the EPA launched e-Manifest, a national electronic system, and it changed the mechanics without changing the logic. The [[r]]receiving facility must submit the completed manifest to the system within thirty days of receipt, whether the original was electronic or paper. And the system pays for itself: the [[r]]facility owes a fee for every manifest submitted, lowest for fully electronic filings and highest for mailed paper. That pricing is deliberate. The point of a national database is that a regulator can now ask a question no filing cabinet could ever answer — where did all of this waste actually go — and get the answer in seconds rather than subpoenas.",
    reveals: [1, 27, 53],
    estimatedSeconds: 56,
  },

  {
    id: "block-07",
    sheet: "S-07",
    citation: "40 CFR §§264.72, 264.72(f)",
    slide: "List",
    figure: {
      kind: "list",
      items: [
        "Quantity or waste type does not match the manifest",
        "Facility attempts to reconcile with the generator",
        "Unresolved after 15 days — letter to the EPA",
        "Rejected loads move under a new manifest",
      ],
    },
    narration:
      "The system also has to handle the shipment that does not match its paperwork. A [[r]]manifest discrepancy is any difference between what the manifest says and what actually arrives — a different quantity, a different waste type, or a container that is not there. The facility must first [[r]]try to reconcile it, usually with a phone call to the generator. If it remains [[r]]unresolved after fifteen days, the facility sends a letter to the EPA with a copy of the manifest attached. And a facility may [[r]]refuse a load outright: on a full rejection the waste moves back or onward under a new manifest, with the rejecting facility named as the generator on that new form. The waste never becomes unaccounted for. That is the entire design.",
    reveals: [1, 19, 38, 56],
    estimatedSeconds: 59,
  },

  {
    id: "block-08",
    sheet: "S-08",
    citation: "42 U.S.C. §9607(a)(3)",
    slide: "Statement",
    figure: {
      kind: "statement",
      lines: [
        "The manifest tracks the waste, not the liability",
        "Generator status does not expire",
        "Next: what happens when there is no trail at all",
      ],
    },
    narration:
      "One closing point, and it sets up the next lesson. The manifest [[r]]tracks the waste; it does not transfer the liability. Handing a shipment to a permitted facility discharges your handling duties under RCRA, but under the Superfund statute you remain a party who arranged for disposal, and if that facility later contaminates groundwater you can be brought back in decades afterward. [[r]]Your status as the generator does not expire when the truck pulls away. Which raises the question this whole apparatus was built to answer, and [[r]]the one lesson four takes up: what happens at a site where nobody kept a manifest at all, because the shipments predated the law that would have required one.",
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
