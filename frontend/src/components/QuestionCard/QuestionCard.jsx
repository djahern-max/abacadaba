import { useRef } from 'react'
import styles from './QuestionCard.module.css'

const LETTERS = ['A', 'B', 'C', 'D']

// No correctness here, deliberately: under 6.01.2 (no test bank), the
// application cannot know mid-attempt whether the participant will pass, so
// per-question feedback during the assessment is feedback on a failed
// assessment roughly half the time. See Result.jsx for the end-of-attempt
// breakdown, shown only on a pass.
function choiceState(choice, selectedChoiceId) {
  return choice.id === selectedChoiceId ? 'selected' : 'default'
}

function QuestionCard({
  question,
  selectedChoiceId,
  submitted,
  status,
  error,
  isLastQuestion,
  onSelectChoice,
  onSubmit,
  onRetry,
  onNext,
}) {
  const cardRef = useRef(null)

  const choicesLocked = status === 'submitting' || submitted

  return (
    <div className={styles.card} ref={cardRef}>
      <p className={styles.prompt}>
        {question.position}. {question.prompt}
      </p>
      <ul className={styles.choices}>
        {question.choices.map((choice, index) => {
          const visualState = choiceState(choice, selectedChoiceId)
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
        {submitted ? 'Answer submitted.' : ''}
      </div>

      {status === 'error' && (
        <div className={styles.errorBox}>
          <p className={styles.errorText}>{error}</p>
          <button type="button" className={styles.retryButton} onClick={onRetry}>
            Retry
          </button>
        </div>
      )}

      {status !== 'error' && !submitted && (
        <button
          type="button"
          className={styles.submitButton}
          onClick={onSubmit}
          disabled={selectedChoiceId == null || status === 'submitting'}
        >
          {status === 'submitting' ? 'Submitting…' : 'Submit'}
        </button>
      )}

      {submitted && (
        <button type="button" className={styles.nextButton} onClick={onNext}>
          {isLastQuestion ? 'Finish' : 'Next'}
        </button>
      )}
    </div>
  )
}

export default QuestionCard
