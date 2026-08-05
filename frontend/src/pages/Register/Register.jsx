import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext.jsx'
import styles from './Register.module.css'

function validate(displayName, password) {
  const trimmedName = displayName.trim()
  if (trimmedName.length < 2 || trimmedName.length > 80) {
    return 'Name must be 2 to 80 characters.'
  }
  if (password.length < 10) {
    return 'Password must be at least 10 characters.'
  }
  return ''
}

function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = location.state?.from ?? '/'

  const [displayName, setDisplayName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [status, setStatus] = useState('idle')
  const [error, setError] = useState('')

  async function handleSubmit(event) {
    event.preventDefault()
    const validationError = validate(displayName, password)
    if (validationError) {
      setError(validationError)
      return
    }

    setError('')
    setStatus('submitting')
    try {
      await register(email, password, displayName.trim())
      navigate(from, { replace: true })
    } catch (err) {
      setStatus('idle')
      setError(
        err.status === 409
          ? 'That email is already registered.'
          : "Couldn't create your account. Please try again.",
      )
    }
  }

  return (
    <div className={styles.page}>
      <h1 className={styles.heading}>Create an account</h1>
      <form className={styles.form} onSubmit={handleSubmit}>
        <label className={styles.label} htmlFor="display-name">
          Name
        </label>
        <input
          id="display-name"
          className={styles.input}
          type="text"
          value={displayName}
          onChange={(event) => setDisplayName(event.target.value)}
          required
          disabled={status === 'submitting'}
        />
        <label className={styles.label} htmlFor="email">
          Email
        </label>
        <input
          id="email"
          className={styles.input}
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          required
          disabled={status === 'submitting'}
        />
        <label className={styles.label} htmlFor="password">
          Password
        </label>
        <input
          id="password"
          className={styles.input}
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          required
          disabled={status === 'submitting'}
        />
        <p className={styles.hint}>At least 10 characters.</p>
        {error && <p className={styles.fieldError}>{error}</p>}
        <button type="submit" className={styles.button} disabled={status === 'submitting'}>
          {status === 'submitting' ? 'Creating your account…' : 'Register'}
        </button>
      </form>
      <p className={styles.switch}>
        Already have an account? <Link to="/login">Sign in</Link>
      </p>
    </div>
  )
}

export default Register
