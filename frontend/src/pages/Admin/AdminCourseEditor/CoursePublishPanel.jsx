import { publishAdminCourse, unpublishAdminCourse } from '../../../api/admin'
import styles from '../AdminLessonEditor/PublishPanel.module.css'

const FIXED_CHECKS = [
  { label: 'Title', message: 'Title is required' },
  { label: 'Slug', message: 'Slug is required' },
  { label: 'Description', message: 'Description is required' },
  { label: 'At least one lesson', message: 'Course must have at least one lesson' },
]

function CoursePublishPanel({ course, publishErrors, detailsDirty, onPublishErrors, onChange }) {
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

  const fixedMessages = new Set(FIXED_CHECKS.map((check) => check.message))
  const lessonErrors = publishErrors.filter((message) => !fixedMessages.has(message))
  const publishDisabled = detailsDirty || publishErrors.length > 0

  return (
    <section className={styles.section}>
      <h2 className={styles.heading}>Publish</h2>
      <ul className={styles.checklist}>
        {FIXED_CHECKS.map((check) => {
          const met = !publishErrors.includes(check.message)
          return (
            <li key={check.label} className={met ? styles.checklistItemMet : styles.checklistItem}>
              <span aria-hidden="true">{met ? '✓' : '○'}</span> {check.label}
            </li>
          )
        })}
        {lessonErrors.length === 0 ? (
          <li className={styles.checklistItemMet}>
            <span aria-hidden="true">✓</span> Every lesson has a video, at least one question, and each
            question has exactly one correct choice
          </li>
        ) : (
          lessonErrors.map((message) => (
            <li key={message} className={styles.checklistItem}>
              <span aria-hidden="true">○</span> {message}
            </li>
          ))
        )}
      </ul>
      {course.is_published ? (
        <button type="button" className={styles.button} onClick={handleUnpublish}>
          Unpublish
        </button>
      ) : (
        <>
          <button type="button" className={styles.button} onClick={handlePublish} disabled={publishDisabled}>
            Publish
          </button>
          {detailsDirty && <p className={styles.reason}>Save your details first.</p>}
        </>
      )}
    </section>
  )
}

export default CoursePublishPanel
