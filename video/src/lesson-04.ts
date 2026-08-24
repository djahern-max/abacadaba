/**
 * Lesson 04 — "Love Canal and the Birth of Superfund"
 * Course: Where Does It Actually Go? (hazardous waste, ESG/Sustainability)
 *
 * STATUS: DRAFT — NOT REVIEWED. Clear `meta.status` once a subject matter
 * expert has read the narration (4.01.1, 4.02), then re-render. Clearing the
 * stamp does not require regenerating audio.
 *
 * Maps to learning objective 4: explain how the Love Canal disaster led to the
 * creation of Superfund, and describe how contaminated sites are identified,
 * ranked, and paid for. Two assessment questions are tagged to this objective,
 * so the narration must cover BOTH halves — the history and the HRS/NPL
 * mechanism. Blocks 01–05 are the history; 06–08 are the mechanism.
 *
 * SLIDE NOTE: blocks 03, 04, and 07 are chronologies and want a `Timeline`
 * component, which does not exist yet. They are authored as ordered `List`
 * figures. When `Timeline` lands, swapping those figures is a re-render only —
 * narration and reveal counts are unaffected, so the audio survives.
 *
 * DATES: every date and figure in this lesson is checkable against EPA's Love
 * Canal site record and the CERCLA statute. They are the substance of the
 * assessment questions, so they get verified in review rather than trusted.
 *
 * Types are imported from lesson-01, which is the single definition point.
 *
 * Reveal markers: [[r]] sits in `narration`, immediately before the WORD it
 * reveals. Marker count MUST equal `reveals` length. Verify with
 * `npm run generate -- --lesson 04 --dry-run` before spending any credit.
 */

import audioMeta from "./audio-meta-04.json";
import type { Block } from "./lesson-01";

export type { Block, Figure } from "./lesson-01";

