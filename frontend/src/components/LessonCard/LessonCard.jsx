import { Link } from 'react-router-dom'
import styles from './LessonCard.module.css'

function formatDuration(seconds) {
  if (!seconds) return null
  return `${Math.round(seconds / 60)} min`
}

function LessonCard({ lesson }) {
  const duration = formatDuration(lesson.duration_seconds)

  return (
    <Link to={`/lessons/${lesson.slug}`} className={styles.card}>
      <h2 className={styles.title}>{lesson.title}</h2>
      <p className={styles.description}>{lesson.description}</p>
      {duration && <span className={styles.duration}>{duration}</span>}
    </Link>
  )
}

export default LessonCard
