#!/usr/bin/env node
/**
 * Check every lesson module against the invariants the slide components and the
 * credit rules depend on.
 *
 * These rules already existed, written down in three places: lesson-01.ts's doc
 * comment, LESSON-RUNBOOK.md's "rules that will bite you", and the head of each
 * lesson file. None of them was executable. `generate --dry-run` reports marker
 * counts but does not fail on a mismatch, and finding out that way costs an
 * ElevenLabs round trip. This runs over the committed content instead, offline
 * and free.
 *
 * Usage:
 *   npm run check                 # every lesson
 *   npm run check -- --lesson 06  # one lesson
 *
 * Exit code is 1 if any ERROR fired, 0 otherwise. Warnings never fail the run.
 *
 * ERROR vs WARN is the difference between a wrong video and a wrong preview.
 * An ERROR means the rendered MP4 is defective: an element that never appears,
 * a blank sheet, audio that no longer matches its narration. A WARN means only
 * the silent preview is off, because `estimatedSeconds` and the `reveals`
 * fallback are both discarded the moment measured audio exists and neither may
 * ever reach a credit calculation (7.02.7).
 */

import { LESSONS, type LessonId } from "../src/lessons";

/* ------------------------------------------------------------------ */
/* Configuration                                                       */
/* ------------------------------------------------------------------ */

/** The constant lesson-01.ts documents. Estimates are derived from it. */
const WPM = 130;

/** Attention resets every 20–30s; a new sheet is the cheapest reset. */
const SHEET_MIN_SECONDS = 40;
const SHEET_MAX_SECONDS = 75;

/**
 * Which `figure.kind` each generic slide component accepts.
 *
 * Every component in slides.tsx early-returns null on a kind it does not
 * recognise, so a `Calc` slide carrying a `facts` figure renders a completely
 * blank sheet for the full length of its block. That is the single most
 * expensive mistake available here and nothing else catches it.
 *
 * This is a second copy of a mapping that lives in slides.tsx, and it is
 * deliberate: importing slides.tsx would pull React, Remotion, and
 * @remotion/google-fonts into a plain node script for the sake of five strings.
 * The `Block["slide"]` union already stops a misspelled component name at
 * compile time, so what is duplicated here is only the pairing.
 */
const FIGURE_KIND_FOR: Record<string, string> = {
  Statement: "statement",
  Facts: "facts",
  Calc: "calc",
  List: "list",
  Compare: "compare",
};

/* ------------------------------------------------------------------ */
/* Types                                                               */
/* ------------------------------------------------------------------ */

type AnyBlock = {
  id: string;
  sheet: string;
  citation: string;
  slide: string;
  figure?: Record<string, unknown>;
  narration: string;
  reveals: number[];
  estimatedSeconds: number;
  speech?: string;
};

type LessonModule = {
  meta: Record<string, string>;
  blocks: AnyBlock[];
  transcriptOf: (b: AnyBlock) => string;
  hasAudio: (b: AnyBlock) => boolean;
  durationOf: (b: AnyBlock) => number;
  revealsOf: (b: AnyBlock) => number[];
  usingEstimates: boolean;
  totalSeconds: number;
};

type Finding = { level: "ERROR" | "WARN"; block: string; message: string };

/**
 * Label a finding by id AND sheet. Duplicate ids are one of the things being
 * checked for, so labelling by id alone makes exactly the case that matters
 * unreadable — two findings on "block-04" with no way to tell which is which.
 */
const label = (b: AnyBlock) => `${b.id} ${b.sheet}`;

/* ------------------------------------------------------------------ */
/* Helpers                                                             */
/* ------------------------------------------------------------------ */

const markerCount = (s: string) => (s.match(/\[\[r\]\]/g) ?? []).length;

const wordCount = (s: string) => s.split(/\s+/).filter(Boolean).length;

const expectedSeconds = (words: number) => Math.round((words / WPM) * 60);

/** The revealable elements in a figure, whichever key this kind uses. */
const figureElements = (figure: Record<string, unknown> | undefined): number | null => {
  if (!figure) return null;
  for (const key of ["lines", "rows", "items", "columns"]) {
    const v = figure[key];
    if (Array.isArray(v)) return v.length;
  }
  return null;
};

