import { forwardRef, useEffect, useImperativeHandle, useState } from 'react'
import { updateAdminCourse } from '../../../api/admin'
import { getFieldsOfStudy, getProgramLevels } from '../../../api/meta'
import styles from '../AdminLessonEditor/DetailsForm.module.css'

// 9.02.2 item 3: "no longer than one year from the date of purchase or
// enrollment." abacadaba has no per-enrollment purchase date, so the window
// is measured from the course's own review date instead - see
// app/constants/currency.py's EXPIRATION_WINDOW_DAYS, which this mirrors.
const EXPIRATION_WINDOW_DAYS = 365

function defaultExpiration(reviewedAt) {
  const reviewed = new Date(reviewedAt)
  const withWindow = new Date(reviewed.getTime() + EXPIRATION_WINDOW_DAYS * 24 * 60 * 60 * 1000)
  return withWindow.toISOString().slice(0, 10)
}

const CourseDetailsForm = forwardRef(function CourseDetailsForm({ course, collapsed, onDirtyChange }, ref) {
  const [title, setTitle] = useState(course.title)
  const [slug, setSlug] = useState(course.slug)
  const [description, setDescription] = useState(course.description)
  const [cooldownMinutes, setCooldownMinutes] = useState(course.retake_cooldown_minutes)
  const [maxAttempts, setMaxAttempts] = useState(course.max_attempts ?? '')
  const [passPercent, setPassPercent] = useState(Math.round(Number(course.pass_ratio) * 100))
  const [programKind, setProgramKind] = useState(course.program_kind)
  const [programLevel, setProgramLevel] = useState(course.program_level)
  const [fieldOfStudy, setFieldOfStudy] = useState(course.field_of_study)
  const [prerequisites, setPrerequisites] = useState(course.prerequisites ?? '')
  const [advancePreparation, setAdvancePreparation] = useState(course.advance_preparation ?? '')
  const [expiresOn, setExpiresOn] = useState(course.expires_on ?? '')
  const [fieldsOfStudy, setFieldsOfStudy] = useState(null)
  const [programLevels, setProgramLevels] = useState(null)

  useEffect(() => {
    getFieldsOfStudy().then(setFieldsOfStudy).catch(() => {})
    getProgramLevels().then(setProgramLevels).catch(() => {})
  }, [])

  useEffect(() => {
    // Default only when nothing has ever been set - an author who has to
    // type a date will eventually type a wrong one (current-feature.md,
    // Part 2). Never overwrites an explicit value, on this course or typed
    // locally.
    if (course.expires_on == null && course.reviewed_at && expiresOn === '') {
      setExpiresOn(defaultExpiration(course.reviewed_at))
    }
  }, [course.reviewed_at, course.expires_on])

  const titleDirty = title !== course.title
  const slugDirty = slug !== course.slug
  const descriptionDirty = description !== course.description
  const cooldownDirty = Number(cooldownMinutes) !== course.retake_cooldown_minutes
  const maxAttemptsDirty = String(maxAttempts) !== String(course.max_attempts ?? '')
  const passPercentDirty = Number(passPercent) !== Math.round(Number(course.pass_ratio) * 100)
  const programKindDirty = programKind !== course.program_kind
  const programLevelDirty = programLevel !== course.program_level
  const fieldOfStudyDirty = fieldOfStudy !== course.field_of_study
  const prerequisitesDirty = prerequisites !== (course.prerequisites ?? '')
  const advancePreparationDirty = advancePreparation !== (course.advance_preparation ?? '')
  const expiresOnDirty = expiresOn !== (course.expires_on ?? '')

  const dirty =
    titleDirty ||
    slugDirty ||
    descriptionDirty ||
    cooldownDirty ||
    maxAttemptsDirty ||
    programKindDirty ||
    programLevelDirty ||
    fieldOfStudyDirty ||
    prerequisitesDirty ||
    advancePreparationDirty ||
    expiresOnDirty ||
    passPercentDirty

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
        expires_on: expiresOn === '' ? null : expiresOn,
        pass_ratio: Number(passPercent) / 100,
        program_kind: programKind,
      }),
  }))

  return (
    <section className={styles.section}>
      <h2 className={styles.heading}>Details</h2>
      <div className={styles.form}>
        <label className={styles.label} htmlFor="course-program-kind">
          Offered as
        </label>
        <select
          id="course-program-kind"
          className={`${styles.input} ${programKindDirty ? styles.fieldDirty : ''}`}
          value={programKind}
          onChange={(event) => setProgramKind(event.target.value)}
          disabled={course.is_published}
        >
          <option value="cpe">A CPE program</option>
          <option value="general">Ordinary education (not CPE)</option>
        </select>
        <p className={styles.hint}>
          A CPE program discloses field of study, CPE credit, and NASBA registration, and its publish checklist
          requires a developer, a reviewer, and computed credit. Ordinary education shows none of that CPE
          furniture and skips those checklist items - see current-feature.md, Feature 029. Placed first because it
          changes which of the fields below matter.
          {course.is_published && ' Unpublish this course to change it.'}
        </p>

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

        {programKind === 'cpe' && (
          <>
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
          </>
        )}

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

        <label className={styles.label} htmlFor="course-expires-on">
          Expiration date
        </label>
        <input
          id="course-expires-on"
          className={`${styles.input} ${expiresOnDirty ? styles.fieldDirty : ''}`}
          type="date"
          value={expiresOn}
          onChange={(event) => setExpiresOn(event.target.value)}
        />
        <p className={styles.hint}>
          9.02.2: the date by which a participant must complete the qualified assessment. Required to publish.
          Defaulted to one year past the review date once a review is recorded, but editable.
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

        <label className={styles.label} htmlFor="course-pass-percent">
          Pass threshold (percent of assessment questions)
        </label>
        <input
          id="course-pass-percent"
          className={`${styles.input} ${passPercentDirty ? styles.fieldDirty : ''}`}
          type="number"
          min="70"
          max="100"
          value={passPercent}
          onChange={(event) => setPassPercent(event.target.value)}
        />
        <p className={styles.hint}>
          6.01.2 sets 70 percent as a floor for the qualified assessment - it cannot be set lower, only
          stricter.
        </p>
      </div>
    </section>
  )
})

export default CourseDetailsForm
