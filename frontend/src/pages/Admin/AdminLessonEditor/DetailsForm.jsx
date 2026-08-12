import { useEffect, useState } from 'react'
import { updateAdminLesson } from '../../../api/admin'
import styles from './DetailsForm.module.css'

function DetailsForm({ lesson, detectedDuration, onDirtyChange, onChange }) {
  const [title, setTitle] = useState(lesson.title)
  const [slug, setSlug] = useState(lesson.slug)
  const [description, setDescription] = useState(lesson.description)
  const [duration, setDuration] = useState(lesson.duration_seconds ?? '')
  const [durationAutoFilled, setDurationAutoFilled] = useState(false)
  const [watchPercent, setWatchPercent] = useState(Math.round(lesson.required_watch_ratio * 100))
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const dirty =
    title !== lesson.title ||
    slug !== lesson.slug ||
    description !== lesson.description ||
    String(duration) !== String(lesson.duration_seconds ?? '') ||
    Number(watchPercent) !== Math.round(lesson.required_watch_ratio * 100)

  useEffect(() => {
    onDirtyChange?.(dirty)
  }, [dirty, onDirtyChange])

  useEffect(() => {
    if (detectedDuration == null) return
    setDuration(detectedDuration)
    setDurationAutoFilled(true)
  }, [detectedDuration])

  async function handleSave(event) {
    event.preventDefault()
    setError('')
    setSaving(true)
    try {
      await updateAdminLesson(lesson.id, {
        title,
        slug,
        description,
        duration_seconds: duration === '' ? null : Number(duration),
        required_watch_ratio: Number(watchPercent) / 100,
      })
      await onChange()
    } catch (err) {
      setError(err.body?.detail ?? 'Could not save these details.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <section className={styles.section}>
      <h2 className={styles.heading}>Details</h2>
      <form className={styles.form} onSubmit={handleSave}>
        <label className={styles.label} htmlFor="title">
          Title
        </label>
        <input
          id="title"
          className={styles.input}
          value={title}
          onChange={(event) => setTitle(event.target.value)}
        />

        <label className={styles.label} htmlFor="slug">
          Slug
        </label>
        <input
          id="slug"
          className={styles.input}
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
          className={styles.textarea}
          rows={4}
          value={description}
          onChange={(event) => setDescription(event.target.value)}
        />

        <label className={styles.label} htmlFor="duration">
          Duration (seconds)
        </label>
        <input
          id="duration"
          className={styles.input}
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
          className={styles.input}
          type="number"
          min="0"
          max="100"
          value={watchPercent}
          onChange={(event) => setWatchPercent(event.target.value)}
        />

        {error && <p className={styles.fieldError}>{error}</p>}
        <button type="submit" className={styles.button} disabled={!dirty || saving}>
          {saving ? 'Saving…' : 'Save details'}
        </button>
      </form>
    </section>
  )
}

export default DetailsForm
