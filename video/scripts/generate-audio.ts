#!/usr/bin/env node
/**
 * Generate narration audio and measure it, in one pass.
 *
 * This replaces the manual step in the README where you copied narration into
 * the ElevenLabs web app by hand. More importantly, it fixes a problem that
 * step never solved: reveal timings.
 *
 * The `reveals` array on each block used to be seconds you guessed against a
 * word-count estimate. When the real audio came in at a different length, every
 * reveal on that sheet drifted. Here, you mark reveal points inside the
 * narration itself with [[r]], and the script reads back the exact second each
 * marker is spoken from ElevenLabs' character-level alignment data. Reveals
 * stop being a number you tune and become a measurement.
 *
 * Usage:
 *   npm run generate                  # every block whose text has changed
 *   npm run generate -- --only block-05
 *   npm run generate -- --force       # regenerate everything
 *   npm run generate -- --dry-run     # show what would be sent, spend nothing
 *
 * Writes:
 *   public/audio/<block-id>.mp3
 *   src/audio-meta.json   durations, measured reveals, and a text hash per block
 *
 * Requires ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID in video/.env
 */

import { createHash } from "node:crypto";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { blocks, meta, transcriptOf, speechOf, type Block } from "../src/lesson-01";

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, "..");
const audioDir = join(root, "public", "audio");
const metaPath = join(root, "src", "audio-meta.json");

/* ------------------------------------------------------------------ */
/* Configuration                                                       */
/* ------------------------------------------------------------------ */

const MODEL_ID = "eleven_multilingual_v2";

/**
 * Voice settings tuned for consistency across separately generated files,
 * not for expressiveness.
 *
 * Every block is its own API call, and they play back to back as one continuous
 * lecture. Low stability means the model interprets more freely, which shows up
 * at playback as the narrator's tone visibly resetting at each sheet change.
 * High stability is duller and far more consistent. For a technical lecture that
 * is the right trade.
 *
 * If Russ sounds flat, raise `style` before you lower `stability`.
 */
const VOICE_SETTINGS = {
  stability: 0.55,
  similarity_boost: 0.8,
  style: 0.0,
  use_speaker_boost: true,
};

/**
 * A beat of silence appended to each block so the narration does not run
 * headlong into the next sheet. This is real video time and legitimately counts
 * toward runtime under 7.02.7 — it is part of the program.
 */
const TAIL_SECONDS = 0.6;

/**
 * Pronunciation dictionaries, once you have any. Get these IDs from
 * `GET /v1/pronunciation-dictionaries` after creating one. Up to three.
 *
 * Note: on eleven_multilingual_v2 only ALIAS rules take effect. Phoneme rules
 * are silently ignored by this model, which is a quiet way to waste an evening.
 */
const PRONUNCIATION_DICTIONARIES: { pronunciation_dictionary_id: string; version_id: string }[] = [];

/** Characters after a marker used to locate it in the alignment stream. */
const ANCHOR_LENGTH = 24;

/* ------------------------------------------------------------------ */
/* Environment                                                         */
/* ------------------------------------------------------------------ */

