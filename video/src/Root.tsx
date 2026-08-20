import React from "react";
import { Composition } from "remotion";
import { Lesson } from "./Lesson";
import { blocks, durationOf, totalSeconds, usingEstimates } from "./lesson-01";
import { FPS, WIDTH, HEIGHT, seconds } from "./theme";

// Sum the frames the same way Lesson.tsx does, so the composition length can
// never drift from the content. The credit calculation depends on this number
// being the real runtime, which is why it is derived rather than typed in.
const durationInFrames = blocks.reduce(
  (sum, b) => sum + seconds(durationOf(b)),
  0
);

if (usingEstimates) {
  console.warn(
    `\n[abacadaba] Rendering with ESTIMATED block durations.\n` +
      `  Runtime: ${Math.floor(totalSeconds / 60)}m ${Math.round(totalSeconds % 60)}s (estimated)\n` +
      `  Do not use this figure for the CPE credit calculation.\n` +
      `  Run \`npm run generate\` to produce the narration audio, then re-render.\n`
  );
}

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="Lesson01"
      component={Lesson}
      durationInFrames={durationInFrames}
      fps={FPS}
      width={WIDTH}
      height={HEIGHT}
    />
  </>
);
