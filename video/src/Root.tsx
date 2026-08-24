import React from "react";
import { Composition } from "remotion";
import { Lesson } from "./Lesson";
import { LESSONS, LessonId } from "./lessons";
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
      `  Run \`npm run generate -- --lesson <id>\` to produce narration audio, then re-render.\n`
  );
};

const IDS = Object.keys(LESSONS) as LessonId[];

IDS.forEach((id) =>
  warnIfEstimated(`Lesson${id}`, LESSONS[id].usingEstimates, LESSONS[id].totalSeconds)
);

export const RemotionRoot: React.FC = () => (
  <>
    {IDS.map((id) => {
      const lesson = LESSONS[id];
      return (
        <Composition
          key={id}
          id={`Lesson${id}`}
          component={Lesson}
          defaultProps={{ lessonId: id }}
          durationInFrames={framesFor(lesson.blocks, lesson.durationOf as never)}
          fps={FPS}
          width={WIDTH}
          height={HEIGHT}
        />
      );
    })}
  </>
);