const loadEnv = () => {
  const envPath = join(root, ".env");
  if (!existsSync(envPath)) {
    fail(`No .env at ${envPath}. Create it with ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID.`);
  }
  for (const line of readFileSync(envPath, "utf8").split("\n")) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const eq = trimmed.indexOf("=");
    if (eq === -1) continue;
    const key = trimmed.slice(0, eq).trim();
    const value = trimmed.slice(eq + 1).trim().replace(/^["']|["']$/g, "");
    if (!process.env[key]) process.env[key] = value;
  }
};

const fail = (message: string): never => {
  console.error(`\n  ${message}\n`);
  process.exit(1);
};

/* ------------------------------------------------------------------ */
/* Marker handling                                                     */
/* ------------------------------------------------------------------ */

const MARKER = /\[\[r\]\]/g;

/**
 * Split narration into the text actually sent to the API and the character
 * offsets at which reveals should fire.
 *
 * The offsets are into the stripped text, because that is what the alignment
 * data describes.
 */
const parseMarkers = (narration: string) => {
  let text = "";
  let cursor = 0;
  const offsets: number[] = [];

  MARKER.lastIndex = 0;
  let match: RegExpExecArray | null;
  while ((match = MARKER.exec(narration)) !== null) {
    text += narration.slice(cursor, match.index);
    // Collapse whitespace that surrounded the marker so the sent text reads
    // naturally. The marker is punctuation for us, not for the model.
    text = text.replace(/\s+$/, "");
    if (text.length > 0) text += " ";
    offsets.push(text.length);
    cursor = match.index + match[0].length;
    while (narration[cursor] === " ") cursor += 1;
  }
  text += narration.slice(cursor);

  return { text: text.trim(), offsets };
};

/**
 * Turn character offsets into seconds using the alignment ElevenLabs returns.
 *
 * Deliberately not index arithmetic. If a pronunciation dictionary substitutes
 * an alias, the spoken character stream is a different length from what we sent,
 * and index arithmetic would silently produce wrong timings. Instead we search
 * for the phrase that follows each marker inside the reconstructed alignment
 * text, which survives substitution as long as the anchor itself was not aliased.
 */
const revealSecondsFrom = (
  alignment: { characters: string[]; character_start_times_seconds: number[] },
  sentText: string,
  offsets: number[]
): number[] => {
  const aligned = alignment.characters.join("");
  const exact = aligned === sentText;

  return offsets.map((offset) => {
    if (exact) {
      return Number(alignment.character_start_times_seconds[offset].toFixed(3));
    }
    const anchor = sentText.slice(offset, offset + ANCHOR_LENGTH);
    const found = aligned.indexOf(anchor);
    if (found === -1) {
      console.warn(
        `    could not locate reveal anchor "${anchor.slice(0, 30)}…" — falling back to offset`
      );
      const clamped = Math.min(offset, alignment.character_start_times_seconds.length - 1);
      return Number(alignment.character_start_times_seconds[clamped].toFixed(3));
    }
    return Number(alignment.character_start_times_seconds[found].toFixed(3));
  });
};

/* ------------------------------------------------------------------ */
/* Generation                                                          */
/* ------------------------------------------------------------------ */

type BlockMeta = {
  durationSeconds: number;
  reveals: number[];
  hash: string;
  generatedAt: string;
};

const hashOf = (text: string) =>
  createHash("sha256").update(text).digest("hex").slice(0, 12);

const generate = async (
  block: Block,
  previousText: string,
  nextText: string,
  apiKey: string,
  voiceId: string
): Promise<BlockMeta> => {
  const { text, offsets } = parseMarkers(speechOf(block));

  const body: Record<string, unknown> = {
    text,
    model_id: MODEL_ID,
    voice_settings: VOICE_SETTINGS,
    // Prosody context. Not spoken — it tells the model how the sentence before
    // and after landed, which noticeably smooths the seams between sheets.
    previous_text: previousText || undefined,
    next_text: nextText || undefined,
  };
  if (PRONUNCIATION_DICTIONARIES.length > 0) {
    body.pronunciation_dictionary_locators = PRONUNCIATION_DICTIONARIES;
  }

  const url =
    `https://api.elevenlabs.io/v1/text-to-speech/${voiceId}/with-timestamps` +
    `?output_format=mp3_44100_128`;

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "xi-api-key": apiKey,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`${response.status} ${response.statusText}\n    ${detail.slice(0, 400)}`);
  }

  const payload = (await response.json()) as {
    audio_base64: string;
    alignment: {
      characters: string[];
      character_start_times_seconds: number[];
      character_end_times_seconds: number[];
    };
  };

  mkdirSync(audioDir, { recursive: true });
  writeFileSync(join(audioDir, `${block.id}.mp3`), Buffer.from(payload.audio_base64, "base64"));

  const ends = payload.alignment.character_end_times_seconds;
  const spoken = ends[ends.length - 1];
  const reveals = revealSecondsFrom(payload.alignment, text, offsets);

  return {
    durationSeconds: Number((spoken + TAIL_SECONDS).toFixed(3)),
    reveals,
    hash: hashOf(text),
    generatedAt: new Date().toISOString(),
  };
};

/* ------------------------------------------------------------------ */
/* Main                                                                */
/* ------------------------------------------------------------------ */

