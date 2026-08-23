import styles from './AnswerBreakdown.module.css'

// Only ever rendered on a passed attempt (Result.jsx) - per-question
// correctness on a failed assessment is not permitted (6.01.2, no-test-bank
// arm). The server never sends this data for a failed attempt in the first
// place; this component doesn't re-derive that decision, just renders it.
function AnswerBreakdown({ answers }) {
  return (
    <section className={styles.breakdown}>
      <h2 className={styles.heading}>Your answers</h2>
      <ol className={styles.list}>
        {answers.map((answer) => (
          <li
            key={answer.question_id}
            className={answer.is_correct ? styles.itemCorrect : styles.itemIncorrect}
          >
            <p className={styles.prompt}>{answer.prompt}</p>
            <p className={styles.answerLine}>
              Your answer: {answer.chosen_choice_text} {answer.is_correct ? '(correct)' : '(incorrect)'}
            </p>
            {!answer.is_correct && (
              <p className={styles.answerLine}>Correct answer: {answer.correct_choice_text}</p>
            )}
            {answer.feedback && <p className={styles.answerLine}>{answer.feedback}</p>}
          </li>
        ))}
      </ol>
    </section>
  )
}

export default AnswerBreakdown
