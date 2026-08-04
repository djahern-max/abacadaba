import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getLesson } from '../../api/lessons'
import VideoPlayer from '../../components/VideoPlayer/VideoPlayer'
import styles from './LessonDetail.module.css'

function formatDuration(seconds) {
  if (!seconds) return null
  return `${Math.round(seconds / 60)} min`
}

function LessonDetail() {
  const { slug } = useParams()
  const [state, setState] = useState({ status: 'loading', lesson: null })

  useEffect(() => {
    setState({ status: 'loading', lesson: null })
    getLesson(slug)
      .then((lesson) => setState({ status: 'loaded', lesson }))
      .catch((error) => {
        setState({ status: error.status === 404 ? 'not-found' : 'error', lesson: null })
      })
  }, [slug])

  if (state.status === 'loading') {
    return <p className={styles.message}>Loading lesson&hellip;</p>
  }

  if (state.status === 'not-found') {
    return (
      <div className={styles.message}>
        <p>We couldn&apos;t find that lesson.</p>
        <Link to="/">Back to lessons</Link>
      </div>
    )
  }

  if (state.status === 'error') {
    return <p className={styles.message}>Couldn&apos;t load this lesson. Please try again later.</p>
  }

  const duration = formatDuration(state.lesson.duration_seconds)

  return (
    <article className={styles.detail}>
      <Link to="/" className={styles.back}>
        &larr; Back to lessons
      </Link>
      <h1 className={styles.title}>{state.lesson.title}</h1>
      {duration && <span className={styles.duration}>{duration}</span>}
      {state.lesson.video_key ? (
        <VideoPlayer slug={state.lesson.slug} />
      ) : (
        <div className={styles.video}>Video coming soon</div>
      )}
      <p className={styles.description}>{state.lesson.description}</p>
      <Link to={`/lessons/${state.lesson.slug}/quiz`} className={styles.quizButton}>
        Take the quiz
      </Link>
    </article>
  )
}

export default LessonDetail
