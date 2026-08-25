// One place to put both words when a descriptor needs to read as teaching
// rather than as compliance - see current-feature.md, Part 4. Field of
// study and Expires have no general-course label because they're omitted
// from a general course's payload entirely, not just relabelled.
const PROGRAM_LABELS = {
  cpe: {
    programLevel: 'Program level',
    prerequisites: 'Prerequisites',
    advancePreparation: 'Advance preparation',
    length: 'CPE credit',
    assessment: 'assessment',
  },
  general: {
    programLevel: 'Level',
    prerequisites: 'What you should know first',
    advancePreparation: 'Before you start',
    length: 'Length',
    assessment: 'quiz',
  },
}

export function programLabel(programKind, key) {
  return (PROGRAM_LABELS[programKind] ?? PROGRAM_LABELS.cpe)[key]
}
