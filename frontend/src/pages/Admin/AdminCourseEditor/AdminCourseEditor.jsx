import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useBlocker, useNavigate, useParams } from 'react-router-dom'
import { checkAdminCoursePublish, deleteAdminCourse, getAdminCourse, uploadAdminCourseThumbnail } from '../../../api/admin'
import { getCourseThumbnailUrl } from '../../../api/courses'
import ThumbnailUploader from '../../../components/ThumbnailUploader/ThumbnailUploader'
import StickySaveBar from '../../../components/StickySaveBar/StickySaveBar'
import Button from '../../../components/Button/Button'
import CourseDetailsForm from './CourseDetailsForm'
import ObjectivesPanel from './ObjectivesPanel'
import LessonsPanel from './LessonsPanel'
import CoursePublishPanel from './CoursePublishPanel'
import styles from '../AdminLessonEditor/AdminLessonEditor.module.css'

function AdminCourseEditor() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [state, setState] = useState({ status: 'loading', course: null })
  const [publishErrors, setPublishErrors] = useState([])
  const [deleteError, setDeleteError] = useState('')
  const [detailsDirty, setDetailsDirty] = useState(0)
  const [objectivesDirty, setObjectivesDirty] = useState(0)
  const [uploading, setUploading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState('')

  const detailsRef = useRef(null)
  const objectivesRef = useRef(null)

  const totalDirty = detailsDirty + objectivesDirty
  const hasUnsavedWork = totalDirty > 0 || uploading

  const refresh = useCallback(() => {
    return getAdminCourse(id)
      .then((course) => {
        setState({ status: 'loaded', course })
        return checkAdminCoursePublish(id).then((result) => setPublishErrors(result.errors))
      })
      .catch(() => setState({ status: 'error', course: null }))
  }, [id])

  useEffect(() => {
    setState({ status: 'loading', course: null })
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

  const shouldBlock = useCallback(
    ({ currentLocation, nextLocation }) => hasUnsavedWork && currentLocation.pathname !== nextLocation.pathname,
    [hasUnsavedWork],
  )
  const blocker = useBlocker(shouldBlock)

  useEffect(() => {
    if (blocker.state !== 'blocked') return
    if (window.confirm('You have unsaved changes. Leave this page?')) {
      blocker.proceed()
    } else {
      blocker.reset()
    }
  }, [blocker])

  async function handleSaveAll() {
    setSaveError('')
    setSaving(true)
    try {
      const tasks = []
      if (detailsDirty > 0) tasks.push(detailsRef.current.save())
      if (objectivesDirty > 0) tasks.push(objectivesRef.current.save())
      await Promise.all(tasks)
      await refresh()
    } catch {
      setSaveError('Could not save your changes. Try again.')
    } finally {
      setSaving(false)
    }
  }

  useEffect(() => {
    function handleKeyDown(event) {
      const key = event.key.toLowerCase()
      if (!(event.metaKey || event.ctrlKey) || key !== 's') return
      event.preventDefault()
      if (totalDirty > 0 && !saving) handleSaveAll()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [totalDirty, saving, handleSaveAll])

  async function handleDelete() {
    if (!window.confirm(`Delete "${state.course.title}"? This cannot be undone.`)) return
    setDeleteError('')
    try {
      await deleteAdminCourse(id)
      navigate('/admin')
    } catch (error) {
      const detail = Array.isArray(error.body?.detail) ? error.body.detail.join(', ') : error.body?.detail
      setDeleteError(detail ?? 'Could not delete this course.')
    }
  }

  if (state.status === 'loading') {
    return <p className={styles.message}>Loading&hellip;</p>
  }
  if (state.status === 'error') {
    return <p className={styles.message}>Couldn&apos;t load this course.</p>
  }

  const { course } = state

  return (
    <div className={styles.page}>
      <Link to="/admin" className={styles.back}>
        &larr; All courses
      </Link>
      <div className={styles.headerRow}>
        <h1 className={styles.heading}>{course.title}</h1>
        <span className={`${styles.badge} ${course.is_published ? styles.published : styles.draft}`}>
          {course.is_published ? 'Published' : 'Draft'}
        </span>
        <Link to={`/admin/courses/${course.id}/stats`} className={styles.statsLink}>
          View stats
        </Link>
        <Button
          variant="primary"
          className={styles.headerSaveButton}
          onClick={handleSaveAll}
          disabled={totalDirty === 0 || saving}
        >
          {saving ? 'Saving…' : 'Save'}
        </Button>
      </div>

      <CourseDetailsForm ref={detailsRef} course={course} onDirtyChange={setDetailsDirty} />
      <ThumbnailUploader
        item={course}
        label="Course thumbnail"
        placementNote="Shown on the course card in the catalog."
        uploadThumbnail={uploadAdminCourseThumbnail}
        fetchThumbnailUrl={() => getCourseThumbnailUrl(course.slug)}
        onUploadingChange={setUploading}
        onChange={refresh}
      />
      <ObjectivesPanel ref={objectivesRef} course={course} onDirtyChange={setObjectivesDirty} onChange={refresh} />
      <LessonsPanel course={course} onChange={refresh} />
      <CoursePublishPanel
        course={course}
        publishErrors={publishErrors}
        hasUnsavedWork={hasUnsavedWork}
        onPublishErrors={setPublishErrors}
        onChange={refresh}
      />

      <section className={styles.dangerZone}>
        <Button variant="danger" onClick={handleDelete}>
          Delete course
        </Button>
        {deleteError && <p className={styles.fieldError}>{deleteError}</p>}
      </section>

      <StickySaveBar count={totalDirty} saving={saving} error={saveError} onSave={handleSaveAll} />
    </div>
  )
}

export default AdminCourseEditor
