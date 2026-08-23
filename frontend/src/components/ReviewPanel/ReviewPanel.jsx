import { useEffect, useState } from 'react'
import { getReviewQuestions, submitReviewAnswer } from '../../api/review'
import styles from './ReviewPanel.module.css'

const INITIAL_ANSWER_STATE = { selectedChoiceId: null, status: 'idle', result: null }

// 5.01.2.2: the verdict (correct/incorrect) is mandatory, the feedback text
// is optional - render the verdict always, the text when present. There is
// no minimum passing rate here (5.01.2.1), so re-answering just overwrites.
function ReviewQuestion({ courseSlug, lessonSlug, question }) {
  const [state, setState] = useState(INITIAL_ANSWER_STATE)

  function handleSelect(choiceId) {
    if (state.status === 'submitting') return
    setState({ selectedChoiceId: choiceId, status: 'idle', result: null })
  }

  function handleSubmit() {
    setState((prev) => ({ ...prev, status: 'submitting' }))
    submitReviewAnswer(courseSlug, lessonSlug, question.id, state.selectedChoiceId)
      .then((result) => setState((prev) => ({ ...prev, status: 'graded', result })))
      .catch(() => setState((prev) => ({ ...prev, status: 'error' })))
  }

  return (
    <div className={styles.question}>
      <p className={styles.prompt}>{question.prompt}</p>
      <ul className={styles.choices}>
        {question.choices.map((choice) => (
          <li key={choice.id}>
            <button
              type="button"
              className={`${styles.choice} ${choice.id === state.selectedChoiceId ? styles.selected : ''}`}
              onClick={() => handleSelect(choice.id)}
              disabled={state.status === 'submitting'}
              aria-pressed={choice.id === state.selectedChoiceId}
            >
              {choice.text}
            </button>
          </li>
        ))}
      </ul>

      {state.status === 'error' && (
        <p className={styles.errorText}>Couldn&apos;t submit your answer. Please try again.</p>
      )}

      {state.result ? (
        <div className={state.result.correct ? styles.verdictCorrect : styles.verdictIncorrect}>
          <p className={styles.verdictText}>{state.result.correct ? 'Correct' : 'Incorrect'}</p>
          {state.result.feedback && <p className={styles.feedbackText}>{state.result.feedback}</p>}
          <button type="button" className={styles.retryButton} onClick={() => setState(INITIAL_ANSWER_STATE)}>
            Try again
          </button>
        </div>
      ) : (
        <button
          type="button"
          className={styles.submitButton}
          onClick={handleSubmit}
          disabled={state.selectedChoiceId == null || state.status === 'submitting'}
        >
          {state.status === 'submitting' ? 'Submitting…' : 'Submit'}
        </button>
      )}
    </div>
  )
}

function ReviewPanel({ courseSlug, lessonSlug }) {
  const [state, setState] = useState({ status: 'loading', questions: [] })

  useEffect(() => {
    setState({ status: 'loading', questions: [] })
    getReviewQuestions(courseSlug, lessonSlug)
      .then((data) => setState({ status: 'loaded', questions: data.questions }))
      .catch(() => setState({ status: 'error', questions: [] }))
  }, [courseSlug, lessonSlug])

  if (state.status !== 'loaded' || state.questions.length === 0) {
    return null
  }

  return (
    <section className={styles.panel}>
      <h2 className={styles.heading}>Check your understanding</h2>
      {state.questions.map((question) => (
        <ReviewQuestion key={question.id} courseSlug={courseSlug} lessonSlug={lessonSlug} question={question} />
      ))}
    </section>
  )
}

export default ReviewPanel
