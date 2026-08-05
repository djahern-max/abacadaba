import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getAttemptResult } from '../../api/attempts'
import { certificatePdfUrl, claimCertificate } from '../../api/certificates'
import { bigBurst } from '../../lib/confetti'
import styles from './Result.module.css'

const SITE_URL = import.meta.env.VITE_SITE_URL || 'http://localhost:5173'

function storageKey(attemptId) {
  return `abacadaba:certificate:${attemptId}`
}

function loadStoredCertificate(attemptId) {
  try {
    const raw = localStorage.getItem(storageKey(attemptId))
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function storeCertificate(attemptId, certificate) {
  try {
    localStorage.setItem(storageKey(attemptId), JSON.stringify(certificate))
  } catch {
    // localStorage may be unavailable; the download link still works this session
  }
}

function Certificate({ attemptId }) {
  const [certificate, setCertificate] = useState(() => loadStoredCertificate(attemptId))
  const [name, setName] = useState('')
  const [status, setStatus] = useState('idle')
  const [validationError, setValidationError] = useState('')

  async function handleSubmit(event) {
    event.preventDefault()
    const trimmed = name.trim()
    if (trimmed.length < 2 || trimmed.length > 80) {
      setValidationError('Enter a name between 2 and 80 characters.')
      return
    }
    setValidationError('')
    setStatus('submitting')
    try {
      const result = await claimCertificate(attemptId, trimmed)
      const claimed = { code: result.certificate_code, name: result.recipient_name }
      storeCertificate(attemptId, claimed)
      setCertificate(claimed)
      setStatus('idle')
    } catch {
      setStatus('error')
    }
  }

  if (certificate) {
    return (
      <div className={styles.certificate}>
        <p className={styles.certificateCode}>Certificate code: {certificate.code}</p>
        <p className={styles.certificateCode}>
          Verify at: {SITE_URL}/verify/{certificate.code}
        </p>
        <a
          className={styles.certificateButton}
          href={certificatePdfUrl(attemptId)}
          download
        >
          Download PDF
        </a>
      </div>
    )
  }

  return (
    <form className={styles.certificateForm} onSubmit={handleSubmit}>
      <label className={styles.label} htmlFor="recipient-name">
        Name as it should appear on your certificate
      </label>
      <input
        id="recipient-name"
        className={styles.input}
        type="text"
        value={name}
        onChange={(event) => setName(event.target.value)}
        disabled={status === 'submitting'}
      />
      {validationError && <p className={styles.fieldError}>{validationError}</p>}
      {status === 'error' && (
        <p className={styles.fieldError}>Couldn&apos;t claim your certificate. Please try again.</p>
      )}
      <button type="submit" className={styles.certificateButton} disabled={status === 'submitting'}>
        {status === 'submitting' ? 'Getting your certificate…' : 'Get my certificate'}
      </button>
    </form>
  )
}

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
        <Certificate attemptId={result.attempt_id} />
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
