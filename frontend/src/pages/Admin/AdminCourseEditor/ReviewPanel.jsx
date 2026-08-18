import { forwardRef, useEffect, useImperativeHandle, useState } from 'react'
import { Link } from 'react-router-dom'
import { getAdminSMEs, updateAdminCourse } from '../../../api/admin'
import SourcesPanel from './SourcesPanel'
import styles from '../AdminLessonEditor/DetailsForm.module.css'

const REVIEW_CYCLES = ['annual', 'biennial']

function toDatetimeLocal(isoString) {
  if (!isoString) return ''
  const date = new Date(isoString)
  const pad = (n) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function fromDatetimeLocal(value) {
  return value ? new Date(value).toISOString() : null
}

// The developer/reviewer/review-date chain (4.01, 4.01.1, 4.02) plus the
// source list, placed beside it per current-feature.md's placement decision:
// a reviewer signing off next to an empty source list should have to notice.
const ReviewPanel = forwardRef(function ReviewPanel({ course, onDirtyChange, onChange }, ref) {
  const [developerId, setDeveloperId] = useState(String(course.developer_id ?? ''))
  const [reviewerId, setReviewerId] = useState(String(course.reviewer_id ?? ''))
  const [reviewedAt, setReviewedAt] = useState(() => toDatetimeLocal(course.reviewed_at))
  const [reviewNotes, setReviewNotes] = useState(course.review_notes ?? '')
  const [reviewCycle, setReviewCycle] = useState(course.review_cycle)
  const [smes, setSmes] = useState(null)

  useEffect(() => {
    getAdminSMEs().then(setSmes).catch(() => {})
  }, [])

  const initialReviewedAt = toDatetimeLocal(course.reviewed_at)

  // A <select> value is always a string, so both sides must be strings -
  // `developerId !== course.developer_id` would compare "39" to 39 and
  // report dirty forever, even right after a successful save.
  const developerDirty = developerId !== String(course.developer_id ?? '')
  const reviewerDirty = reviewerId !== String(course.reviewer_id ?? '')
  const reviewedAtDirty = reviewedAt !== initialReviewedAt
  const reviewNotesDirty = reviewNotes !== (course.review_notes ?? '')
  const reviewCycleDirty = reviewCycle !== course.review_cycle

  const dirty = developerDirty || reviewerDirty || reviewedAtDirty || reviewNotesDirty || reviewCycleDirty

  useEffect(() => {
    onDirtyChange?.(dirty ? 1 : 0)
  }, [dirty, onDirtyChange])

  useImperativeHandle(ref, () => ({
    save: () =>
      updateAdminCourse(course.id, {
        developer_id: developerId === '' ? null : Number(developerId),
        reviewer_id: reviewerId === '' ? null : Number(reviewerId),
        reviewed_at: fromDatetimeLocal(reviewedAt),
        review_notes: reviewNotes === '' ? null : reviewNotes,
        review_cycle: reviewCycle,
      }),
  }))

  const stale = course.is_published && course.reviewed_at && course.reviewed_at < course.content_updated_at

  return (
    <section className={styles.section}>
      <h2 className={styles.heading}>Development and review</h2>

      {stale && (
        <p className={styles.warning}>
          This course has changed since it was last reviewed. It stays published and keeps serving
          participants, but it cannot be re-published until it is reviewed again.
        </p>
      )}

      <div className={styles.form}>
        <label className={styles.label} htmlFor="review-developer">
          Developer
        </label>
        <select
          id="review-developer"
          className={`${styles.input} ${developerDirty ? styles.fieldDirty : ''}`}
          value={developerId}
          onChange={(event) => setDeveloperId(event.target.value)}
        >
          <option value="">Select a developer&hellip;</option>
          {(smes ?? []).map((sme) => (
            <option key={sme.id} value={sme.id}>
              {sme.name} &mdash; {sme.credentials}
            </option>
          ))}
        </select>

        <label className={styles.label} htmlFor="review-reviewer">
          Reviewer
        </label>
        <select
          id="review-reviewer"
          className={`${styles.input} ${reviewerDirty ? styles.fieldDirty : ''}`}
          value={reviewerId}
          onChange={(event) => setReviewerId(event.target.value)}
        >
          <option value="">Select a reviewer&hellip;</option>
          {(smes ?? []).map((sme) => (
            <option key={sme.id} value={sme.id}>
              {sme.name} &mdash; {sme.credentials}
            </option>
          ))}
        </select>
        <p className={styles.hint}>
          Must be a different person from the developer. Managed on the{' '}
          <Link to="/admin/smes">subject matter experts</Link> page.
        </p>

        <label className={styles.label} htmlFor="review-date">
          Review date
        </label>
        <input
          id="review-date"
          type="datetime-local"
          className={`${styles.input} ${reviewedAtDirty ? styles.fieldDirty : ''}`}
          value={reviewedAt}
          onChange={(event) => setReviewedAt(event.target.value)}
        />

        <label className={styles.label} htmlFor="review-cycle">
          Review cycle
        </label>
        <select
          id="review-cycle"
          className={`${styles.input} ${reviewCycleDirty ? styles.fieldDirty : ''}`}
          value={reviewCycle}
          onChange={(event) => setReviewCycle(event.target.value)}
        >
          {REVIEW_CYCLES.map((cycle) => (
            <option key={cycle} value={cycle}>
              {cycle.charAt(0).toUpperCase() + cycle.slice(1)}
            </option>
          ))}
        </select>
        <p className={styles.hint}>Annual for subjects that change frequently, otherwise biennial.</p>

        <label className={styles.label} htmlFor="review-notes">
          Review notes
        </label>
        <textarea
          id="review-notes"
          className={`${styles.textarea} ${reviewNotesDirty ? styles.fieldDirty : ''}`}
          rows={3}
          value={reviewNotes}
          onChange={(event) => setReviewNotes(event.target.value)}
        />
      </div>

      <SourcesPanel course={course} onChange={onChange} />
    </section>
  )
})

export default ReviewPanel