export const meta = {
  lessonId: "04",
  courseCode: "HAZWASTE-04",
  courseTitle: "Where Does It Actually Go?",
  lessonTitle: "Love Canal and the Birth of Superfund",
  title: "Love Canal and the Birth of Superfund",
  subtitle: "How one neighborhood produced a federal cleanup program",
  eyebrow: "Lesson 04",
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
    citation: "EPA Region 2, Love Canal site record",
    slide: "Statement",
    figure: {
      kind: "statement",
      lines: [
        "A canal dug for a city that was never built",
        "A clay-lined trench, then a school on top",
        "Every step was legal when it was taken",
      ],
    },
    narration:
      "Every rule in the last three lessons exists because of a place. In the eighteen nineties an entrepreneur named William Love began digging a [[r]]canal at Niagara Falls to power a model industrial city. The city was never built, the financing collapsed, and what remained was a trench roughly three thousand feet long. Decades later it looked like an asset: a [[r]]clay-lined pit, apparently watertight, in a region that badly needed somewhere to put chemical waste. What happened next is the reason we have manifests, permitted facilities, and a federal cleanup program. And the part worth holding onto from the start is that [[r]]nearly every step was lawful when it was taken. The law arrived thirty-eight years after the first drum went in.",
    reveals: [1, 28, 54],
    estimatedSeconds: 57,
  },

  {
    id: "block-02",
    sheet: "S-02",
    citation: "EPA Region 2, Love Canal site record",
    slide: "Facts",
    figure: {
      kind: "facts",
      rows: [
        { label: "Site", value: "Abandoned canal, Niagara Falls, New York" },
        { label: "Dumping", value: "1942–1953, roughly 21,800 tons of waste" },
        { label: "Sale", value: "1953, to the Board of Education, for $1" },
        { label: "Deed", value: "Described the waste; disclaimed all liability" },
      ],
    },
    narration:
      "The facts are short and they are not in dispute. The [[r]]site is an abandoned canal in Niagara Falls, New York. Between [[r]]nineteen forty-two and nineteen fifty-three, Hooker Chemical placed roughly twenty-one thousand eight hundred tons of chemical waste into it — drummed and bulk, including solvent residues, pesticide byproducts, and dioxin-bearing material. Then in [[r]]nineteen fifty-three the company sold the covered site to the Niagara Falls Board of Education for one dollar. The [[r]]deed is the detail that makes this a case study rather than merely a scandal: it described the waste, warned against disturbing the cover, and disclaimed all future liability. The seller disclosed. The buyer accepted. And under the law as it then stood, that was the end of the matter.",
    reveals: [1, 19, 36, 54],
    estimatedSeconds: 57,
  },

  {
    id: "block-03",
    sheet: "S-03",
    citation: "EPA Region 2; NYS Department of Health",
    slide: "List",
    figure: {
      kind: "list",
      items: [
        "A school and hundreds of homes built on and around the site",
        "Sewer and road construction cut through the clay cap",
        "A run of wet years raised the water table",
        "Chemicals surfaced in basements, yards, and the schoolyard",
      ],
    },
    narration:
      "Containment failed in four steps, none of them dramatic. First, a [[r]]school opened on the site in nineteen fifty-five and hundreds of homes went up around it, because the land was cheap and the neighborhood was growing. Second, [[r]]sewer lines and road cuts were driven through the clay cap — that cap was the entire containment, and it was breached by ordinary municipal construction. Third, a [[r]]run of unusually wet years raised the water table, and the trench began to behave like a bathtub. Fourth, the contents [[r]]came up: sludge in basements, corroding drums working toward the surface, chemical burns reported on children in the schoolyard, and standing puddles that would not evaporate. No single decision caused this. Four ordinary ones did.",
    reveals: [1, 18, 36, 53],
    estimatedSeconds: 56,
  },

  {
    id: "block-04",
    sheet: "S-04",
    citation: "Presidential emergency declarations, 1978 and 1980",
    slide: "List",
    figure: {
      kind: "list",
      items: [
        "1976 — press investigation and resident sampling",
        "August 2, 1978 — New York declares a health emergency",
        "August 7, 1978 — first federal emergency, non-natural disaster",
        "May 1980 — second declaration, ~700 more households",
      ],
    },
    narration:
      "The response took four years, and it began with residents rather than regulators. In [[r]]nineteen seventy-six a local newspaper investigation and independent sampling documented what people had been reporting for years, and Lois Gibbs, a mother whose son attended the school, organized the homeowners association that refused to let the story close. On [[r]]August second, nineteen seventy-eight, the New York health commissioner declared a public health emergency and recommended evacuating pregnant women and young children. [[r]]Five days later President Carter declared a federal emergency — the first ever issued for something other than a natural disaster — and two hundred thirty-nine families were relocated. In [[r]]May of nineteen eighty a second declaration extended relocation to roughly seven hundred more households.",
    reveals: [1, 18, 35, 52],
    estimatedSeconds: 55,
  },

  {
    id: "block-05",
    sheet: "S-05",
    citation: "42 U.S.C. §9601 et seq.",
    slide: "Statement",
    figure: {
      kind: "statement",
      lines: [
        "CERCLA signed December 11, 1980",
        "RCRA governs waste being generated now",
        "CERCLA reaches backward, to waste already in the ground",
      ],
    },
    narration:
      "[[r]]Superfund was signed into law on December eleventh, nineteen eighty — five weeks after the election, by an outgoing president, in the last days of an outgoing Congress. Formally it is the Comprehensive Environmental Response, Compensation, and Liability Act. Its distinction from everything in lessons one through three is the entire point. [[r]]RCRA governs waste that is being generated now. It is prospective and procedural, and it works through permits, categories, and manifests. [[r]]CERCLA reaches backward. It applies to waste already in the ground, put there by companies that may no longer exist, under practices that broke no law at the time. Congress decided someone had to pay for those sites, and that it should not be whoever happened to buy the land afterward.",
    reveals: [1, 28, 54],
    estimatedSeconds: 57,
  },

  {
    id: "block-06",
    sheet: "S-06",
    citation: "42 U.S.C. §9607(a)",
    slide: "Facts",
    figure: {
      kind: "facts",
      rows: [
        { label: "Strict", value: "No negligence needs to be shown" },
        { label: "Joint and several", value: "One party can be held for the whole cost" },
        { label: "Retroactive", value: "Reaches disposal that was legal at the time" },
        { label: "Four classes of PRP", value: "Current owner, past owner, generator, transporter" },
      ],
    },
    narration:
      "The liability scheme is the most aggressive in American environmental law, and it carries three adjectives. It is [[r]]strict: nobody has to prove you were careless, only that your waste is there. It is [[r]]joint and several, so where the harm cannot be cleanly divided, one solvent party can be held responsible for the entire cost and left to sue the others for contribution. And it is [[r]]retroactive, reaching conduct that violated nothing when it occurred. The statute names [[r]]four classes of potentially responsible party: the current owner or operator, the owner or operator at the time of disposal, anyone who arranged for disposal — which means the generator, and which is exactly where lesson three ended — and transporters who selected the site.",
    reveals: [1, 19, 36, 54],
    estimatedSeconds: 57,
  },

  {
    id: "block-07",
    sheet: "S-07",
    citation: "40 CFR Part 300, Appendix A (Hazard Ranking System)",
    slide: "List",
    figure: {
      kind: "list",
      items: [
        "Preliminary assessment, then site inspection",
        "Hazard Ranking System score across four pathways",
        "28.50 or above — eligible for the National Priorities List",
        "Investigation, Record of Decision, remedy, deletion",
      ],
    },
    narration:
      "Sites are not cleaned up because they are bad. They are cleaned up because they are ranked. A reported site first gets a [[r]]preliminary assessment from existing records, and where warranted a site inspection with actual sampling. Those results feed the [[r]]Hazard Ranking System, a numerical model that scores the site across four pathways — groundwater, surface water, soil exposure, and air — weighing how toxic the material is, how likely it is to move, and how many people are close to it. A score of [[r]]twenty-eight point five zero or higher makes a site eligible for the National Priorities List. Listing opens the long road: [[r]]remedial investigation, a feasibility study of the alternatives, a Record of Decision selecting the remedy, construction, and eventually deletion from the list.",
    reveals: [1, 19, 38, 56],
    estimatedSeconds: 59,
  },

  {
    id: "block-08",
    sheet: "S-08",
    citation: "26 U.S.C. §4661; Infrastructure Investment and Jobs Act (2021)",
    slide: "Statement",
    figure: {
      kind: "statement",
      lines: [
        "Funded by excise taxes on chemicals and petroleum",
        "Authority lapsed in 1995; reinstated in 2022",
        "Enforcement first — responsible parties pay most cleanups",
      ],
    },
    narration:
      "Which leaves the word in the middle of the statute's name: compensation. Superfund was originally a trust fund fed by [[r]]excise taxes on chemical feedstocks and petroleum, on the theory that the industries producing the hazard should capitalize the remedy. That taxing [[r]]authority lapsed in nineteen ninety-five, the balance ran down, and for nearly two decades cleanups were funded from general appropriations — the chemical excise taxes were only reinstated in twenty twenty-two. But the fund was never meant to be the main payer. EPA's stated policy is [[r]]enforcement first, and most cleanups are performed or financed by responsible parties, which is what joint and several liability is for. Occidental, Hooker's successor, settled with the United States for one hundred twenty-nine million dollars in nineteen ninety-five.",
    reveals: [1, 28, 55],
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
