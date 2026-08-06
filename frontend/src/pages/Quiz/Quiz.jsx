import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { getQuiz } from '../../api/quiz'
import { startAttempt, submitAttemptAnswer } from '../../api/attempts'
import QuestionCard from '../../components/QuestionCard/QuestionCard'
import ProgressBar from '../../components/ProgressBar/ProgressBar'
import styles from './Quiz.module.css'

const INITIAL_ANSWER_STATE = {
  selectedChoiceId: null,
  status: 'idle', // idle | submitting | graded | error
  result: null,
  error: null,
}

function Quiz() {
  const { slug } = useParams()
  const navigate = useNavigate()
  const [state, setState] = useState({ status: 'loading', quiz: null, attemptId: null, lockedDetail: '' })
  const [currentIndex, setCurrentIndex] = useState(0)
  const [answerState, setAnswerState] = useState(INITIAL_ANSWER_STATE)

  useEffect(() => {
    setState({ status: 'loading', quiz: null, attemptId: null, lockedDetail: '' })
    setCurrentIndex(0)
    setAnswerState(INITIAL_ANSWER_STATE)

    Promise.all([getQuiz(slug), startAttempt(slug)])
      .then(([quiz, attempt]) =>
        setState({ status: 'loaded', quiz, attemptId: attempt.attempt_id, lockedDetail: '' }),
      )
      .catch((error) => {
        if (error.status === 403) {
          setState({
            status: 'locked',
            quiz: null,
            attemptId: null,
            lockedDetail: error.body?.detail ?? 'Watch more of the video before taking the quiz.',
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
  }, [slug])

  if (state.status === 'loading') {
    return <p className={styles.message}>Loading quiz&hellip;</p>
  }

  if (state.status === 'not-found') {
    return (
      <div className={styles.message}>
        <p>This lesson doesn&apos;t have a quiz yet.</p>
        <Link to={`/lessons/${slug}`}>Back to lesson</Link>
      </div>
    )
  }

  if (state.status === 'locked') {
    return (
      <div className={styles.message}>
        <p>{state.lockedDetail}</p>
        <Link to={`/lessons/${slug}`}>Back to lesson</Link>
      </div>
    )
  }

  if (state.status === 'error') {
    return <p className={styles.message}>Couldn&apos;t load this quiz. Please try again later.</p>
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
      .then((response) => {
        setAnswerState((prev) => ({
          ...prev,
          status: 'graded',
          result: { correct: response.correct, correctChoiceId: response.correct_choice_id },
        }))
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
      <Link to={`/lessons/${slug}`} className={styles.back}>
        &larr; Back to lesson
      </Link>
      <h1 className={styles.title}>{quiz.lesson_title}</h1>
      <ProgressBar current={currentIndex + 1} total={quiz.questions.length} />
      <QuestionCard
        question={question}
        selectedChoiceId={answerState.selectedChoiceId}
        result={answerState.result}
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
