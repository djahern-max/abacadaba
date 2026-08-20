import { interpolate, spring } from "remotion";
import { FPS } from "./theme";

/**
 * Reveal timing.
 *
 * Content appears when the narrator reaches it, not on a decorative schedule.
 * The `reveals` array on each block holds seconds from block start; these
 * helpers turn one of those into an opacity and a small vertical offset.
 *
 * Deliberately understated. A participant is listening to a technical
 * explanation for eight minutes; slides that slide, bounce, or fade at length
 * compete with the narration instead of supporting it. 12 frames, 10px, done.
 */

export const revealAt = (frame: number, atSeconds: number) => {
  const start = atSeconds * FPS;
  const progress = interpolate(frame, [start, start + 12], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return {
    opacity: progress,
    transform: `translateY(${(1 - progress) * 10}px)`,
  };
};

/** Has this reveal happened yet? For state changes rather than fades. */
export const isRevealed = (frame: number, atSeconds: number) =>
  frame >= atSeconds * FPS;

/** One springy moment, used exactly once — the AND gate closing on sheet S-05. */
export const springAt = (frame: number, atSeconds: number) =>
  spring({
    frame: frame - atSeconds * FPS,
    fps: FPS,
    config: { damping: 200, mass: 0.6 },
  });
