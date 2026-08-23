import { useCallback, useEffect, useState } from 'react'
import { Link, Navigate, useParams } from 'react-router-dom'
import { getCourse, getLessonSegment } from '../../api/courses'
import ReviewPanel from '../../components/ReviewPanel/ReviewPanel'
import VideoPlayer from '../../components/VideoPlayer/VideoPlayer'
import styles from './LessonSegment.module.css'

function formatDuration(seconds) {
  if (!seconds) return null
  return `${Math.round(seconds / 60)} min`
}

function LessonSegment() {
  const { slug, lessonSlug } = useParams()
  const [state, setState] = useState({ status: 'loading', segment: null })
  const [watchUnlocked, setWatchUnlocked] = useState(false)

  // Reused from VideoPlayer's own watch-progress fetch (Feature 015) rather
  // than fetched again here - the review panel appears once this segment's
  // watch gate closes (5.01.2.1: "placed throughout the program").
  const handleProgressChange = useCallback((progress) => {
    setWatchUnlocked(progress.unlocked)
  }, [])

  useEffect(() => {
    setState({ status: 'loading', segment: null })
    setWatchUnlocked(false)
    // A one-lesson course has no segment page of its own - its content lives
    // on the course page now, so old links and bookmarks here redirect there
    // rather than 404ing. Cheap: one extra fetch on a rarely-hit route.
    getCourse(slug)
      .then((course) => {
        if (course.lessons.length === 1) {
          setState({ status: 'redirect', segment: null })
          return undefined
        }
        return getLessonSegment(slug, lessonSlug).then((segment) => setState({ status: 'loaded', segment }))
      })
      .catch((error) => {
        setState({ status: error.status === 404 ? 'not-found' : 'error', segment: null })
      })
  }, [slug, lessonSlug])

  if (state.status === 'loading') {
    return <p className={styles.message}>Loading segment&hellip;</p>
  }

  if (state.status === 'redirect') {
    return <Navigate to={`/courses/${slug}`} replace />
  }

  if (state.status === 'not-found') {
    return (
      <div className={styles.message}>
        <p>We couldn&apos;t find that segment.</p>
        <Link to={`/courses/${slug}`}>Back to course</Link>
      </div>
    )
  }

  if (state.status === 'error') {
    return <p className={styles.message}>Couldn&apos;t load this segment. Please try again later.</p>
  }

  const { segment } = state
  const duration = formatDuration(segment.duration_seconds)
  const hasVideo = Boolean(segment.video_key)

  return (
    <article className={styles.detail}>
      <Link to={`/courses/${slug}`} className={styles.back}>
        &larr; Back to {segment.course_title}
      </Link>
      <h1 className={styles.title}>{segment.title}</h1>
      {duration && <span className={styles.duration}>{duration}</span>}
      {hasVideo ? (
        <VideoPlayer courseSlug={slug} lessonSlug={segment.slug} onProgressChange={handleProgressChange} />
      ) : (
        <div className={styles.video}>Video coming soon</div>
      )}
      <p className={styles.description}>{segment.description}</p>

      {watchUnlocked && <ReviewPanel courseSlug={slug} lessonSlug={segment.slug} />}

      <nav className={styles.nav}>
        {segment.previous_lesson_slug ? (
          <Link to={`/courses/${slug}/lessons/${segment.previous_lesson_slug}`} className={styles.navLink}>
            &larr; Previous segment
          </Link>
        ) : (
          <span className={styles.navSpacer} />
        )}
        {segment.next_lesson_slug && (
          <Link to={`/courses/${slug}/lessons/${segment.next_lesson_slug}`} className={styles.navLink}>
            Next segment &rarr;
          </Link>
        )}
      </nav>
    </article>
  )
}

export default LessonSegment
