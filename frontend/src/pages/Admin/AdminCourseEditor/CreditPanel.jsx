import { useEffect, useState } from 'react'
import { getAdminCourseCredit, recomputeAdminCourseCredit } from '../../../api/admin'
import Button from '../../../components/Button/Button'
import styles from './CreditPanel.module.css'

function formatMinutes(value) {
  return value == null ? '—' : `${Number(value).toFixed(2)} min`
}

// The word-count credit formula (7.02.6/7.02.7), term by term - see
// current-feature.md, "Store the inputs, not just the answer". Not part of
// the page's batched save: credit is derived from the course's other
// content by an explicit Recompute action, not typed in directly.
function CreditPanel({ course, onChange }) {
  const [breakdown, setBreakdown] = useState(null)
  const [loading, setLoading] = useState(true)
  const [recomputing, setRecomputing] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    setLoading(true)
    getAdminCourseCredit(course.id)
      .then(setBreakdown)
      .catch(() => setError('Could not load credit.'))
      .finally(() => setLoading(false))
  }, [course.id, course.credit_computed_at])

  async function handleRecompute() {
    setError('')
    setRecomputing(true)
    try {
      const fresh = await recomputeAdminCourseCredit(course.id)
      setBreakdown(fresh)
      await onChange()
    } catch {
      setError('Could not recompute credit.')
    } finally {
      setRecomputing(false)
    }
  }

  // Derived exactly like the review chain's staleness (021), never a
  // stored bool: see current-feature.md, "Do not add a credit_is_stale boolean".
  const stale = course.credit_computed_at == null || course.credit_computed_at < course.content_updated_at
  // Feature 029: this panel stays visible and computable for a general
  // course - it's useful information - but staleness must not read as a
  // publish blocker there, since the credit gate is relaxed. See
  // current-feature.md, frontend task 3.
  const isGeneral = course.program_kind === 'general'

  return (
    <section className={styles.section}>
      <h2 className={styles.heading}>Credit</h2>

      {stale && (
        <p className={styles.warning}>
          {course.credit_computed_at == null
            ? 'Credit has not been computed yet.'
            : 'This course has changed since credit was last computed.'}{' '}
          {isGeneral
            ? 'It stays as last computed until you recompute below.'
            : 'It stays as last computed until you recompute below, and the course cannot publish while stale.'}
        </p>
      )}

      <table className={styles.table}>
        <thead>
          <tr>
            <th>Segment</th>
            <th>Runtime</th>
            <th>Counts as</th>
            <th>Word count</th>
          </tr>
        </thead>
        <tbody>
          {course.lessons.map((lesson) => (
            <tr key={lesson.id}>
              <td>{lesson.title}</td>
              <td>{lesson.duration_seconds == null ? '—' : `${lesson.duration_seconds}s`}</td>
              <td>{lesson.av_is_additional_learning ? 'Additional learning (A/V)' : 'Narration of text'}</td>
              <td>{lesson.av_is_additional_learning ? '—' : lesson.word_count}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {loading ? (
        <p className={styles.message}>Loading&hellip;</p>
      ) : breakdown?.computed_at == null ? (
        <p className={styles.message}>Not yet computed. Click Recompute below.</p>
      ) : (
        <dl className={styles.arithmetic}>
          <div className={styles.row}>
            <dt>Words &divide; {180} (7.02.6)</dt>
            <dd>
              {breakdown.word_count} &divide; 180 = {formatMinutes(breakdown.word_term_minutes)}
            </dd>
          </div>
          <div className={styles.row}>
            <dt>A/V duration</dt>
            <dd>
              {breakdown.av_seconds}s = {formatMinutes(breakdown.av_term_minutes)}
            </dd>
          </div>
          <div className={styles.row}>
            <dt>Questions &times; 1.85</dt>
            <dd>
              {breakdown.question_count} &times; 1.85 = {formatMinutes(breakdown.question_term_minutes)}
            </dd>
          </div>
          <div className={styles.rowTotal}>
            <dt>Sum</dt>
            <dd>{formatMinutes(breakdown.raw_minutes)}</dd>
          </div>
          <div className={styles.row}>
            <dt>&divide; 50 (one credit)</dt>
            <dd>{Number(breakdown.raw_credit).toFixed(4)} raw credit</dd>
          </div>
          <div className={styles.rowTotal}>
            <dt>Rounded down to the nearest one-fifth (7.01)</dt>
            <dd className={styles.award}>{breakdown.award} credit</dd>
          </div>
          <p className={styles.hint}>
            Formula version {breakdown.formula_version}, computed {new Date(breakdown.computed_at).toLocaleString()}.
          </p>
        </dl>
      )}

      <Button variant="secondary" onClick={handleRecompute} disabled={recomputing}>
        {recomputing ? 'Recomputing…' : 'Recompute credit'}
      </Button>
      {error && <p className={styles.fieldError}>{error}</p>}
    </section>
  )
}

export default CreditPanel
