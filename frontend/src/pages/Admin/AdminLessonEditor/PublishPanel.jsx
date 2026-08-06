import { publishAdminLesson, unpublishAdminLesson } from '../../../api/admin'
import styles from './PublishPanel.module.css'

function PublishPanel({ lesson, publishErrors, onPublishErrors, onChange }) {
  async function handlePublish() {
    try {
      await publishAdminLesson(lesson.id)
      onPublishErrors([])
      await onChange()
    } catch (error) {
      onPublishErrors(Array.isArray(error.body?.detail) ? error.body.detail : ['Could not publish this lesson.'])
    }
  }

  async function handleUnpublish() {
    await unpublishAdminLesson(lesson.id)
    onPublishErrors([])
    await onChange()
  }

  return (
    <section className={styles.section}>
      <h2 className={styles.heading}>Publish</h2>
      {publishErrors.length > 0 && (
        <ul className={styles.checklist}>
          {publishErrors.map((message) => (
            <li key={message}>{message}</li>
          ))}
        </ul>
      )}
      {lesson.is_published ? (
        <button type="button" className={styles.button} onClick={handleUnpublish}>
          Unpublish
        </button>
      ) : (
        <button
          type="button"
          className={styles.button}
          onClick={handlePublish}
          disabled={publishErrors.length > 0}
        >
          Publish
        </button>
      )}
    </section>
  )
}

export default PublishPanel
