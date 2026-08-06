import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext.jsx'
import styles from './AdminGuard.module.css'

function AdminGuard({ children }) {
  const { user, loading } = useAuth()
  const location = useLocation()

  if (loading) {
    return <p className={styles.message}>Loading&hellip;</p>
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />
  }

  if (!user.is_admin) {
    return <p className={styles.message}>You don&apos;t have access to this page.</p>
  }

  return children
}

export default AdminGuard
