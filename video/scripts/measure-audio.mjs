#!/usr/bin/env node
/**
 * Measure the narration audio and write src/durations.json.
 *
 * This is the step that turns the composition from "roughly right" into
 * something whose runtime can be used for the CPE credit calculation. Estimated
 * durations are for judging the visuals; they must never reach the credit
 * formula under 7.02.7.
 *
 * Usage:
 *   1. Put ElevenLabs output in public/audio/ as <block-id>.mp3
 *      (block-01.mp3 ... block-07.mp3; the title sheet has no narration)
 *   2. npm run measure
 *   3. Paste the printed AUDIO_PRESENT block into src/Lesson.tsx
 *   4. npm run render
 *
 * Requires ffprobe on PATH (comes with ffmpeg).
 */

import { execFileSync } from "node:child_process";
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, "..");
const audioDir = join(root, "public", "audio");
const durationsPath = join(root, "src", "durations.json");

// Read block ids and estimates straight out of the content file rather than
// duplicating the list here. Two copies of the block list will drift.
const lessonSrc = readFileSync(join(root, "src", "lesson-01.ts"), "utf8");
const ids = [...lessonSrc.matchAll(/id:\s*"([^"]+)"/g)].map((m) => m[1]);
const estimates = [...lessonSrc.matchAll(/estimatedSeconds:\s*([\d.]+)/g)].map(
  (m) => Number(m[1])
);

if (ids.length !== estimates.length) {
  console.error(
    "Could not pair block ids with estimates. Check the shape of lesson-01.ts."
  );
  process.exit(1);
}

const probe = (file) => {
  const out = execFileSync(
    "ffprobe",
    [
      "-v", "error",
      "-show_entries", "format=duration",
      "-of", "default=noprint_wrappers=1:nokey=1",
      file,
    ],
    { encoding: "utf8" }
  );
  return Number(out.trim());
};

// A beat of silence after each block so the narration does not run headlong
// into the next sheet. Tune this once you have heard it.
const TAIL_SECONDS = 0.6;

const durations = {};
const present = [];
const rows = [];
let total = 0;

ids.forEach((id, i) => {
  const file = join(audioDir, `${id}.mp3`);
  if (existsSync(file)) {
    const measured = probe(file) + TAIL_SECONDS;
    durations[id] = Number(measured.toFixed(3));
    present.push(id);
    rows.push([id, estimates[i], durations[id], "measured"]);
    total += durations[id];
  } else {
    rows.push([id, estimates[i], estimates[i], "ESTIMATE — no audio"]);
    total += estimates[i];
  }
});

writeFileSync(durationsPath, JSON.stringify(durations, null, 2) + "\n");

console.log("");
console.log("block        estimate   actual   source");
console.log("------------------------------------------------------");
for (const [id, est, act, src] of rows) {
  console.log(
    `${id.padEnd(12)} ${String(est).padStart(7)}s ${String(act).padStart(7)}s   ${src}`
  );
}
console.log("------------------------------------------------------");

const mins = Math.floor(total / 60);
const secs = total % 60;
console.log(`total        ${total.toFixed(1)}s  =  ${mins}m ${secs.toFixed(0)}s`);
console.log("");

if (present.length === ids.length) {
  const questions = 8;
  const credit = (total / 60 + questions * 1.85) / 50;
  const rounded = Math.floor(credit * 5) / 5;
  console.log("CPE credit, 7.02.7 (entire program is video):");
  console.log(
    `  [${(total / 60).toFixed(2)} min + (${questions} questions x 1.85)] / 50 = ${credit.toFixed(3)}`
  );
  console.log(`  Rounded down to the nearest one-fifth: ${rounded.toFixed(1)} credits`);
  console.log("  Enter the runtime, not this number, in the admin editor —");
  console.log("  the app recomputes and must own the arithmetic.");
} else {
  console.log(
    `${ids.length - present.length} block(s) still have no audio. Runtime above is not final.`
  );
}

console.log("");
console.log("Paste into src/Lesson.tsx:");
console.log("const AUDIO_PRESENT: Record<string, boolean> = {");
for (const id of present) console.log(`  "${id}": true,`);
console.log("};");
console.log("");
