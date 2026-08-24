import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getCourseEvaluations } from '../../../api/admin'
import { getEvaluationDimensions } from '../../../api/evaluations'
import styles from './Evaluations.module.css'

const LOW_MEAN_THRESHOLD = 3

function percent(ratio) {
  return ratio === null ? '—' : `${Math.round(ratio * 100)}%`
}

function MeanRow({ question, mean }) {
  const flagged = mean !== null && mean < LOW_MEAN_THRESHOLD
  return (
    <tr className={flagged ? styles.flaggedRow : undefined}>
      <td>{question}</td>
      <td>
        {mean === null ? '—' : mean.toFixed(1)}
        {flagged && <span className={styles.badge}>Below average</span>}
      </td>
    </tr>
  )
}

function Evaluations() {
  const { id } = useParams()
  const [state, setState] = useState({ status: 'loading', data: null, dimensions: [] })

  useEffect(() => {
    setState({ status: 'loading', data: null, dimensions: [] })
    Promise.all([getCourseEvaluations(id), getEvaluationDimensions()])
      .then(([data, { dimensions }]) => setState({ status: 'loaded', data, dimensions }))
      .catch(() => setState({ status: 'error', data: null, dimensions: [] }))
  }, [id])

  if (state.status === 'loading') {
    return <p className={styles.message}>Loading&hellip;</p>
  }
  if (state.status === 'error') {
    return <p className={styles.message}>Couldn&apos;t load evaluations for this course.</p>
  }

  const { data, dimensions } = state
  const { summary, comments } = data
  const questionByKey = Object.fromEntries(dimensions.map((dimension) => [dimension.key, dimension.question]))
  const means = summary.means.filter((row) => questionByKey[row.key])

  return (
    <div className={styles.page}>
      <Link to={`/admin/courses/${id}`} className={styles.back}>
        &larr; Back to course
      </Link>
      <h1 className={styles.heading}>Evaluations</h1>

      {summary.response_count === 0 ? (
        <p className={styles.message}>No evaluations yet. They&apos;ll appear here once participants submit one.</p>
      ) : (
        <>
          <section className={styles.summaryRow}>
            <div className={styles.stat}>
              <span className={styles.statValue}>{summary.response_count}</span>
              <span className={styles.statLabel}>Responses</span>
            </div>
            <div className={styles.stat}>
              <span className={styles.statValue}>{percent(summary.response_rate)}</span>
              <span className={styles.statLabel}>Response rate</span>
            </div>
          </section>

          <section className={styles.section}>
            <h2 className={styles.sectionHeading}>Mean rating by dimension</h2>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Dimension</th>
                  <th>Mean (1&ndash;5)</th>
                </tr>
              </thead>
              <tbody>
                {means.map((row) => (
                  <MeanRow key={row.key} question={questionByKey[row.key]} mean={row.mean} />
                ))}
              </tbody>
            </table>
          </section>

          <section className={styles.section}>
            <h2 className={styles.sectionHeading}>Comments</h2>
            {comments.length === 0 ? (
              <p className={styles.message}>No comments yet.</p>
            ) : (
              <ul className={styles.commentList}>
                {comments.map((comment, index) => (
                  <li key={index} className={styles.comment}>
                    <p className={styles.commentText}>&ldquo;{comment.comments}&rdquo;</p>
                    <p className={styles.commentDate}>{new Date(comment.submitted_at).toLocaleDateString()}</p>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </div>
  )
}

export default Evaluations
