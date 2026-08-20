import React from "react";
import { AbsoluteFill, Sequence, Audio, staticFile } from "remotion";
import { blocks, durationOf, revealsOf, hasAudio } from "./lesson-01";
import { Sheet } from "./Sheet";
import { SLIDES } from "./slides";
import { seconds } from "./theme";

/**
 * Sequences the blocks back to back.
 *
 * Every duration comes from the data file, so there is no timing number in
 * this component. When measured audio replaces the estimates, this file does
 * not change.
 *
 * Audio is optional per block. A block with no audio file renders silent,
 * which is what lets you judge the visuals before generating narration.
 */

export const Lesson: React.FC = () => {
  let cursor = 0;

  return (
    <AbsoluteFill>
      {blocks.map((block) => {
        const from = cursor;
        const durationInFrames = seconds(durationOf(block));
        cursor += durationInFrames;

        const Slide = SLIDES[block.slide as keyof typeof SLIDES];

        return (
          <Sequence
            key={block.id}
            from={from}
            durationInFrames={durationInFrames}
            name={`${block.sheet} ${block.slide}`}
          >
            <Sheet sheet={block.sheet} citation={block.citation}>
              <Slide reveals={revealsOf(block)} />
            </Sheet>
            {hasAudio(block) ? (
              <Audio src={staticFile(`audio/${block.id}.mp3`)} />
            ) : null}
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
