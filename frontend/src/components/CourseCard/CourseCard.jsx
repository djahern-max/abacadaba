import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getCourseThumbnailUrl } from '../../api/courses'
import styles from './CourseCard.module.css'

function segmentLabel(count) {
  return count === 1 ? '1 segment' : `${count} segments`
}

function CourseCard({ course }) {
  const [thumbnailUrl, setThumbnailUrl] = useState(null)

  useEffect(() => {
    if (!course.has_thumbnail) {
      setThumbnailUrl(null)
      return
    }
    let cancelled = false
    getCourseThumbnailUrl(course.slug)
      .then(({ url }) => {
        if (!cancelled) setThumbnailUrl(url)
      })
      .catch(() => {})
    return () => {
      cancelled = true
    }
  }, [course.has_thumbnail, course.slug])

  return (
    <Link to={`/courses/${course.slug}`} className={styles.card}>
      <div className={styles.thumbnailWrap}>
        {thumbnailUrl ? (
          <img src={thumbnailUrl} alt={course.title} className={styles.thumbnail} />
        ) : (
          <div className={styles.placeholder} aria-hidden="true" />
        )}
      </div>
      <h2 className={styles.title}>{course.title}</h2>
      <p className={styles.description}>{course.description}</p>
      <span className={styles.segmentCount}>{segmentLabel(course.lesson_count)}</span>
    </Link>
  )
}

export default CourseCard
