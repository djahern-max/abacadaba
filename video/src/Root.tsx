import React from "react";
import { Composition } from "remotion";
import { Lesson } from "./Lesson";
import * as lesson01 from "./lesson-01";
import * as lesson02 from "./lesson-02";
import { FPS, WIDTH, HEIGHT, seconds } from "./theme";

// Sum the frames the same way Lesson.tsx does, so a composition's length can
// never drift from its content. The credit calculation depends on this number
// being the real runtime, which is why it is derived rather than typed in.
const framesFor = (
  blocks: { id: string }[],
  durationOf: (b: never) => number
) => blocks.reduce((sum, b) => sum + seconds(durationOf(b as never)), 0);

const warnIfEstimated = (
  label: string,
  usingEstimates: boolean,
  totalSeconds: number
) => {
  if (!usingEstimates) return;
  console.warn(
    `\n[abacadaba] ${label}: Rendering with ESTIMATED block durations.\n` +
      `  Runtime: ${Math.floor(totalSeconds / 60)}m ${Math.round(totalSeconds % 60)}s (estimated)\n` +
      `  Do not use this figure for the CPE credit calculation.\n` +
      `  Run \`npm run generate\` (or \`generate:02\`) to produce narration audio, then re-render.\n`
  );
};

warnIfEstimated("Lesson01", lesson01.usingEstimates, lesson01.totalSeconds);
warnIfEstimated("Lesson02", lesson02.usingEstimates, lesson02.totalSeconds);

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="Lesson01"
      component={Lesson}
      defaultProps={{ lessonId: "01" }}
      durationInFrames={framesFor(lesson01.blocks, lesson01.durationOf as never)}
      fps={FPS}
      width={WIDTH}
      height={HEIGHT}
    />
    <Composition
      id="Lesson02"
      component={Lesson}
      defaultProps={{ lessonId: "02" }}
      durationInFrames={framesFor(lesson02.blocks, lesson02.durationOf as never)}
      fps={FPS}
      width={WIDTH}
      height={HEIGHT}
    />
  </>
);
