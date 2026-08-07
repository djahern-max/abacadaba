import { useState } from 'react'
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext.jsx'
import GoogleButton from '../../components/GoogleButton/GoogleButton.jsx'
import PasswordInput from '../../components/PasswordInput/PasswordInput.jsx'
import styles from './Login.module.css'

const OAUTH_ERROR_MESSAGES = {
  unverified_email:
    "That Google account's email isn't verified by Google, so it can't be linked automatically. Sign in with your password instead.",
  state_mismatch: 'Your Google sign-in attempt expired or was invalid. Please try again.',
  google_auth_failed: 'Something went wrong signing in with Google. Please try again.',
}

function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = location.state?.from ?? '/'
  const [searchParams] = useSearchParams()
  const oauthError = OAUTH_ERROR_MESSAGES[searchParams.get('error')]

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [status, setStatus] = useState('idle')
  const [error, setError] = useState('')

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setStatus('submitting')
    try {
      await login(email, password)
      navigate(from, { replace: true })
    } catch {
      setStatus('idle')
      setError('Incorrect email or password.')
    }
  }

  return (
    <div className={styles.page}>
      <h1 className={styles.heading}>Sign in</h1>
      {oauthError && <p className={styles.fieldError}>{oauthError}</p>}
      <GoogleButton />
      <form className={styles.form} onSubmit={handleSubmit}>
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
        <PasswordInput
          id="password"
          label="Password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          disabled={status === 'submitting'}
          autoComplete="current-password"
        />
        {error && <p className={styles.fieldError}>{error}</p>}
        <button type="submit" className={styles.button} disabled={status === 'submitting'}>
          {status === 'submitting' ? 'Signing in…' : 'Sign in'}
        </button>
      </form>
      <p className={styles.switch}>
        Need an account? <Link to="/register">Register</Link>
      </p>
    </div>
  )
}

export default Login
