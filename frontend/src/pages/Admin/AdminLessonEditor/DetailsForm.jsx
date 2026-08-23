import { forwardRef, useEffect, useImperativeHandle, useState } from 'react'
import { updateAdminLesson } from '../../../api/admin'
import styles from './DetailsForm.module.css'

const DetailsForm = forwardRef(function DetailsForm({ lesson, detectedDuration, onDirtyChange }, ref) {
  const [title, setTitle] = useState(lesson.title)
  const [slug, setSlug] = useState(lesson.slug)
  const [description, setDescription] = useState(lesson.description)
  const [duration, setDuration] = useState(lesson.duration_seconds ?? '')
  const [durationAutoFilled, setDurationAutoFilled] = useState(false)
  const [watchPercent, setWatchPercent] = useState(Math.round(lesson.required_watch_ratio * 100))
  const [additionalLearning, setAdditionalLearning] = useState(lesson.av_is_additional_learning)
  const [wordCount, setWordCount] = useState(lesson.word_count)

  const titleDirty = title !== lesson.title
  const slugDirty = slug !== lesson.slug
  const descriptionDirty = description !== lesson.description
  const durationDirty = String(duration) !== String(lesson.duration_seconds ?? '')
  const watchPercentDirty = Number(watchPercent) !== Math.round(lesson.required_watch_ratio * 100)
  const additionalLearningDirty = additionalLearning !== lesson.av_is_additional_learning
  const wordCountDirty = Number(wordCount) !== lesson.word_count

  const dirty =
    titleDirty ||
    slugDirty ||
    descriptionDirty ||
    durationDirty ||
    watchPercentDirty ||
    additionalLearningDirty ||
    wordCountDirty

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
        title,
        slug,
        description,
        duration_seconds: duration === '' ? null : Number(duration),
        required_watch_ratio: Number(watchPercent) / 100,
        av_is_additional_learning: additionalLearning,
        word_count: wordCount === '' ? 0 : Number(wordCount),
      }),
  }))

  return (
    <section className={styles.section}>
      <h2 className={styles.heading}>Details</h2>
      <div className={styles.form}>
        <label className={styles.label} htmlFor="title">
          Title
        </label>
        <input
          id="title"
          className={`${styles.input} ${titleDirty ? styles.fieldDirty : ''}`}
          value={title}
          onChange={(event) => setTitle(event.target.value)}
        />

        <label className={styles.label} htmlFor="slug">
          Slug
        </label>
        <input
          id="slug"
          className={`${styles.input} ${slugDirty ? styles.fieldDirty : ''}`}
          value={slug}
          onChange={(event) => setSlug(event.target.value)}
        />
        {lesson.is_published && slug !== lesson.slug && (
          <p className={styles.warning}>
            Changing the slug of a published lesson breaks any links already shared.
          </p>
        )}

        <label className={styles.label} htmlFor="description">
          Description
        </label>
        <textarea
          id="description"
          className={`${styles.textarea} ${descriptionDirty ? styles.fieldDirty : ''}`}
          rows={4}
          value={description}
          onChange={(event) => setDescription(event.target.value)}
        />
        <p className={styles.hint}>A short blurb for this segment in the course&apos;s lesson list.</p>

        <label className={styles.label} htmlFor="duration">
          Duration (seconds)
        </label>
        <input
          id="duration"
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

        <label className={styles.label} htmlFor="watch-percent">
          Required watch percentage
        </label>
        <input
          id="watch-percent"
          className={`${styles.input} ${watchPercentDirty ? styles.fieldDirty : ''}`}
          type="number"
          min="0"
          max="100"
          value={watchPercent}
          onChange={(event) => setWatchPercent(event.target.value)}
        />

        <label className={styles.label} htmlFor="additional-learning">
          <input
            id="additional-learning"
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
            <label className={styles.label} htmlFor="word-count">
              Word count
            </label>
            <input
              id="word-count"
              className={`${styles.input} ${wordCountDirty ? styles.fieldDirty : ''}`}
              type="number"
              min="0"
              value={wordCount}
              onChange={(event) => setWordCount(event.target.value)}
            />
          </>
        )}
      </div>
    </section>
  )
})

export default DetailsForm
