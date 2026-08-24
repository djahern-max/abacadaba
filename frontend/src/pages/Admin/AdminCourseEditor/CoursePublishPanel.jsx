import { Link } from 'react-router-dom'
import { publishAdminCourse, unpublishAdminCourse } from '../../../api/admin'
import Button from '../../../components/Button/Button'
import styles from '../AdminLessonEditor/PublishPanel.module.css'

const FIXED_CHECKS = [
  { label: 'Title', message: 'Title is required' },
  { label: 'Slug', message: 'Slug is required' },
  { label: 'Description', message: 'Description is required' },
  { label: 'At least one lesson', message: 'Course must have at least one lesson' },
  { label: 'Developer', message: 'A developer is required' },
  { label: 'Reviewer', message: 'A reviewer is required' },
  { label: 'Review date', message: 'A review date is required' },
  { label: 'Expiration date', message: 'An expiration date is required for self study programs (9.02.2)' },
  {
    label: 'Credit is up to date',
    messages: ['Credit has not been computed yet', 'This course has changed since credit was last computed'],
  },
]

const LESSON_MESSAGE_PATTERN = /^Lesson '(.+?)'/
const LESSON_MESSAGE_PREFIX = /^Lesson '.+?'\s*/
// Feature 026: a site-wide condition surfacing in a course-level checklist -
// current-feature.md says to word it so the author knows it isn't something
// wrong with their course. Not one of FIXED_CHECKS since the message names
// which policies, so it can't be matched by exact string.
const POLICIES_MESSAGE_PREFIX = "The sponsor's policies are not yet published:"

function lessonForMessage(course, message) {
  const match = message.match(LESSON_MESSAGE_PATTERN)
  if (!match) return null
  return course.lessons.find((lesson) => lesson.title === match[1]) ?? null
}

function CoursePublishPanel({ course, publishErrors, hasUnsavedWork, onPublishErrors, onChange }) {
  async function handlePublish() {
    try {
      await publishAdminCourse(course.id)
      onPublishErrors([])
      await onChange()
    } catch (error) {
      onPublishErrors(
        Array.isArray(error.body?.detail) ? error.body.detail : ['Could not publish this course.'],
      )
    }
  }

  async function handleUnpublish() {
    await unpublishAdminCourse(course.id)
    onPublishErrors([])
    await onChange()
  }

  const fixedMessages = new Set(FIXED_CHECKS.flatMap((check) => check.messages ?? [check.message]))
  const policiesError = publishErrors.find((message) => message.startsWith(POLICIES_MESSAGE_PREFIX))
  const lessonErrors = publishErrors.filter(
    (message) => !fixedMessages.has(message) && message !== policiesError,
  )
  const publishDisabled = hasUnsavedWork || publishErrors.length > 0
  // A collapsed (single-lesson) course has no second lesson to disambiguate
  // from, so the "Lesson 'X'" prefix names a field the author can't even
  // see, and the link to that lesson's editor has nowhere useful to go.
  const singleLesson = course.lessons.length === 1

  return (
    <section className={styles.section}>
      <h2 className={styles.heading}>Publish</h2>
      <ul className={styles.checklist}>
        {FIXED_CHECKS.map((check) => {
          const messages = check.messages ?? [check.message]
          const met = !messages.some((message) => publishErrors.includes(message))
          return (
            <li key={check.label} className={met ? styles.checklistItemMet : styles.checklistItem}>
              <span aria-hidden="true">{met ? '✓' : '○'}</span> {check.label}
            </li>
          )
        })}
        <li className={policiesError ? styles.checklistItem : styles.checklistItemMet}>
          <span aria-hidden="true">{policiesError ? '○' : '✓'}</span>{' '}
          {policiesError ? (
            <>
              {policiesError} <Link to="/admin/policies">Write them here.</Link>
            </>
          ) : (
            "Sponsor's policies are published"
          )}
        </li>
        {course.lessons.length === 0 ? (
          // A per-lesson rule has nothing to check against zero lessons — vacuously
          // true is not the same as satisfied, so this renders neutral, not met.
          <li className={styles.checklistItem}>
            <span aria-hidden="true">○</span> Every lesson has a video with a duration (if it counts toward
            credit), at least one question, and each question has exactly one correct choice
          </li>
        ) : lessonErrors.length === 0 ? (
          <li className={styles.checklistItemMet}>
            <span aria-hidden="true">✓</span> Every lesson has a video with a duration (if it counts toward
            credit), at least one question, and each question has exactly one correct choice
          </li>
        ) : (
          lessonErrors.map((message) => {
            const lesson = lessonForMessage(course, message)
            const display = singleLesson ? message.replace(LESSON_MESSAGE_PREFIX, '') : message
            return (
              <li key={message} className={styles.checklistItem}>
                <span aria-hidden="true">○</span>{' '}
                {lesson && !singleLesson ? (
                  <Link to={`/admin/lessons/${lesson.id}`} className={styles.lessonLink}>
                    {display}
                  </Link>
                ) : (
                  display
                )}
              </li>
            )
          })
        )}
      </ul>
      {course.is_published ? (
        <Button variant="primary" onClick={handleUnpublish}>
          Unpublish
        </Button>
      ) : (
        <>
          <Button variant="primary" onClick={handlePublish} disabled={publishDisabled}>
            Publish
          </Button>
          {hasUnsavedWork && <p className={styles.reason}>Save your changes first.</p>}
        </>
      )}
    </section>
  )
}

export default CoursePublishPanel
