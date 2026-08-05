import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext.jsx'
import styles from './Login.module.css'

function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = location.state?.from ?? '/'

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
