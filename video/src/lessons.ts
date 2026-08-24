import * as lesson01 from "./lesson-01";

export const LESSONS = { "01": lesson01 } as const;
export type LessonId = keyof typeof LESSONS;
