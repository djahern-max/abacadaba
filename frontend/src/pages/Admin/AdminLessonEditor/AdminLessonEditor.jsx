import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { deleteAdminLesson, getAdminLesson } from '../../../api/admin'
import DetailsForm from './DetailsForm'
import VideoUploader from './VideoUploader'
import QuestionsEditor from './QuestionsEditor'
import PublishPanel from './PublishPanel'
import styles from './AdminLessonEditor.module.css'

function AdminLessonEditor() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [state, setState] = useState({ status: 'loading', lesson: null })
  const [publishErrors, setPublishErrors] = useState([])
  const [deleteError, setDeleteError] = useState('')

  const refresh = useCallback(() => {
    setPublishErrors([])
    return getAdminLesson(id)
      .then((lesson) => setState({ status: 'loaded', lesson }))
      .catch(() => setState({ status: 'error', lesson: null }))
  }, [id])

  useEffect(() => {
    setState({ status: 'loading', lesson: null })
    refresh()
  }, [id, refresh])

  async function handleDelete() {
    if (!window.confirm(`Delete "${state.lesson.title}"? This cannot be undone.`)) return
    setDeleteError('')
    try {
      await deleteAdminLesson(id)
      navigate('/admin')
    } catch (error) {
      const detail = Array.isArray(error.body?.detail) ? error.body.detail.join(', ') : error.body?.detail
      setDeleteError(detail ?? 'Could not delete this lesson.')
    }
  }

  if (state.status === 'loading') {
    return <p className={styles.message}>Loading&hellip;</p>
  }
  if (state.status === 'error') {
    return <p className={styles.message}>Couldn&apos;t load this lesson.</p>
  }

  const { lesson } = state

  return (
    <div className={styles.page}>
      <Link to="/admin" className={styles.back}>
        &larr; All lessons
      </Link>
      <div className={styles.headerRow}>
        <h1 className={styles.heading}>{lesson.title}</h1>
        <span className={`${styles.badge} ${lesson.is_published ? styles.published : styles.draft}`}>
          {lesson.is_published ? 'Published' : 'Draft'}
        </span>
        <Link to={`/admin/lessons/${lesson.id}/stats`} className={styles.statsLink}>
          View stats
        </Link>
      </div>

      <DetailsForm lesson={lesson} onChange={refresh} />
      <VideoUploader lesson={lesson} onChange={refresh} />
      <QuestionsEditor lesson={lesson} onChange={refresh} />
      <PublishPanel
        lesson={lesson}
        publishErrors={publishErrors}
        onPublishErrors={setPublishErrors}
        onChange={refresh}
      />

      <section className={styles.dangerZone}>
        <button type="button" className={styles.deleteButton} onClick={handleDelete}>
          Delete lesson
        </button>
        {deleteError && <p className={styles.fieldError}>{deleteError}</p>}
      </section>
    </div>
  )
}

export default AdminLessonEditor
