import { useEffect, useState } from 'react'
import { getHealth } from './api/health'
import styles from './App.module.css'

function App() {
  const [status, setStatus] = useState('checking')

  useEffect(() => {
    getHealth()
      .then(() => setStatus('connected'))
      .catch(() => setStatus('unreachable'))
  }, [])

  return (
    <div className={styles.app}>
      <h1 className={styles.title}>abacadaba</h1>
      {status === 'checking' && (
        <span className={`${styles.pill} ${styles.checking}`}>Checking backend&hellip;</span>
      )}
      {status === 'connected' && (
        <span className={`${styles.pill} ${styles.connected}`}>Backend connected</span>
      )}
      {status === 'unreachable' && (
        <span className={`${styles.pill} ${styles.unreachable}`}>Backend unreachable</span>
      )}
    </div>
  )
}

export default App
