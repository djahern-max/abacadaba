import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getQuiz, submitAnswer } from '../../api/quiz'
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
  const [state, setState] = useState({ status: 'loading', quiz: null })
  const [currentIndex, setCurrentIndex] = useState(0)
  const [answerState, setAnswerState] = useState(INITIAL_ANSWER_STATE)
  const [results, setResults] = useState([])
  const [finished, setFinished] = useState(false)

  useEffect(() => {
    setState({ status: 'loading', quiz: null })
    setCurrentIndex(0)
    setAnswerState(INITIAL_ANSWER_STATE)
    setResults([])
    setFinished(false)
    getQuiz(slug)
      .then((quiz) => setState({ status: 'loaded', quiz }))
      .catch((error) => {
        setState({ status: error.status === 404 ? 'not-found' : 'error', quiz: null })
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

  if (state.status === 'error') {
    return <p className={styles.message}>Couldn&apos;t load this quiz. Please try again later.</p>
  }

  const { quiz } = state

  if (finished) {
    return (
      <div className={styles.quiz}>
        <div className={styles.complete}>
          <h1 className={styles.title}>Quiz complete</h1>
          <p>
            You answered {results.length} of {quiz.question_count} questions.
          </p>
          <p className={styles.note}>Scoring and certificates are coming in a future update.</p>
          <Link to={`/lessons/${slug}`}>Back to lesson</Link>
        </div>
      </div>
    )
  }

  const question = quiz.questions[currentIndex]
  const isLastQuestion = currentIndex === quiz.questions.length - 1

  function handleSelectChoice(choiceId) {
    setAnswerState((prev) => ({ ...prev, selectedChoiceId: choiceId }))
  }

  function submitCurrentAnswer() {
    setAnswerState((prev) => ({ ...prev, status: 'submitting', error: null }))
    submitAnswer(slug, question.id, answerState.selectedChoiceId)
      .then((response) => {
        setAnswerState((prev) => ({
          ...prev,
          status: 'graded',
          result: { correct: response.correct, correctChoiceId: response.correct_choice_id },
        }))
        setResults((prev) => [...prev, { questionId: question.id, correct: response.correct }])
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
      setFinished(true)
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
