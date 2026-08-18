import { forwardRef, useEffect, useImperativeHandle, useRef, useState } from 'react'
import VideoUploader from '../AdminLessonEditor/VideoUploader'
import QuestionsEditor from '../AdminLessonEditor/QuestionsEditor'
import LessonVideoFields from './LessonVideoFields'
import AddSecondSegmentControl from './AddSecondSegmentControl'
import styles from '../AdminLessonEditor/AdminLessonEditor.module.css'

// The course renders collapsed when it has exactly one lesson (feature 019a).
// This bundles everything that lesson needs - video, its duration and watch
// requirement, and its questions - onto the course page, plus the one control
// that expands back to the two-level editor. Lesson title, description,
// thumbnail, and position stay hidden but untouched in the database.
const CollapsedLessonEditor = forwardRef(function CollapsedLessonEditor(
  { course, lesson, onDirtyChange, onUploadingChange, onChange },
  ref,
) {
  const [fieldsDirty, setFieldsDirty] = useState(0)
  const [questionsDirty, setQuestionsDirty] = useState(0)
  const [detectedDuration, setDetectedDuration] = useState(null)
  const fieldsRef = useRef(null)
  const questionsRef = useRef(null)

  const totalDirty = fieldsDirty + questionsDirty

  useEffect(() => {
    onDirtyChange?.(totalDirty)
  }, [totalDirty, onDirtyChange])

  useImperativeHandle(ref, () => ({
    save: async () => {
      const tasks = []
      if (fieldsDirty > 0) tasks.push(fieldsRef.current.save())
      if (questionsDirty > 0) tasks.push(questionsRef.current.save())
      await Promise.all(tasks)
    },
  }))

  return (
    <>
      <VideoUploader
        lesson={lesson}
        onDurationDetected={setDetectedDuration}
        onUploadingChange={onUploadingChange}
        onChange={onChange}
      />
      <section className={styles.section}>
        <h2 className={styles.heading}>Duration and watch requirement</h2>
        <LessonVideoFields
          ref={fieldsRef}
          lesson={lesson}
          detectedDuration={detectedDuration}
          onDirtyChange={setFieldsDirty}
        />
      </section>
      <QuestionsEditor ref={questionsRef} lesson={lesson} onDirtyChange={setQuestionsDirty} onChange={onChange} />
      <AddSecondSegmentControl course={course} />
    </>
  )
})

export default CollapsedLessonEditor
