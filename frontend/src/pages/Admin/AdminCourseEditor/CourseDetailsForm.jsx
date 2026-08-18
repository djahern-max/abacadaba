import { forwardRef, useEffect, useImperativeHandle, useState } from 'react'
import { updateAdminCourse } from '../../../api/admin'
import { getFieldsOfStudy, getProgramLevels } from '../../../api/meta'
import styles from '../AdminLessonEditor/DetailsForm.module.css'

const CourseDetailsForm = forwardRef(function CourseDetailsForm({ course, collapsed, onDirtyChange }, ref) {
  const [title, setTitle] = useState(course.title)
  const [slug, setSlug] = useState(course.slug)
  const [description, setDescription] = useState(course.description)
  const [cooldownMinutes, setCooldownMinutes] = useState(course.retake_cooldown_minutes)
  const [maxAttempts, setMaxAttempts] = useState(course.max_attempts ?? '')
  const [programLevel, setProgramLevel] = useState(course.program_level)
  const [fieldOfStudy, setFieldOfStudy] = useState(course.field_of_study)
  const [prerequisites, setPrerequisites] = useState(course.prerequisites ?? '')
  const [advancePreparation, setAdvancePreparation] = useState(course.advance_preparation ?? '')
  const [fieldsOfStudy, setFieldsOfStudy] = useState(null)
  const [programLevels, setProgramLevels] = useState(null)

  useEffect(() => {
    getFieldsOfStudy().then(setFieldsOfStudy).catch(() => {})
    getProgramLevels().then(setProgramLevels).catch(() => {})
  }, [])

  const titleDirty = title !== course.title
  const slugDirty = slug !== course.slug
  const descriptionDirty = description !== course.description
  const cooldownDirty = Number(cooldownMinutes) !== course.retake_cooldown_minutes
  const maxAttemptsDirty = String(maxAttempts) !== String(course.max_attempts ?? '')
  const programLevelDirty = programLevel !== course.program_level
  const fieldOfStudyDirty = fieldOfStudy !== course.field_of_study
  const prerequisitesDirty = prerequisites !== (course.prerequisites ?? '')
  const advancePreparationDirty = advancePreparation !== (course.advance_preparation ?? '')

  const dirty =
    titleDirty ||
    slugDirty ||
    descriptionDirty ||
    cooldownDirty ||
    maxAttemptsDirty ||
    programLevelDirty ||
    fieldOfStudyDirty ||
    prerequisitesDirty ||
    advancePreparationDirty

  useEffect(() => {
    onDirtyChange?.(dirty ? 1 : 0)
  }, [dirty, onDirtyChange])

  useImperativeHandle(ref, () => ({
    save: () =>
      updateAdminCourse(course.id, {
        title,
        slug,
        description,
        retake_cooldown_minutes: Number(cooldownMinutes),
        max_attempts: maxAttempts === '' ? null : Number(maxAttempts),
        program_level: programLevel,
        field_of_study: fieldOfStudy,
        prerequisites: prerequisites === '' ? null : prerequisites,
        advance_preparation: advancePreparation === '' ? null : advancePreparation,
      }),
  }))

  return (
    <section className={styles.section}>
      <h2 className={styles.heading}>Details</h2>
      <div className={styles.form}>
        <label className={styles.label} htmlFor="course-title">
          Title
        </label>
        <input
          id="course-title"
          className={`${styles.input} ${titleDirty ? styles.fieldDirty : ''}`}
          value={title}
          onChange={(event) => setTitle(event.target.value)}
        />

        <label className={styles.label} htmlFor="course-slug">
          Slug
        </label>
        <input
          id="course-slug"
          className={`${styles.input} ${slugDirty ? styles.fieldDirty : ''}`}
          value={slug}
          onChange={(event) => setSlug(event.target.value)}
        />
        {course.is_published && slug !== course.slug && (
          <p className={styles.warning}>
            Changing the slug of a published course breaks any links already shared.
          </p>
        )}

        <label className={styles.label} htmlFor="course-description">
          {collapsed ? 'Description' : 'Course description'}
        </label>
        <textarea
          id="course-description"
          className={`${styles.textarea} ${descriptionDirty ? styles.fieldDirty : ''}`}
          rows={4}
          value={description}
          onChange={(event) => setDescription(event.target.value)}
        />
        <p className={styles.hint}>
          Shown on the public course page before enrollment — the disclosure a participant reads to decide
          whether to take this course. The most consequential field on this page.
        </p>

        <label className={styles.label} htmlFor="course-program-level">
          Program level
        </label>
        <select
          id="course-program-level"
          className={`${styles.input} ${programLevelDirty ? styles.fieldDirty : ''}`}
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
          className={`${styles.input} ${fieldOfStudyDirty ? styles.fieldDirty : ''}`}
          value={fieldOfStudy}
          onChange={(event) => setFieldOfStudy(event.target.value)}
        >
          {fieldsOfStudy ? (
            <>
              <option value={fieldsOfStudy.non_cpe}>{fieldsOfStudy.non_cpe}</option>
              <optgroup label="Technical">
                {fieldsOfStudy.technical.map((field) => (
                  <option key={field.name} value={field.name}>
                    {field.name}
                  </option>
                ))}
              </optgroup>
              <optgroup label="Non-technical">
                {fieldsOfStudy.non_technical.map((field) => (
                  <option key={field.name} value={field.name}>
                    {field.name}
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
          className={`${styles.textarea} ${prerequisitesDirty ? styles.fieldDirty : ''}`}
          rows={2}
          value={prerequisites}
          onChange={(event) => setPrerequisites(event.target.value)}
        />

        <label className={styles.label} htmlFor="course-advance-preparation">
          Advance preparation
        </label>
        <textarea
          id="course-advance-preparation"
          className={`${styles.textarea} ${advancePreparationDirty ? styles.fieldDirty : ''}`}
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
          className={`${styles.input} ${cooldownDirty ? styles.fieldDirty : ''}`}
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
          className={`${styles.input} ${maxAttemptsDirty ? styles.fieldDirty : ''}`}
          type="number"
          min="1"
          value={maxAttempts}
          onChange={(event) => setMaxAttempts(event.target.value)}
        />
        <p className={styles.hint}>Blank means unlimited attempts.</p>
      </div>
    </section>
  )
})

export default CourseDetailsForm
