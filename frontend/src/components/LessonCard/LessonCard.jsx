import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getLessonThumbnailUrl } from '../../api/courses'
import styles from './LessonCard.module.css'

function formatDuration(seconds) {
  if (!seconds) return null
  return `${Math.round(seconds / 60)} min`
}

function LessonCard({ courseSlug, lesson, watched }) {
  const duration = formatDuration(lesson.duration_seconds)
  const [thumbnailUrl, setThumbnailUrl] = useState(null)

  useEffect(() => {
    if (!lesson.has_thumbnail) {
      setThumbnailUrl(null)
      return
    }
    let cancelled = false
    getLessonThumbnailUrl(courseSlug, lesson.slug)
      .then(({ url }) => {
        if (!cancelled) setThumbnailUrl(url)
      })
      .catch(() => {})
    return () => {
      cancelled = true
    }
  }, [courseSlug, lesson.has_thumbnail, lesson.slug])

  return (
    <Link to={`/courses/${courseSlug}/lessons/${lesson.slug}`} className={styles.card}>
      <div className={styles.thumbnailWrap}>
        {thumbnailUrl ? (
          <img src={thumbnailUrl} alt={lesson.title} className={styles.thumbnail} />
        ) : (
          <div className={styles.placeholder} aria-hidden="true" />
        )}
      </div>
      <h2 className={styles.title}>
        {lesson.position}. {lesson.title}
      </h2>
      <p className={styles.description}>{lesson.description}</p>
      <div className={styles.meta}>
        {duration && <span className={styles.duration}>{duration}</span>}
        {watched !== undefined && (
          <span className={watched ? styles.watched : styles.notWatched}>
            {watched ? 'Watched' : 'Not watched yet'}
          </span>
        )}
      </div>
    </Link>
  )
}

export default LessonCard
