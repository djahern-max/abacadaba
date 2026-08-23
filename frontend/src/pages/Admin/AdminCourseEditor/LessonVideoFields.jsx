import { forwardRef, useEffect, useImperativeHandle, useState } from 'react'
import { updateAdminLesson } from '../../../api/admin'
import styles from '../AdminLessonEditor/DetailsForm.module.css'

const LessonVideoFields = forwardRef(function LessonVideoFields({ lesson, detectedDuration, onDirtyChange }, ref) {
  const [duration, setDuration] = useState(lesson.duration_seconds ?? '')
  const [durationAutoFilled, setDurationAutoFilled] = useState(false)
  const [watchPercent, setWatchPercent] = useState(Math.round(lesson.required_watch_ratio * 100))
  const [additionalLearning, setAdditionalLearning] = useState(lesson.av_is_additional_learning)
  const [wordCount, setWordCount] = useState(lesson.word_count)

  const durationDirty = String(duration) !== String(lesson.duration_seconds ?? '')
  const watchPercentDirty = Number(watchPercent) !== Math.round(lesson.required_watch_ratio * 100)
  const additionalLearningDirty = additionalLearning !== lesson.av_is_additional_learning
  const wordCountDirty = Number(wordCount) !== lesson.word_count
  const dirty = durationDirty || watchPercentDirty || additionalLearningDirty || wordCountDirty

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
        av_is_additional_learning: additionalLearning,
        word_count: wordCount === '' ? 0 : Number(wordCount),
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

      <label className={styles.label} htmlFor="segment-additional-learning">
        <input
          id="segment-additional-learning"
          type="checkbox"
          checked={additionalLearning}
          onChange={(event) => setAdditionalLearning(event.target.checked)}
        />{' '}
        This segment&apos;s audio teaches something the slides don&apos;t say
      </label>
      <p className={styles.hint}>
        {additionalLearning
          ? "Checked: this segment's runtime counts toward the course's CPE credit (7.02.7)."
          : "Unchecked: the audio is narration of the on-screen text, not additional learning - its runtime doesn't count. Enter the word count below instead (7.02.6)."}
      </p>

      {!additionalLearning && (
        <>
          <label className={styles.label} htmlFor="segment-word-count">
            Word count
          </label>
          <input
            id="segment-word-count"
            className={`${styles.input} ${wordCountDirty ? styles.fieldDirty : ''}`}
            type="number"
            min="0"
            value={wordCount}
            onChange={(event) => setWordCount(event.target.value)}
          />
        </>
      )}
    </div>
  )
})

export default LessonVideoFields
