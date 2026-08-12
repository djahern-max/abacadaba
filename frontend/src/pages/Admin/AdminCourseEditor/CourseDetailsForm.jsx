import { useEffect, useState } from 'react'
import { updateAdminCourse } from '../../../api/admin'
import { getFieldsOfStudy, getProgramLevels } from '../../../api/meta'
import styles from '../AdminLessonEditor/DetailsForm.module.css'

function CourseDetailsForm({ course, onDirtyChange, onChange }) {
  const [title, setTitle] = useState(course.title)
  const [slug, setSlug] = useState(course.slug)
  const [description, setDescription] = useState(course.description)
  const [cooldownMinutes, setCooldownMinutes] = useState(course.retake_cooldown_minutes)
  const [maxAttempts, setMaxAttempts] = useState(course.max_attempts ?? '')
  const [programLevel, setProgramLevel] = useState(course.program_level)
  const [fieldOfStudy, setFieldOfStudy] = useState(course.field_of_study)
  const [prerequisites, setPrerequisites] = useState(course.prerequisites ?? '')
  const [advancePreparation, setAdvancePreparation] = useState(course.advance_preparation ?? '')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [fieldsOfStudy, setFieldsOfStudy] = useState(null)
  const [programLevels, setProgramLevels] = useState(null)

  useEffect(() => {
    getFieldsOfStudy().then(setFieldsOfStudy).catch(() => {})
    getProgramLevels().then(setProgramLevels).catch(() => {})
  }, [])

  const dirty =
    title !== course.title ||
    slug !== course.slug ||
    description !== course.description ||
    Number(cooldownMinutes) !== course.retake_cooldown_minutes ||
    String(maxAttempts) !== String(course.max_attempts ?? '') ||
    programLevel !== course.program_level ||
    fieldOfStudy !== course.field_of_study ||
    prerequisites !== (course.prerequisites ?? '') ||
    advancePreparation !== (course.advance_preparation ?? '')

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
        program_level: programLevel,
        field_of_study: fieldOfStudy,
        prerequisites: prerequisites === '' ? null : prerequisites,
        advance_preparation: advancePreparation === '' ? null : advancePreparation,
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

        <label className={styles.label} htmlFor="course-program-level">
          Program level
        </label>
        <select
          id="course-program-level"
          className={styles.input}
          value={programLevel}
          onChange={(event) => setProgramLevel(event.target.value)}
        >
          {(programLevels?.levels ?? [course.program_level]).map((level) => (
            <option key={level} value={level}>
              {level.charAt(0).toUpperCase() + level.slice(1)}
            </option>
          ))}
        </select>

        <label className={styles.label} htmlFor="course-field-of-study">
          Field of study
        </label>
        <select
          id="course-field-of-study"
          className={styles.input}
          value={fieldOfStudy}
          onChange={(event) => setFieldOfStudy(event.target.value)}
        >
          {fieldsOfStudy ? (
            <>
              <option value={fieldsOfStudy.non_cpe}>{fieldsOfStudy.non_cpe}</option>
              <optgroup label="Technical">
                {fieldsOfStudy.technical.map((value) => (
                  <option key={value} value={value}>
                    {value}
                  </option>
                ))}
              </optgroup>
              <optgroup label="Non-technical">
                {fieldsOfStudy.non_technical.map((value) => (
                  <option key={value} value={value}>
                    {value}
                  </option>
                ))}
              </optgroup>
            </>
          ) : (
            <option value={fieldOfStudy}>{fieldOfStudy}</option>
          )}
        </select>

        <label className={styles.label} htmlFor="course-prerequisites">
          Prerequisites
        </label>
        <textarea
          id="course-prerequisites"
          className={styles.textarea}
          rows={2}
          value={prerequisites}
          onChange={(event) => setPrerequisites(event.target.value)}
        />

        <label className={styles.label} htmlFor="course-advance-preparation">
          Advance preparation
        </label>
        <textarea
          id="course-advance-preparation"
          className={styles.textarea}
          rows={2}
          value={advancePreparation}
          onChange={(event) => setAdvancePreparation(event.target.value)}
        />
        <p className={styles.hint}>
          Required for Intermediate, Advanced, and Update courses. Leave blank for Basic and Overview to show
          &quot;None&quot; on the course page.
        </p>

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
