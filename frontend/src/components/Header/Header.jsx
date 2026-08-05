import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext.jsx'
import styles from './Header.module.css'

function Header({ status }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  async function handleSignOut() {
    await logout()
    navigate('/')
  }

  return (
    <header className={styles.header}>
      <Link to="/" className={styles.wordmark}>
        abacadaba
      </Link>
      <div className={styles.right}>
        {status === 'checking' && (
          <span className={`${styles.pill} ${styles.checking}`}>Checking backend&hellip;</span>
        )}
        {status === 'connected' && (
          <span className={`${styles.pill} ${styles.connected}`}>Backend connected</span>
        )}
        {status === 'unreachable' && (
          <span className={`${styles.pill} ${styles.unreachable}`}>Backend unreachable</span>
        )}
        {user ? (
          <nav className={styles.nav}>
            <Link to="/me">My progress</Link>
            <span className={styles.displayName}>{user.display_name}</span>
            <button type="button" className={styles.signOutButton} onClick={handleSignOut}>
              Sign out
            </button>
          </nav>
        ) : (
          <nav className={styles.nav}>
            <Link to="/login">Sign in</Link>
            <Link to="/register">Register</Link>
          </nav>
        )}
      </div>
    </header>
  )
}

export default Header
