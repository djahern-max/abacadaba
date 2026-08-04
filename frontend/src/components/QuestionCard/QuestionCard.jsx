import styles from './QuestionCard.module.css'

const LETTERS = ['A', 'B', 'C', 'D']

function QuestionCard({ question }) {
  return (
    <div className={styles.card}>
      <p className={styles.prompt}>
        {question.position}. {question.prompt}
      </p>
      <ul className={styles.choices}>
        {question.choices.map((choice, index) => (
          <li key={choice.id} className={styles.choice}>
            <span className={styles.letter}>{LETTERS[index]}</span>
            <span className={styles.text}>{choice.text}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default QuestionCard
