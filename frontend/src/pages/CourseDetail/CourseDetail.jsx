import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getCourse, getCourseWatchStatus } from '../../api/courses'
import LessonCard from '../../components/LessonCard/LessonCard'
import ReviewPanel from '../../components/ReviewPanel/ReviewPanel'
import VideoPlayer from '../../components/VideoPlayer/VideoPlayer'
import { useAuth } from '../../context/AuthContext.jsx'
import styles from './CourseDetail.module.css'

function CourseDetail() {
  const { slug } = useParams()
  const { user, loading: authLoading } = useAuth()
  const [state, setState] = useState({ status: 'loading', course: null })
  const [watchStatus, setWatchStatus] = useState(null)
  const [singleLessonProgress, setSingleLessonProgress] = useState(null)

  useEffect(() => {
    setState({ status: 'loading', course: null })
    setWatchStatus(null)
    setSingleLessonProgress(null)
    getCourse(slug)
      .then((course) => setState({ status: 'loaded', course }))
      .catch((error) => {
        setState({ status: error.status === 404 ? 'not-found' : 'error', course: null })
      })
  }, [slug])

  useEffect(() => {
    if (!user) return
    getCourseWatchStatus(slug)
      .then(setWatchStatus)
      .catch(() => {})
  }, [slug, user])

  if (state.status === 'loading') {
    return <p className={styles.message}>Loading course&hellip;</p>
  }

  if (state.status === 'not-found') {
    return (
      <div className={styles.message}>
        <p>We couldn&apos;t find that course.</p>
        <Link to="/">Back to courses</Link>
      </div>
    )
  }

  if (state.status === 'error') {
    return <p className={styles.message}>Couldn&apos;t load this course. Please try again later.</p>
  }

  const { course } = state
  // A course renders collapsed when it has exactly one lesson - derived on
  // every render, never stored. See current-feature.md, "One rule, derived".
  const singleLesson = course.lessons.length === 1 ? course.lessons[0] : null
  const watchedBySlug = Object.fromEntries(
    (watchStatus?.lessons ?? []).map((item) => [item.lesson_slug, item.progress.unlocked]),
  )
  const outstanding = watchStatus?.lessons.find((item) => !item.progress.unlocked)
  const gateMet =
    user?.is_admin ||
    (singleLesson ? singleLessonProgress?.unlocked === true : watchStatus?.gate_met === true)
  const levelLabel = course.program_level.charAt(0).toUpperCase() + course.program_level.slice(1)
  // ISO date strings compare lexicographically, so no Date parsing/timezone
  // edge cases - 9.02.2.
  const todayIso = new Date().toISOString().slice(0, 10)
  const isExpired = course.expires_on != null && course.expires_on < todayIso

  return (
    <article className={styles.detail}>
      <Link to="/" className={styles.back}>
        &larr; Back to courses
      </Link>
      <h1 className={styles.title}>{course.title}</h1>
      <p className={styles.description}>{course.description}</p>

      {course.learning_objectives.length > 0 && (
        <section className={styles.objectives}>
          <h2 className={styles.sectionHeading}>What you will learn</h2>
          <ul className={styles.objectivesList}>
            {course.learning_objectives.map((objective) => (
              <li key={objective.position}>{objective.text}</li>
            ))}
          </ul>
        </section>
      )}

      <dl className={styles.programDetails}>
        <div className={styles.programDetail}>
          <dt>Program level</dt>
          <dd>{levelLabel}</dd>
        </div>
        <div className={styles.programDetail}>
          <dt>Field of study</dt>
          <dd>{course.field_of_study}</dd>
        </div>
        <div className={styles.programDetail}>
          <dt>Prerequisites</dt>
          <dd>{course.prerequisites || 'None'}</dd>
        </div>
        <div className={styles.programDetail}>
          <dt>Advance preparation</dt>
          <dd>{course.advance_preparation || 'None'}</dd>
        </div>
        <div className={styles.programDetail}>
          <dt>CPE credit</dt>
          <dd>{course.credit_award != null ? `${course.credit_award} credit` : 'Not yet available'}</dd>
        </div>
        <div className={styles.programDetail}>
          <dt>Expires</dt>
          <dd>
            {course.expires_on != null ? new Date(course.expires_on).toLocaleDateString() : 'Not yet available'}
          </dd>
        </div>
      </dl>

      <nav className={styles.policyLinks}>
        <Link to="/policies/refund-and-cancellation">Refund and cancellation policy</Link>
        <Link to="/policies/complaint-resolution">Complaint resolution policy</Link>
      </nav>

      {course.reviewed_at && (
        <section className={styles.reviewInfo}>
          <p className={styles.reviewDate}>
            Last reviewed {new Date(course.reviewed_at).toLocaleDateString()}
          </p>
          {(course.developer || course.reviewer) && (
            <ul className={styles.reviewCredits}>
              {course.developer && (
                <li>
                  Developed by {course.developer.name}, {course.developer.credentials}
                </li>
              )}
              {course.reviewer && (
                <li>
                  Reviewed by {course.reviewer.name}, {course.reviewer.credentials}
                </li>
              )}
            </ul>
          )}
        </section>
      )}

      {singleLesson ? (
        <>
          <VideoPlayer
            courseSlug={course.slug}
            lessonSlug={singleLesson.slug}
            onProgressChange={setSingleLessonProgress}
          />
          {singleLessonProgress?.unlocked && (
            <ReviewPanel courseSlug={course.slug} lessonSlug={singleLesson.slug} />
          )}
        </>
      ) : (
        <ol className={styles.lessonList}>
          {course.lessons.map((lesson) => (
            <li key={lesson.id}>
              <LessonCard
                courseSlug={course.slug}
                lesson={lesson}
                watched={watchStatus ? watchedBySlug[lesson.slug] : undefined}
              />
            </li>
          ))}
        </ol>
      )}

      {isExpired ? (
        <span className={styles.assessmentButtonDisabled}>
          This program expired on {new Date(course.expires_on).toLocaleDateString()} and is no longer accepting
          new attempts.
        </span>
      ) : authLoading ? (
        <span className={styles.assessmentButtonDisabled}>Checking your watch progress&hellip;</span>
      ) : !user ? (
        <Link to="/login" state={{ from: `/courses/${course.slug}` }} className={styles.assessmentButton}>
          Sign in to take the assessment
        </Link>
      ) : gateMet ? (
        <Link to={`/courses/${course.slug}/quiz`} className={styles.assessmentButton}>
          Take the assessment
        </Link>
      ) : (
        <span className={styles.assessmentButtonDisabled}>
          {singleLesson
            ? 'Watch the video to unlock the assessment'
            : outstanding
              ? `Watch "${outstanding.lesson_title}" to unlock the assessment`
              : 'Checking your watch progress…'}
        </span>
      )}
    </article>
  )
}

export default CourseDetail
