import React from "react";
import { AbsoluteFill, Sequence, Audio, staticFile } from "remotion";
import { LESSONS, type LessonId } from "./lessons";
import { Sheet } from "./Sheet";
import { SLIDES } from "./slides";
import { seconds } from "./theme";

/**
 * Sequences the blocks of one lesson back to back.
 *
 * Every duration comes from the data file, so there is no timing number in
 * this component. When measured audio replaces the estimates, this file does
 * not change.
 *
 * Audio is optional per block. A block with no audio file renders silent,
 * which is what lets you judge the visuals before generating narration.
 */

export const Lesson: React.FC<{ lessonId: LessonId }> = ({ lessonId }) => {
  const mod = LESSONS[lessonId] as unknown as {
    blocks: {
      id: string;
      sheet: string;
      citation: string;
      slide: string;
      figure?: unknown;
    }[];
    meta: import("./slides").LessonMeta;
    durationOf: (b: never) => number;
    revealsOf: (b: never) => number[];
    hasAudio: (b: never) => boolean;
  };

  let cursor = 0;

  return (
    <AbsoluteFill>
      {mod.blocks.map((block) => {
        const from = cursor;
        const durationInFrames = seconds(mod.durationOf(block as never));
        cursor += durationInFrames;

        const Slide = SLIDES[block.slide as keyof typeof SLIDES];

        return (
          <Sequence
            key={block.id}
            from={from}
            durationInFrames={durationInFrames}
            name={`${block.sheet} ${block.slide}`}
          >
            <Sheet sheet={block.sheet} citation={block.citation} meta={mod.meta}>
              <Slide
                reveals={mod.revealsOf(block as never)}
                figure={block.figure as never}
                meta={mod.meta}
              />
            </Sheet>
            {mod.hasAudio(block as never) ? (
              <Audio src={staticFile(`audio/${lessonId}/${block.id}.mp3`)} />
            ) : null}
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