const mmss = (seconds: number) =>
  `${Math.floor(seconds / 60)}m ${String(Math.round(seconds % 60)).padStart(2, "0")}s`;

/* ------------------------------------------------------------------ */
/* The checks                                                          */
/* ------------------------------------------------------------------ */

function checkLesson(mod: LessonModule): Finding[] {
  const findings: Finding[] = [];
  const err = (b: AnyBlock, message: string) =>
    findings.push({ level: "ERROR", block: label(b), message });
  const warn = (b: AnyBlock, message: string) =>
    findings.push({ level: "WARN", block: label(b), message });

  const seen = new Set<string>();

  for (const b of mod.blocks) {
    /* --- identity ------------------------------------------------- */

    if (seen.has(b.id)) {
      err(b, `duplicate block id — the mp3 filename collides and one block's audio silently overwrites the other`);
    }
    seen.add(b.id);

    const isTitle = b.slide === "Title";

    if (isTitle && b.narration.trim().length > 0) {
      err(b, `a Title block must have empty narration — usingEstimates excludes narration-less blocks, and a narrated title makes it permanently true`);
    }
    if (!isTitle && b.narration.trim().length === 0) {
      err(b, `empty narration on a non-Title block — it will render silent for ${b.estimatedSeconds}s`);
    }

    /* --- figure and slide pairing --------------------------------- */

    const generic = isTitle || b.slide in FIGURE_KIND_FOR;

    if (!generic) {
      // Lesson 01's bespoke components (Misconception, FiveSteps, and the rest)
      // carry their content inside the component rather than in a figure. There
      // is nothing here to count, so the figure checks below are skipped rather
      // than failed. Their element counts are a real blind spot: a bespoke
      // component with fewer elements than its block has markers cannot be
      // detected without reading the JSX.
      warn(b, `bespoke slide component "${b.slide}" — figure checks skipped, element count not verifiable from data`);
    } else if (isTitle) {
      if (b.figure) err(b, `a Title block should not carry a figure — Title reads meta, not figure`);
    } else {
      const wanted = FIGURE_KIND_FOR[b.slide];
      if (!b.figure) {
        err(b, `slide "${b.slide}" has no figure — the component returns null and the sheet renders blank for the whole block`);
      } else if (b.figure.kind !== wanted) {
        err(b, `slide "${b.slide}" wants figure.kind "${wanted}" but got "${String(b.figure.kind)}" — the component returns null and the sheet renders blank for the whole block`);
      }
    }

    /* --- markers vs reveals --------------------------------------- */

    const markers = markerCount(b.narration);
    const fallback = b.reveals;

    // The title sheet has no narration, so its three reveals are hand-set and
    // have no markers to match. Everything else must agree.
    if (!isTitle && markers !== fallback.length) {
      err(b, `${markers} marker(s) but reveals has ${fallback.length} entr${fallback.length === 1 ? "y" : "ies"} — slides index reveals positionally, so the mismatch renders undefined and the element never appears`);
    }

    if (fallback.length === 0) {
      err(b, `empty reveals array — nothing on this sheet will ever appear`);
    }

    const ascending = fallback.every((r, i) => i === 0 || r > fallback[i - 1]);
    if (!ascending) err(b, `reveals are not strictly ascending: [${fallback.join(", ")}]`);
    if (fallback.some((r) => r < 0)) err(b, `negative reveal time in [${fallback.join(", ")}]`);

    /* --- stale audio ---------------------------------------------- */

    const measured = mod.hasAudio(b);
    if (measured && !isTitle) {
      const measuredReveals = mod.revealsOf(b);
      if (measuredReveals.length !== markers) {
        err(b, `narration has ${markers} marker(s) but the measured audio recorded ${measuredReveals.length} — the mp3 is stale relative to the text. Regenerate this block before rendering`);
      }
    }

    /* --- figure element count ------------------------------------- */

    const elements = figureElements(b.figure);
    if (elements !== null && elements < fallback.length) {
      err(b, `figure has ${elements} element(s) but ${fallback.length} reveal(s) — the extra markers are wasted and the last ones fire on nothing`);
    }

    /* --- pacing --------------------------------------------------- */

    const actual = mod.durationOf(b);
    if (!isTitle && (actual < SHEET_MIN_SECONDS || actual > SHEET_MAX_SECONDS)) {
      warn(b, `${Math.round(actual)}s is outside the ${SHEET_MIN_SECONDS}–${SHEET_MAX_SECONDS}s sheet window${measured ? " (measured)" : " (estimated)"}`);
    }

    /* --- estimate hygiene ----------------------------------------- */
    /* Only meaningful until audio exists; measured duration always wins.  */

    if (!isTitle && !measured) {
      const words = wordCount(mod.transcriptOf(b));
      const want = expectedSeconds(words);
      if (b.estimatedSeconds !== want) {
        warn(b, `estimatedSeconds is ${b.estimatedSeconds} but ${words} words at ${WPM} wpm is ${want}`);
      }
      if (fallback[0] < 0.5) {
        warn(b, `first reveal at ${fallback[0]}s — nothing is on screen before it`);
      }
      const last = fallback[fallback.length - 1];
      if (last > b.estimatedSeconds - 3) {
        warn(b, `last reveal at ${last}s leaves under 3s before the sheet changes`);
      }
    }
  }

  /* --- speech drift ----------------------------------------------- */

  for (const b of mod.blocks) {
    if (b.speech && markerCount(b.speech) !== markerCount(b.narration)) {
      err(b, `speech and narration carry different marker counts — speech is what gets timed, narration is the transcript of record, and they must agree`);
    }
  }

  for (const k of ["courseCode", "courseTitle", "lessonTitle", "position",
    "deliveryMethod", "fieldOfStudy", "revision", "revisionDate"]) {
    if (!mod.meta[k]) {
      findings.push({
        level: "ERROR",
        block: "meta",
        message: `meta.${k} is missing or empty — it renders as undefined on the sheet`,
      });
    }
  }

  return findings;
}

