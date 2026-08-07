import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext.jsx'
import styles from './Header.module.css'

function Header() {
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
        {user ? (
          <nav className={styles.nav}>
            <Link to="/me">My progress</Link>
            {user.is_admin && <Link to="/admin">Admin</Link>}
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
