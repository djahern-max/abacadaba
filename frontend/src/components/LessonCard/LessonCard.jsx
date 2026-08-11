import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getThumbnailUrl } from '../../api/lessons'
import styles from './LessonCard.module.css'

function formatDuration(seconds) {
  if (!seconds) return null
  return `${Math.round(seconds / 60)} min`
}

function LessonCard({ lesson }) {
  const duration = formatDuration(lesson.duration_seconds)
  const [thumbnailUrl, setThumbnailUrl] = useState(null)

  useEffect(() => {
    if (!lesson.has_thumbnail) {
      setThumbnailUrl(null)
      return
    }
    let cancelled = false
    getThumbnailUrl(lesson.slug)
      .then(({ url }) => {
        if (!cancelled) setThumbnailUrl(url)
      })
      .catch(() => {})
    return () => {
      cancelled = true
    }
  }, [lesson.has_thumbnail, lesson.slug])

  return (
    <Link to={`/lessons/${lesson.slug}`} className={styles.card}>
      <div className={styles.thumbnailWrap}>
        {thumbnailUrl ? (
          <img src={thumbnailUrl} alt={lesson.title} className={styles.thumbnail} />
        ) : (
          <div className={styles.placeholder} aria-hidden="true" />
        )}
      </div>
      <h2 className={styles.title}>{lesson.title}</h2>
      <p className={styles.description}>{lesson.description}</p>
      {duration && <span className={styles.duration}>{duration}</span>}
    </Link>
  )
}

export default LessonCard
