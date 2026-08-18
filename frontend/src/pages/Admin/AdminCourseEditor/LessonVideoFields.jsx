import { forwardRef, useEffect, useImperativeHandle, useState } from 'react'
import { updateAdminLesson } from '../../../api/admin'
import styles from '../AdminLessonEditor/DetailsForm.module.css'

const LessonVideoFields = forwardRef(function LessonVideoFields({ lesson, detectedDuration, onDirtyChange }, ref) {
  const [duration, setDuration] = useState(lesson.duration_seconds ?? '')
  const [durationAutoFilled, setDurationAutoFilled] = useState(false)
  const [watchPercent, setWatchPercent] = useState(Math.round(lesson.required_watch_ratio * 100))

  const durationDirty = String(duration) !== String(lesson.duration_seconds ?? '')
  const watchPercentDirty = Number(watchPercent) !== Math.round(lesson.required_watch_ratio * 100)
  const dirty = durationDirty || watchPercentDirty

  useEffect(() => {
    onDirtyChange?.(dirty ? 1 : 0)
  }, [dirty, onDirtyChange])

  useEffect(() => {
    if (detectedDuration == null) return
    setDuration(detectedDuration)
    setDurationAutoFilled(true)
  }, [detectedDuration])

  useImperativeHandle(ref, () => ({
    save: () =>
      updateAdminLesson(lesson.id, {
        duration_seconds: duration === '' ? null : Number(duration),
        required_watch_ratio: Number(watchPercent) / 100,
      }),
  }))

  return (
    <div className={styles.form}>
      <label className={styles.label} htmlFor="segment-duration">
        Duration (seconds)
      </label>
      <input
        id="segment-duration"
        className={`${styles.input} ${durationDirty ? styles.fieldDirty : ''}`}
        type="number"
        min="0"
        value={duration}
        onChange={(event) => {
          setDuration(event.target.value)
          setDurationAutoFilled(false)
        }}
      />
      {durationAutoFilled && (
        <p className={styles.hint}>Filled in from the video you selected. Still editable.</p>
      )}
      {duration === '' && (
        <p className={styles.warning}>
          No duration set, so the watch requirement below cannot apply. This segment will be ungated.
        </p>
      )}

      <label className={styles.label} htmlFor="segment-watch-percent">
        Required watch percentage
      </label>
      <input
        id="segment-watch-percent"
        className={`${styles.input} ${watchPercentDirty ? styles.fieldDirty : ''}`}
        type="number"
        min="0"
        max="100"
        value={watchPercent}
        onChange={(event) => setWatchPercent(event.target.value)}
      />
    </div>
  )
})

export default LessonVideoFields
