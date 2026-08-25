import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import styles from './AccountMenu.module.css'

function AccountMenu({ user, onSignOut }) {
  const [open, setOpen] = useState(false)
  const buttonRef = useRef(null)
  const menuRef = useRef(null)
  const navigate = useNavigate()

  useEffect(() => {
    if (!open) return

    function handlePointerDown(event) {
      if (menuRef.current?.contains(event.target) || buttonRef.current?.contains(event.target)) return
      setOpen(false)
    }

    function handleKeyDown(event) {
      const items = Array.from(menuRef.current?.querySelectorAll('[role="menuitem"]') ?? [])
      const currentIndex = items.indexOf(document.activeElement)

      if (event.key === 'Escape') {
        event.preventDefault()
        setOpen(false)
        buttonRef.current?.focus()
      } else if (event.key === 'ArrowDown') {
        event.preventDefault()
        items[(currentIndex + 1) % items.length]?.focus()
      } else if (event.key === 'ArrowUp') {
        event.preventDefault()
        items[(currentIndex - 1 + items.length) % items.length]?.focus()
      }
    }

    document.addEventListener('pointerdown', handlePointerDown)
    document.addEventListener('keydown', handleKeyDown)
    menuRef.current?.querySelector('[role="menuitem"]')?.focus()

    return () => {
      document.removeEventListener('pointerdown', handlePointerDown)
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [open])

  async function handleSignOut() {
    setOpen(false)
    await onSignOut()
    navigate('/')
  }

  return (
    <div className={styles.container}>
      <button
        type="button"
        ref={buttonRef}
        className={styles.trigger}
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        {user.display_name}
        <span className={styles.caret} aria-hidden="true">
          ▾
        </span>
      </button>
      {open && (
        <div className={styles.menu} role="menu" ref={menuRef}>
          {user.is_admin && (
            <Link to="/admin" role="menuitem" className={styles.menuItem} onClick={() => setOpen(false)}>
              Admin
            </Link>
          )}
          <button type="button" role="menuitem" className={styles.menuItem} onClick={handleSignOut}>
            Sign out
          </button>
        </div>
      )}
    </div>
  )
}

export default AccountMenu
