import { useEffect, useState } from 'react'
import { Link, Navigate, useNavigate, useParams } from 'react-router-dom'
import { getQuiz } from '../../api/quiz'
import { startAttempt, submitAttemptAnswer } from '../../api/attempts'
import QuestionCard from '../../components/QuestionCard/QuestionCard'
import ProgressBar from '../../components/ProgressBar/ProgressBar'
import { useAuth } from '../../context/AuthContext.jsx'
import styles from './Quiz.module.css'

const INITIAL_ANSWER_STATE = {
  selectedChoiceId: null,
  status: 'idle', // idle | submitting | submitted | error
  error: null,
}

function Quiz() {
  const { slug } = useParams()
  const navigate = useNavigate()
  const { user, loading: authLoading } = useAuth()
  const [state, setState] = useState({ status: 'loading', quiz: null, attemptId: null, lockedDetail: '' })
  const [currentIndex, setCurrentIndex] = useState(0)
  const [answerState, setAnswerState] = useState(INITIAL_ANSWER_STATE)

  useEffect(() => {
    if (authLoading || !user) return

    setState({ status: 'loading', quiz: null, attemptId: null, lockedDetail: '' })
    setCurrentIndex(0)
    setAnswerState(INITIAL_ANSWER_STATE)

    startAttempt(slug)
      .then((attempt) => getQuiz(slug, attempt.attempt_id).then((quiz) => ({ quiz, attempt })))
      .then(({ quiz, attempt }) =>
        setState({ status: 'loaded', quiz, attemptId: attempt.attempt_id, lockedDetail: '' }),
      )
      .catch((error) => {
        if (error.status === 403) {
          setState({
            status: 'locked',
            quiz: null,
            attemptId: null,
            lockedDetail: error.body?.detail ?? 'Watch more of the course before taking the assessment.',
          })
          return
        }
        if (error.status === 429) {
          setState({
            status: 'limited',
            quiz: null,
            attemptId: null,
            lockedDetail: error.body?.detail ?? "You've reached the retake limit for this assessment.",
          })
          return
        }
        setState({
          status: error.status === 404 ? 'not-found' : 'error',
          quiz: null,
          attemptId: null,
          lockedDetail: '',
        })
      })
  }, [slug, authLoading, user])

  if (authLoading) {
    return <p className={styles.message}>Loading assessment&hellip;</p>
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: `/courses/${slug}` }} replace />
  }

  if (state.status === 'loading') {
    return <p className={styles.message}>Loading assessment&hellip;</p>
  }

  if (state.status === 'not-found') {
    return (
      <div className={styles.message}>
        <p>This course doesn&apos;t have an assessment yet.</p>
        <Link to={`/courses/${slug}`}>Back to course</Link>
      </div>
    )
  }

  if (state.status === 'locked' || state.status === 'limited') {
    return (
      <div className={styles.message}>
        <p>{state.lockedDetail}</p>
        <Link to={`/courses/${slug}`}>Back to course</Link>
      </div>
    )
  }

  if (state.status === 'error') {
    return <p className={styles.message}>Couldn&apos;t load this assessment. Please try again later.</p>
  }

  const { quiz, attemptId } = state
  const question = quiz.questions[currentIndex]
  const isLastQuestion = currentIndex === quiz.questions.length - 1

  function handleSelectChoice(choiceId) {
    setAnswerState((prev) => ({ ...prev, selectedChoiceId: choiceId }))
  }

  function submitCurrentAnswer() {
    setAnswerState((prev) => ({ ...prev, status: 'submitting', error: null }))
    submitAttemptAnswer(attemptId, question.id, answerState.selectedChoiceId)
      .then(() => {
        setAnswerState((prev) => ({ ...prev, status: 'submitted' }))
      })
      .catch(() => {
        setAnswerState((prev) => ({
          ...prev,
          status: 'error',
          error: "Couldn't submit your answer. Please try again.",
        }))
      })
  }

  function handleNext() {
    if (isLastQuestion) {
      navigate(`/attempts/${attemptId}`)
      return
    }
    setCurrentIndex((prev) => prev + 1)
    setAnswerState(INITIAL_ANSWER_STATE)
  }

  return (
    <div className={styles.quiz}>
      <Link to={`/courses/${slug}`} className={styles.back}>
        &larr; Back to course
      </Link>
      <h1 className={styles.title}>{quiz.course_title}</h1>
      <ProgressBar current={currentIndex + 1} total={quiz.questions.length} />
      <QuestionCard
        question={question}
        selectedChoiceId={answerState.selectedChoiceId}
        submitted={answerState.status === 'submitted'}
        status={answerState.status}
        error={answerState.error}
        isLastQuestion={isLastQuestion}
        onSelectChoice={handleSelectChoice}
        onSubmit={submitCurrentAnswer}
        onRetry={submitCurrentAnswer}
        onNext={handleNext}
      />
    </div>
  )
}

export default Quiz
