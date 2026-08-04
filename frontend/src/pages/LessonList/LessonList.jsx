import { useEffect, useState } from 'react'
import { getLessons } from '../../api/lessons'
import LessonCard from '../../components/LessonCard/LessonCard'
import styles from './LessonList.module.css'

function LessonList() {
  const [state, setState] = useState({ status: 'loading', lessons: [] })

  useEffect(() => {
    getLessons()
      .then((lessons) => setState({ status: 'loaded', lessons }))
      .catch(() => setState({ status: 'error', lessons: [] }))
  }, [])

  if (state.status === 'loading') {
    return <p className={styles.message}>Loading lessons&hellip;</p>
  }

  if (state.status === 'error') {
    return <p className={styles.message}>Couldn&apos;t load lessons. Please try again later.</p>
  }

  if (state.lessons.length === 0) {
    return <p className={styles.message}>No lessons yet. Check back soon.</p>
  }

  return (
    <div className={styles.grid}>
      {state.lessons.map((lesson) => (
        <LessonCard key={lesson.id} lesson={lesson} />
      ))}
    </div>
  )
}

export default LessonList
