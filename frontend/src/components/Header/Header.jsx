import { useEffect, useState } from 'react'
import { Link, NavLink } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext.jsx'
import Wordmark from '../Wordmark/Wordmark'
import AccountMenu from './AccountMenu'
import styles from './Header.module.css'

function Header() {
  const { user, logout } = useAuth()
  const [scrolled, setScrolled] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  useEffect(() => {
    function handleScroll() {
      setScrolled(window.scrollY > 8)
    }
    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <header className={scrolled ? `${styles.header} ${styles.scrolled}` : styles.header}>
      <div className={styles.bar}>
        <Wordmark />

        <button
          type="button"
          className={styles.mobileToggle}
          aria-haspopup="true"
          aria-expanded={mobileOpen}
          aria-label="Toggle menu"
          onClick={() => setMobileOpen((value) => !value)}
        >
          <span aria-hidden="true">☰</span>
        </button>

        <div className={mobileOpen ? `${styles.zones} ${styles.zonesOpen}` : styles.zones}>
          {user && (
            <nav className={styles.productNav} aria-label="Product">
              <NavLink to="/me" className={styles.navLink}>
                My progress
              </NavLink>
            </nav>
          )}

          <div className={styles.account}>
            {user ? (
              <AccountMenu user={user} onSignOut={logout} />
            ) : (
              <Link to="/login" className={styles.signIn}>
                Sign in
              </Link>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}

export default Header
