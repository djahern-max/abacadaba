import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useBlocker, useNavigate, useParams } from 'react-router-dom'
import { checkAdminCoursePublish, deleteAdminLesson, getAdminLesson, uploadAdminThumbnail } from '../../../api/admin'
import { getLessonThumbnailUrl } from '../../../api/courses'
import ThumbnailUploader from '../../../components/ThumbnailUploader/ThumbnailUploader'
import StickySaveBar from '../../../components/StickySaveBar/StickySaveBar'
import Button from '../../../components/Button/Button'
import DetailsForm from './DetailsForm'
import VideoUploader from './VideoUploader'
import QuestionsEditor from './QuestionsEditor'
import styles from './AdminLessonEditor.module.css'

const LESSON_MESSAGE_PATTERN = /^Lesson '.+?'\s*/

function AdminLessonEditor() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [state, setState] = useState({ status: 'loading', lesson: null })
  const [deleteError, setDeleteError] = useState('')
  const [detailsDirty, setDetailsDirty] = useState(0)
  const [questionsDirty, setQuestionsDirty] = useState(0)
  const [uploading, setUploading] = useState(false)
  const [detectedDuration, setDetectedDuration] = useState(null)
  const [saving, setSaving] = useState(false)
  const [saveError, setSaveError] = useState('')
  const [outstanding, setOutstanding] = useState(null)

  const detailsRef = useRef(null)
  const questionsRef = useRef(null)

  const totalDirty = detailsDirty + questionsDirty
  const hasUnsavedWork = totalDirty > 0 || uploading

  const refresh = useCallback(() => {
    return getAdminLesson(id)
      .then((lesson) => {
        setState({ status: 'loaded', lesson })
        return checkAdminCoursePublish(lesson.course_id)
          .then((result) =>
            setOutstanding(
              result.errors
                .filter((message) => message.startsWith(`Lesson '${lesson.title}'`))
                .map((message) => message.replace(LESSON_MESSAGE_PATTERN, '')),
            ),
          )
          .catch(() => setOutstanding(null))
      })
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
      if (questionsDirty > 0) tasks.push(questionsRef.current.save())
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
      <Link to={backTo} className={styles.back}>
        &larr; Back to course
      </Link>
      <div className={styles.headerRow}>
        <h1 className={styles.heading}>{lesson.title}</h1>
        <span className={`${styles.badge} ${lesson.is_published ? styles.published : styles.draft}`}>
          {lesson.is_published ? 'Published' : 'Draft'}
        </span>
        <Button
          variant="primary"
          className={styles.headerSaveButton}
          onClick={handleSaveAll}
          disabled={totalDirty === 0 || saving}
        >
          {saving ? 'Saving…' : 'Save'}
        </Button>
      </div>
      <p className={styles.message}>
        Publishing happens for the whole course. Once every lesson is complete, publish the course from{' '}
        <Link to={backTo}>its editor</Link>.
      </p>

      <DetailsForm
        ref={detailsRef}
        lesson={lesson}
        detectedDuration={detectedDuration}
        onDirtyChange={setDetailsDirty}
      />
      <VideoUploader
        lesson={lesson}
        onDurationDetected={setDetectedDuration}
        onUploadingChange={setUploading}
        onChange={refresh}
      />
      <ThumbnailUploader
        item={lesson}
        label="Lesson thumbnail"
        placementNote="The poster frame shown before this segment's video plays."
        uploadThumbnail={uploadAdminThumbnail}
        fetchThumbnailUrl={() => getLessonThumbnailUrl(lesson.course_slug, lesson.slug)}
        onUploadingChange={setUploading}
        onChange={refresh}
      />
      <QuestionsEditor ref={questionsRef} lesson={lesson} onDirtyChange={setQuestionsDirty} onChange={refresh} />

      <section className={styles.nextStep}>
        <h2 className={styles.heading}>Next</h2>
        {outstanding === null ? (
          <p className={styles.message}>Checking what's still outstanding&hellip;</p>
        ) : outstanding.length === 0 ? (
          <p className={styles.message}>This lesson meets all publish requirements.</p>
        ) : (
          <>
            <p className={styles.message}>Still needed before the course can publish:</p>
            <ul className={styles.outstandingList}>
              {outstanding.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </>
        )}
        <Link to={backTo} className={styles.nextStepLink}>
          &larr; Back to course
        </Link>
      </section>

      <section className={styles.dangerZone}>
        <Button variant="danger" onClick={handleDelete}>
          Delete lesson
        </Button>
        {deleteError && <p className={styles.fieldError}>{deleteError}</p>}
      </section>

      <StickySaveBar count={totalDirty} saving={saving} error={saveError} onSave={handleSaveAll} />
    </div>
  )
}

export default AdminLessonEditor