const main = async () => {
  loadEnv();

  const args = process.argv.slice(2);
  const force = args.includes("--force");
  const dryRun = args.includes("--dry-run");
  const onlyIndex = args.indexOf("--only");
  const only = onlyIndex !== -1 ? args[onlyIndex + 1] : null;

  const apiKey = process.env.ELEVENLABS_API_KEY;
  const voiceId = process.env.ELEVENLABS_VOICE_ID;
  if (!dryRun && !apiKey) fail("ELEVENLABS_API_KEY is not set in video/.env");
  if (!dryRun && !voiceId) fail("ELEVENLABS_VOICE_ID is not set in video/.env");

  const existing: Record<string, BlockMeta> = existsSync(metaPath)
    ? JSON.parse(readFileSync(metaPath, "utf8"))
    : {};

  // Blocks with empty narration — the title sheet — have no audio by design.
  const spoken = blocks.filter((b) => b.narration.trim().length > 0);
  const targets = only ? spoken.filter((b) => b.id === only) : spoken;

  if (only && targets.length === 0) {
    fail(`No block with id "${only}". Ids: ${spoken.map((b) => b.id).join(", ")}`);
  }

  console.log(`\n  ${meta.courseCode} — ${meta.lessonTitle}`);
  console.log(`  voice ${voiceId ?? "(dry run)"}  model ${MODEL_ID}\n`);

  const result = { ...existing };
  let generated = 0;
  let skipped = 0;

  for (const block of targets) {
    const { text } = parseMarkers(speechOf(block));
    const hash = hashOf(text);
    const audioExists = existsSync(join(audioDir, `${block.id}.mp3`));
    const unchanged = existing[block.id]?.hash === hash && audioExists;

    if (unchanged && !force) {
      console.log(`  ${block.sheet}  ${block.id.padEnd(9)} unchanged, skipped`);
      skipped += 1;
      continue;
    }

    if (dryRun) {
      const { offsets } = parseMarkers(speechOf(block));
      console.log(`  ${block.sheet}  ${block.id.padEnd(9)} ${text.length} chars, ${offsets.length} reveals`);
      continue;
    }

    const index = spoken.indexOf(block);
    const previousText = index > 0 ? transcriptOf(spoken[index - 1]) : "";
    const nextText = index < spoken.length - 1 ? transcriptOf(spoken[index + 1]) : "";

    process.stdout.write(`  ${block.sheet}  ${block.id.padEnd(9)} generating… `);
    try {
      const blockMeta = await generate(block, previousText, nextText, apiKey!, voiceId!);
      result[block.id] = blockMeta;
      console.log(
        `${blockMeta.durationSeconds.toFixed(1)}s  ` +
          `est ${block.estimatedSeconds}s  ` +
          `reveals [${blockMeta.reveals.map((r) => r.toFixed(1)).join(", ")}]`
      );
      generated += 1;
    } catch (error) {
      console.log("FAILED");
      console.error(`    ${(error as Error).message}`);
      process.exitCode = 1;
    }
  }

  if (dryRun) {
    console.log("\n  Dry run. Nothing sent, nothing written.\n");
    return;
  }

  writeFileSync(metaPath, JSON.stringify(result, null, 2) + "\n");

  /* -------------------------------------------------------------- */
  /* Runtime and credit                                              */
  /* -------------------------------------------------------------- */

  const missing = spoken.filter((b) => result[b.id] === undefined);
  const totalSeconds = blocks.reduce(
    (sum, b) => sum + (result[b.id]?.durationSeconds ?? b.estimatedSeconds),
    0
  );

  console.log(`\n  generated ${generated}, skipped ${skipped}`);
  console.log(
    `  runtime ${Math.floor(totalSeconds / 60)}m ${Math.round(totalSeconds % 60)}s` +
      (missing.length ? `  (${missing.length} block(s) still estimated)` : "")
  );

  if (missing.length === 0) {
    // 7.02.7, entire program is video:
    //   [actual video minutes + (questions x 1.85)] / 50
    //
    // The question count is a placeholder. Under feature 019 the course, not
    // the lesson, is the credit-bearing unit, so the real figure is every
    // question across all five lessons and the real runtime is all five videos
    // summed. Treat what follows as a sanity check on this segment, not as the
    // number that goes on a certificate. The app owns that arithmetic.
    const questions = 8;
    const minutes = totalSeconds / 60;
    const credit = (minutes + questions * 1.85) / 50;
    const rounded = Math.floor(credit * 5) / 5;

    console.log("\n  7.02.7 sanity check, this segment alone:");
    console.log(
      `    [${minutes.toFixed(2)} min + (${questions} x 1.85)] / 50 = ${credit.toFixed(3)}`
    );
    console.log(`    rounded down to one-fifth: ${rounded.toFixed(1)} credits`);
    console.log("    NOT the course credit. Credit attaches to the course.");
  }

  console.log("\n  Next: npm run dev, and check the reveals land on the words.\n");
};

main().catch((error) => fail(error.message));
