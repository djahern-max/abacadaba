import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getAttemptResult } from '../../api/attempts'
import { bigBurst } from '../../lib/confetti'
import styles from './Result.module.css'

function Result() {
  const { attemptId } = useParams()
  const [state, setState] = useState({ status: 'loading', result: null })
  const headingRef = useRef(null)
  const burstFired = useRef(false)

  useEffect(() => {
    setState({ status: 'loading', result: null })
    burstFired.current = false
    getAttemptResult(attemptId)
      .then((result) => setState({ status: 'loaded', result }))
      .catch((error) => {
        if (error.status === 404) {
          setState({ status: 'not-found', result: null })
        } else if (error.status === 409) {
          setState({ status: 'not-complete', result: null })
        } else {
          setState({ status: 'error', result: null })
        }
      })
  }, [attemptId])

  useEffect(() => {
    if (state.status !== 'loaded') return
    headingRef.current?.focus()
    if (state.result.passed && !burstFired.current) {
      burstFired.current = true
      bigBurst()
    }
  }, [state])

  if (state.status === 'loading') {
    return <p className={styles.message}>Loading your result&hellip;</p>
  }

  if (state.status === 'not-found') {
    return (
      <div className={styles.message}>
        <p>We couldn&apos;t find that attempt.</p>
        <Link to="/">Back home</Link>
      </div>
    )
  }

  if (state.status === 'not-complete') {
    return (
      <div className={styles.message}>
        <p>This attempt isn&apos;t finished yet.</p>
        <Link to="/">Back home</Link>
      </div>
    )
  }

  if (state.status === 'error') {
    return <p className={styles.message}>Couldn&apos;t load this result. Please try again later.</p>
  }

  const { result } = state
  const scoreText = `${result.score} out of ${result.question_count}`

  if (result.passed) {
    return (
      <div className={styles.result}>
        <h1 className={styles.heading} tabIndex={-1} ref={headingRef}>
          You passed!
        </h1>
        <p className={styles.score}>
          You scored {scoreText} on {result.lesson_title}.
        </p>
        <button type="button" className={styles.certificateButton} disabled>
          Download certificate
        </button>
        <p className={styles.note}>Certificates are arriving in a future update.</p>
        <Link to={`/lessons/${result.lesson_slug}`}>Back to lesson</Link>
      </div>
    )
  }

  return (
    <div className={styles.result}>
      <h1 className={styles.heading} tabIndex={-1} ref={headingRef}>
        Not quite yet
      </h1>
      <p className={styles.score}>
        You scored {scoreText} on {result.lesson_title}. A passing score is 4 out of 5&mdash;you&apos;re close,
        give it another go.
      </p>
      <div className={styles.actions}>
        <Link to={`/lessons/${result.lesson_slug}`}>Watch again</Link>
        <Link to={`/lessons/${result.lesson_slug}/quiz`}>Retry quiz</Link>
      </div>
    </div>
  )
}

export default Result
