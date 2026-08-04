import { useEffect, useRef } from 'react'
import { smallBurst } from '../../lib/confetti'
import styles from './QuestionCard.module.css'

const LETTERS = ['A', 'B', 'C', 'D']

function choiceState(choice, selectedChoiceId, result) {
  if (result) {
    if (choice.id === result.correctChoiceId) return 'correct'
    if (choice.id === selectedChoiceId) return 'incorrect'
    return 'default'
  }
  return choice.id === selectedChoiceId ? 'selected' : 'default'
}

function QuestionCard({
  question,
  selectedChoiceId,
  result,
  status,
  error,
  isLastQuestion,
  onSelectChoice,
  onSubmit,
  onRetry,
  onNext,
}) {
  const cardRef = useRef(null)

  useEffect(() => {
    if (result && result.correct) {
      smallBurst(cardRef.current)
    }
  }, [result])

  const choicesLocked = status === 'submitting' || status === 'graded'

  let announcement = ''
  if (result) {
    announcement = result.correct ? 'Correct!' : 'Incorrect. The correct answer is highlighted.'
  }

  return (
    <div className={styles.card} ref={cardRef}>
      <p className={styles.prompt}>
        {question.position}. {question.prompt}
      </p>
      <ul className={styles.choices}>
        {question.choices.map((choice, index) => {
          const visualState = choiceState(choice, selectedChoiceId, result)
          return (
            <li key={choice.id}>
              <button
                type="button"
                className={`${styles.choice} ${styles[visualState]}`}
                onClick={() => onSelectChoice(choice.id)}
                disabled={choicesLocked}
                aria-pressed={choice.id === selectedChoiceId}
              >
                <span className={styles.letter}>{LETTERS[index]}</span>
                <span className={styles.text}>{choice.text}</span>
              </button>
            </li>
          )
        })}
      </ul>

      <div aria-live="polite" className={styles.visuallyHidden}>
        {announcement}
      </div>

      {status === 'error' && (
        <div className={styles.errorBox}>
          <p className={styles.errorText}>{error}</p>
          <button type="button" className={styles.retryButton} onClick={onRetry}>
            Retry
          </button>
        </div>
      )}

      {status !== 'error' && !result && (
        <button
          type="button"
          className={styles.submitButton}
          onClick={onSubmit}
          disabled={selectedChoiceId == null || status === 'submitting'}
        >
          {status === 'submitting' ? 'Submitting…' : 'Submit'}
        </button>
      )}

      {result && (
        <button type="button" className={styles.nextButton} onClick={onNext}>
          {isLastQuestion ? 'Finish' : 'Next'}
        </button>
      )}
    </div>
  )
}

export default QuestionCard
