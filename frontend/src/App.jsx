import { useEffect, useState } from 'react'
import { Link, Route, Routes } from 'react-router-dom'
import { getHealth } from './api/health'
import LessonList from './pages/LessonList/LessonList'
import LessonDetail from './pages/LessonDetail/LessonDetail'
import Quiz from './pages/Quiz/Quiz'
import Result from './pages/Result/Result'
import styles from './App.module.css'

function NotFound() {
  return (
    <div className={styles.notFound}>
      <p>Page not found.</p>
      <Link to="/">Back home</Link>
    </div>
  )
}

function App() {
  const [status, setStatus] = useState('checking')

  useEffect(() => {
    getHealth()
      .then(() => setStatus('connected'))
      .catch(() => setStatus('unreachable'))
  }, [])

  return (
    <div className={styles.app}>
      <header className={styles.header}>
        <Link to="/" className={styles.wordmark}>
          abacadaba
        </Link>
        {status === 'checking' && (
          <span className={`${styles.pill} ${styles.checking}`}>Checking backend&hellip;</span>
        )}
        {status === 'connected' && (
          <span className={`${styles.pill} ${styles.connected}`}>Backend connected</span>
        )}
        {status === 'unreachable' && (
          <span className={`${styles.pill} ${styles.unreachable}`}>Backend unreachable</span>
        )}
      </header>
      <main className={styles.main}>
        <Routes>
          <Route path="/" element={<LessonList />} />
          <Route path="/lessons/:slug" element={<LessonDetail />} />
          <Route path="/lessons/:slug/quiz" element={<Quiz />} />
          <Route path="/attempts/:attemptId" element={<Result />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
