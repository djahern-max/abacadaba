import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getAttemptResult } from '../../api/attempts'
import { certificatePdfUrl, claimCertificate } from '../../api/certificates'
import { useAuth } from '../../context/AuthContext.jsx'
import { bigBurst } from '../../lib/confetti'
import styles from './Result.module.css'

const SITE_URL = import.meta.env.VITE_SITE_URL || 'http://localhost:5173'

function ClaimedCertificate({ attemptId, code }) {
  return (
    <div className={styles.certificate}>
      <p className={styles.certificateCode}>Certificate code: {code}</p>
      <p className={styles.certificateCode}>
        Verify at: {SITE_URL}/verify/{code}
      </p>
      <a className={styles.certificateButton} href={certificatePdfUrl(attemptId)} download>
        Download PDF
      </a>
    </div>
  )
}

function SignedInCertificate({ attemptId, onClaimed }) {
  const [error, setError] = useState(false)
  const claimStarted = useRef(false)

  useEffect(() => {
    if (claimStarted.current) return
    claimStarted.current = true
    claimCertificate(attemptId)
      .then((result) => onClaimed(result.certificate_code))
      .catch(() => setError(true))
  }, [attemptId, onClaimed])

  if (error) {
    return <p className={styles.fieldError}>Couldn&apos;t claim your certificate. Please try again.</p>
  }

  return <p className={styles.message}>Getting your certificate&hellip;</p>
}

function AnonymousCertificateForm({ attemptId, onClaimed }) {
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
      onClaimed(result.certificate_code)
    } catch {
      setStatus('error')
    }
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

function Certificate({ attemptId, certificateCode }) {
  const { user } = useAuth()
  const [code, setCode] = useState(certificateCode)

  if (code) {
    return <ClaimedCertificate attemptId={attemptId} code={code} />
  }

  if (user) {
    return <SignedInCertificate attemptId={attemptId} onClaimed={setCode} />
  }

  return <AnonymousCertificateForm attemptId={attemptId} onClaimed={setCode} />
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
        <Certificate attemptId={result.attempt_id} certificateCode={result.certificate_code} />
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