/* ------------------------------------------------------------------ */
/* Report                                                              */
/* ------------------------------------------------------------------ */

function main() {
  const argv = process.argv.slice(2);
  const at = argv.indexOf("--lesson");
  const only = at >= 0 ? argv[at + 1] : null;

  // Sorted, not insertion order. A key that looks like an array index ("99")
  // is enumerated before one that does not ("01"), so relying on the order
  // lessons.ts declares them in would put lessons in the wrong sequence the
  // first time an id loses its leading zero.
  const ids = (Object.keys(LESSONS) as LessonId[])
    .sort()
    .filter((id) => !only || id === only);

  if (only && ids.length === 0) {
    console.error(`No lesson "${only}". Known: ${(Object.keys(LESSONS) as LessonId[]).sort().join(", ")}`);
    process.exit(1);
  }

  let errors = 0;
  let warnings = 0;

  for (const id of ids) {
    const mod = LESSONS[id] as unknown as LessonModule;
    const findings = checkLesson(mod);
    errors += findings.filter((f) => f.level === "ERROR").length;
    warnings += findings.filter((f) => f.level === "WARN").length;

    const audio = mod.usingEstimates
      ? `${mmss(mod.totalSeconds)} estimated`
      : `${mmss(mod.totalSeconds)} measured`;
    const draft = mod.meta.status ? `  [${mod.meta.status}]` : "";

    console.log(`\nLESSON ${id}  ${mod.meta.courseTitle} — ${mod.meta.lessonTitle}${draft}`);
    console.log(`  ${mod.blocks.length} blocks · ${audio}`);

    if (findings.length === 0) {
      console.log(`  ok`);
      continue;
    }
    for (const f of findings) {
      const tag = f.level === "ERROR" ? "  ERROR" : "  warn ";
      console.log(`${tag} ${f.block.padEnd(14)} ${f.message}`);
    }
  }

  console.log(
    `\n${ids.length} lesson(s) checked · ${errors} error(s) · ${warnings} warning(s)`
  );

  if (errors > 0) {
    console.log(
      `\nErrors mean the rendered video is defective. Fix them before spending` +
      ` narration credit or rendering.`
    );
  }

  process.exit(errors > 0 ? 1 : 0);
}

main();
