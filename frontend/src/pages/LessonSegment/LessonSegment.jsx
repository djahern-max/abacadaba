import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getLessonSegment } from '../../api/courses'
import VideoPlayer from '../../components/VideoPlayer/VideoPlayer'
import styles from './LessonSegment.module.css'

function formatDuration(seconds) {
  if (!seconds) return null
  return `${Math.round(seconds / 60)} min`
}

function LessonSegment() {
  const { slug, lessonSlug } = useParams()
  const [state, setState] = useState({ status: 'loading', segment: null })

  useEffect(() => {
    setState({ status: 'loading', segment: null })
    getLessonSegment(slug, lessonSlug)
      .then((segment) => setState({ status: 'loaded', segment }))
      .catch((error) => {
        setState({ status: error.status === 404 ? 'not-found' : 'error', segment: null })
      })
  }, [slug, lessonSlug])

  if (state.status === 'loading') {
    return <p className={styles.message}>Loading segment&hellip;</p>
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
        <VideoPlayer courseSlug={slug} lessonSlug={segment.slug} />
      ) : (
        <div className={styles.video}>Video coming soon</div>
      )}
      <p className={styles.description}>{segment.description}</p>

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
