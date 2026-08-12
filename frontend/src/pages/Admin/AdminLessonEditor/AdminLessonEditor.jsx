import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { deleteAdminLesson, getAdminLesson, uploadAdminThumbnail } from '../../../api/admin'
import { getLessonThumbnailUrl } from '../../../api/courses'
import ThumbnailUploader from '../../../components/ThumbnailUploader/ThumbnailUploader'
import DetailsForm from './DetailsForm'
import VideoUploader from './VideoUploader'
import QuestionsEditor from './QuestionsEditor'
import styles from './AdminLessonEditor.module.css'

function AdminLessonEditor() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [state, setState] = useState({ status: 'loading', lesson: null })
  const [deleteError, setDeleteError] = useState('')
  const [detailsDirty, setDetailsDirty] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [detectedDuration, setDetectedDuration] = useState(null)

  const hasUnsavedWork = detailsDirty || uploading

  const refresh = useCallback(() => {
    return getAdminLesson(id)
      .then((lesson) => setState({ status: 'loaded', lesson }))
      .catch(() => setState({ status: 'error', lesson: null }))
  }, [id])

  useEffect(() => {
    setState({ status: 'loading', lesson: null })
    refresh()
  }, [id, refresh])

  useEffect(() => {
    function handleBeforeUnload(event) {
      if (!hasUnsavedWork) return
      event.preventDefault()
      event.returnValue = ''
    }
    window.addEventListener('beforeunload', handleBeforeUnload)
    return () => window.removeEventListener('beforeunload', handleBeforeUnload)
  }, [hasUnsavedWork])

  function handleBackClick(event) {
    if (hasUnsavedWork && !window.confirm('You have unsaved changes. Leave this page?')) {
      event.preventDefault()
    }
  }

  async function handleDelete() {
    if (!window.confirm(`Delete "${state.lesson.title}"? This cannot be undone.`)) return
    setDeleteError('')
    try {
      await deleteAdminLesson(id)
      navigate(`/admin/courses/${state.lesson.course_id}`)
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
  const backTo = `/admin/courses/${lesson.course_id}`

  return (
    <div className={styles.page}>
      <Link to={backTo} className={styles.back} onClick={handleBackClick}>
        &larr; Back to course
      </Link>
      <div className={styles.headerRow}>
        <h1 className={styles.heading}>{lesson.title}</h1>
        <span className={`${styles.badge} ${lesson.is_published ? styles.published : styles.draft}`}>
          {lesson.is_published ? 'Published' : 'Draft'}
        </span>
      </div>
      <p className={styles.message}>
        Publishing happens for the whole course. Once every lesson is complete, publish the course from{' '}
        <Link to={backTo}>its editor</Link>.
      </p>

      <DetailsForm
        lesson={lesson}
        detectedDuration={detectedDuration}
        onDirtyChange={setDetailsDirty}
        onChange={refresh}
      />
      <VideoUploader
        lesson={lesson}
        onDurationDetected={setDetectedDuration}
        onUploadingChange={setUploading}
        onChange={refresh}
      />
      <ThumbnailUploader
        item={lesson}
        uploadThumbnail={uploadAdminThumbnail}
        fetchThumbnailUrl={() => getLessonThumbnailUrl(lesson.course_slug, lesson.slug)}
        onUploadingChange={setUploading}
        onChange={refresh}
      />
      <QuestionsEditor lesson={lesson} onChange={refresh} />

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
