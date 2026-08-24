import * as lesson01 from "./lesson-01";
import * as lesson02 from "./lesson-02";

export const LESSONS = { "01": lesson01, "02": lesson02 } as const;
export type LessonId = keyof typeof LESSONS;
