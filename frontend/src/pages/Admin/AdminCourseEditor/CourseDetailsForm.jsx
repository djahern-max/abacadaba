import { useEffect, useState } from 'react'
import { updateAdminCourse } from '../../../api/admin'
import styles from '../AdminLessonEditor/DetailsForm.module.css'

function CourseDetailsForm({ course, onDirtyChange, onChange }) {
  const [title, setTitle] = useState(course.title)
  const [slug, setSlug] = useState(course.slug)
  const [description, setDescription] = useState(course.description)
  const [cooldownMinutes, setCooldownMinutes] = useState(course.retake_cooldown_minutes)
  const [maxAttempts, setMaxAttempts] = useState(course.max_attempts ?? '')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const dirty =
    title !== course.title ||
    slug !== course.slug ||
    description !== course.description ||
    Number(cooldownMinutes) !== course.retake_cooldown_minutes ||
    String(maxAttempts) !== String(course.max_attempts ?? '')

  useEffect(() => {
    onDirtyChange?.(dirty)
  }, [dirty, onDirtyChange])

  async function handleSave(event) {
    event.preventDefault()
    setError('')
    setSaving(true)
    try {
      await updateAdminCourse(course.id, {
        title,
        slug,
        description,
        retake_cooldown_minutes: Number(cooldownMinutes),
        max_attempts: maxAttempts === '' ? null : Number(maxAttempts),
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
        <label className={styles.label} htmlFor="course-title">
          Title
        </label>
        <input
          id="course-title"
          className={styles.input}
          value={title}
          onChange={(event) => setTitle(event.target.value)}
        />

        <label className={styles.label} htmlFor="course-slug">
          Slug
        </label>
        <input
          id="course-slug"
          className={styles.input}
          value={slug}
          onChange={(event) => setSlug(event.target.value)}
        />
        {course.is_published && slug !== course.slug && (
          <p className={styles.warning}>
            Changing the slug of a published course breaks any links already shared.
          </p>
        )}

        <label className={styles.label} htmlFor="course-description">
          Description
        </label>
        <textarea
          id="course-description"
          className={styles.textarea}
          rows={4}
          value={description}
          onChange={(event) => setDescription(event.target.value)}
        />

        <label className={styles.label} htmlFor="course-cooldown-minutes">
          Retake cooldown (minutes)
        </label>
        <input
          id="course-cooldown-minutes"
          className={styles.input}
          type="number"
          min="0"
          value={cooldownMinutes}
          onChange={(event) => setCooldownMinutes(event.target.value)}
        />
        <p className={styles.hint}>Blank or 0 means no cooldown between attempts.</p>

        <label className={styles.label} htmlFor="course-max-attempts">
          Max attempts
        </label>
        <input
          id="course-max-attempts"
          className={styles.input}
          type="number"
          min="1"
          value={maxAttempts}
          onChange={(event) => setMaxAttempts(event.target.value)}
        />
        <p className={styles.hint}>Blank means unlimited attempts.</p>

        {error && <p className={styles.fieldError}>{error}</p>}
        <button type="submit" className={styles.button} disabled={!dirty || saving}>
          {saving ? 'Saving…' : 'Save details'}
        </button>
      </form>
    </section>
  )
}

export default CourseDetailsForm
