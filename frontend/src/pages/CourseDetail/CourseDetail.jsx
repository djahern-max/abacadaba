import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getCourse, getCourseWatchStatus } from '../../api/courses'
import LessonCard from '../../components/LessonCard/LessonCard'
import ReviewPanel from '../../components/ReviewPanel/ReviewPanel'
import VideoPlayer from '../../components/VideoPlayer/VideoPlayer'
import { programLabel } from '../../constants/programLabels'
import { useAuth } from '../../context/AuthContext.jsx'
import styles from './CourseDetail.module.css'

// Part 4: "Length is derived from runtime, not from credit" - the sum of
// each published lesson's measured duration, not credit_award multiplied
// back out (see current-feature.md for why that arithmetic is confidently
// wrong by up to nine minutes).
function formatRuntimeMinutes(lessons) {
  const totalSeconds = lessons.reduce((sum, lesson) => sum + (lesson.duration_seconds || 0), 0)
  const minutes = Math.round(totalSeconds / 60)
  return `${minutes} minute${minutes === 1 ? '' : 's'}`
}

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
  // Feature 029: decides which CPE furniture renders, not a role check -
  // see current-feature.md, "Why this is not a role check". A general
  // course's payload has no sponsor_registry_status/field_of_study/
  // credit_award/expires_on keys at all (Part 2), so every branch below
  // that reads them is gated on isCpe first.
  const isCpe = course.program_kind === 'cpe'
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

      {isCpe && course.sponsor_registry_status !== 'registered' && (
        <p className={styles.notRegisteredNotice}>
          This program is not offered by a sponsor registered with NASBA, and completing it will not earn CPE
          credit.
        </p>
      )}

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
          <dt>{programLabel(course.program_kind, 'programLevel')}</dt>
          <dd>{levelLabel}</dd>
        </div>
        {isCpe && (
          <div className={styles.programDetail}>
            <dt>Field of study</dt>
            <dd>{course.field_of_study}</dd>
          </div>
        )}
        <div className={styles.programDetail}>
          <dt>{programLabel(course.program_kind, 'prerequisites')}</dt>
          <dd>{course.prerequisites || 'None'}</dd>
        </div>
        <div className={styles.programDetail}>
          <dt>{programLabel(course.program_kind, 'advancePreparation')}</dt>
          <dd>{course.advance_preparation || 'None'}</dd>
        </div>
        <div className={styles.programDetail}>
          <dt>{programLabel(course.program_kind, 'length')}</dt>
          <dd>
            {isCpe
              ? course.credit_award != null
                ? `${course.credit_award} credit`
                : 'Not yet available'
              : formatRuntimeMinutes(course.lessons)}
          </dd>
        </div>
        {isCpe && (
          <div className={styles.programDetail}>
            <dt>Expires</dt>
            <dd>
              {course.expires_on != null ? new Date(course.expires_on).toLocaleDateString() : 'Not yet available'}
            </dd>
          </div>
        )}
      </dl>

      {isCpe && (
        <nav className={styles.policyLinks}>
          <Link to="/policies/refund-and-cancellation">Refund and cancellation policy</Link>
          <Link to="/policies/complaint-resolution">Complaint resolution policy</Link>
        </nav>
      )}

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

      <section className={styles.howItWorks}>
        <h2 className={styles.sectionHeading}>How this course works</h2>
        <p>
          This course has {course.lessons.length} segment{course.lessons.length === 1 ? '' : 's'}. Each segment has
          review questions along the way to check your understanding &mdash; practice only, and not graded. After
          you have watched every segment, a single {course.assessment_question_count}-question{' '}
          {programLabel(course.program_kind, 'assessment')} covers the whole course. Score at least{' '}
          {Math.round(course.pass_ratio * 100)}% to pass and get your certificate.
        </p>
      </section>

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
