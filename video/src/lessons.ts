import * as lesson01 from "./lesson-01";
import * as lesson02 from "./lesson-02";
import * as lesson03 from "./lesson-03";
import * as lesson04 from "./lesson-04";
import * as lesson05 from "./lesson-05";
import * as lesson06 from "./lesson-06";

export const LESSONS = {
  "01": lesson01, "02": lesson02, "03": lesson03, "04": lesson04, "05": lesson05, "06": lesson06,
} as const;
export type LessonId = keyof typeof LESSONS;
