import { useEffect, useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { getMyAttempts } from '../../api/attempts'
import { certificatePdfUrl } from '../../api/certificates'
import { useAuth } from '../../context/AuthContext.jsx'
import styles from './Progress.module.css'

function formatDate(isoString) {
  return new Date(isoString).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

function Progress() {
  const { user, loading: authLoading } = useAuth()
  const [state, setState] = useState({ status: 'loading', attempts: [] })

  useEffect(() => {
    if (!user) return
    getMyAttempts()
      .then((attempts) => setState({ status: 'loaded', attempts }))
      .catch(() => setState({ status: 'error', attempts: [] }))
  }, [user])

  if (authLoading) {
    return <p className={styles.message}>Loading&hellip;</p>
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: '/me' }} replace />
  }

  if (state.status === 'loading') {
    return <p className={styles.message}>Loading your progress&hellip;</p>
  }

  if (state.status === 'error') {
    return <p className={styles.message}>Couldn&apos;t load your progress. Please try again later.</p>
  }

  if (state.attempts.length === 0) {
    return (
      <div className={styles.message}>
        <p>You haven&apos;t taken a quiz yet.</p>
        <Link to="/">Browse lessons</Link>
      </div>
    )
  }

  return (
    <div className={styles.page}>
      <h1 className={styles.heading}>My progress</h1>
      <ul className={styles.list}>
        {state.attempts.map((attempt) => (
          <li key={attempt.attempt_id} className={styles.row}>
            <div className={styles.rowMain}>
              <Link to={`/lessons/${attempt.lesson_slug}`} className={styles.lessonTitle}>
                {attempt.lesson_title}
              </Link>
              <span className={`${styles.badge} ${attempt.passed ? styles.passed : styles.failed}`}>
                {attempt.passed ? 'Passed' : 'Not passed'}
              </span>
            </div>
            <div className={styles.rowMeta}>
              <span>Scored {attempt.score} out of 5</span>
              <span>{formatDate(attempt.completed_at)}</span>
              {attempt.certificate_code && (
                <a className={styles.downloadLink} href={certificatePdfUrl(attempt.attempt_id)} download>
                  Download certificate
                </a>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default Progress
