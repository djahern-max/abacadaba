import { publishAdminLesson, unpublishAdminLesson } from '../../../api/admin'
import styles from './PublishPanel.module.css'

const CHECKLIST = [
  { label: 'Title', met: (errors) => !errors.includes('Title is required') },
  { label: 'Slug', met: (errors) => !errors.includes('Slug is required') },
  { label: 'Description', met: (errors) => !errors.includes('Description is required') },
  { label: 'Video uploaded', met: (errors) => !errors.includes('A video must be uploaded') },
  {
    label: '5 questions',
    met: (errors) => !errors.some((message) => message.startsWith('Lesson must have exactly')),
  },
  {
    label: 'Each question has exactly one correct choice',
    met: (errors) =>
      !errors.some((message) => message.includes('correct choice') || message.includes('needs at least')),
  },
]

function PublishPanel({ lesson, publishErrors, detailsDirty, onPublishErrors, onChange }) {
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

  const publishDisabled = detailsDirty || publishErrors.length > 0

  return (
    <section className={styles.section}>
      <h2 className={styles.heading}>Publish</h2>
      <ul className={styles.checklist}>
        {CHECKLIST.map((item) => {
          const met = item.met(publishErrors)
          return (
            <li key={item.label} className={met ? styles.checklistItemMet : styles.checklistItem}>
              <span aria-hidden="true">{met ? '✓' : '○'}</span> {item.label}
            </li>
          )
        })}
      </ul>
      {lesson.is_published ? (
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

export default PublishPanel
