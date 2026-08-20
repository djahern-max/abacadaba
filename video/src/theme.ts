import { loadFont as loadArchivo } from "@remotion/google-fonts/Archivo";
import { loadFont as loadPlexMono } from "@remotion/google-fonts/IBMPlexMono";

const { fontFamily: archivo } = loadArchivo();
const { fontFamily: plexMono } = loadPlexMono();

/**
 * Visual language: a construction drawing set.
 *
 * Every slide is a "sheet" carrying a title block, the way a real drawing
 * sheet does. This is not decoration — the sheets are a numbered sequence and
 * each one cites a specific ASC paragraph, so the title block encodes two
 * things that are actually true about the content and need to be on screen
 * anyway.
 *
 * Palette is taken from the subject's own materials rather than a generic
 * slide theme: drafting vellum, graphite pencil, and the fluorescent pink of
 * surveyor's flagging tape. The pink marks the one thing currently under
 * discussion and appears nowhere else. If it is on more than two elements at
 * once, something has gone wrong.
 */
export const theme = {
  color: {
    vellum: "#F1F3F1",      // sheet background, faintly green-grey like drafting film
    vellumEdge: "#E4E8E5",  // panel fills, table banding
    graphite: "#22262B",    // primary type
    slate: "#5F6D79",       // secondary type, rules
    hairline: "#C3CBC7",    // drawing border, dividers
    flag: "#D01F63",        // surveyor's flagging — the marker, used sparingly
    flagWash: "#FBE7EF",    // flag at low opacity, for fills behind marked items
  },
  font: {
    display: archivo,   // grotesque with an engineered squareness
    body: archivo,
    mono: plexMono,     // title block, sheet numbers, ASC citations
  },
  size: {
    display: 84,
    heading: 62,
    subhead: 44,
    body: 36,
    caption: 26,
    titleBlock: 22,
  },
  // Drawing border inset, in px on a 1920x1080 sheet
  margin: 84,
} as const;

export const FPS = 30;
export const WIDTH = 1920;
export const HEIGHT = 1080;

export const seconds = (s: number) => Math.round(s * FPS);
