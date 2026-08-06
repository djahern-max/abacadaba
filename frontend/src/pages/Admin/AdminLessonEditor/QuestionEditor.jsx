import { useState } from 'react'
import { createAdminChoice, deleteAdminQuestion, moveAdminQuestion, updateAdminQuestion } from '../../../api/admin'
import ChoiceRow from './ChoiceRow'
import styles from './QuestionEditor.module.css'

function QuestionEditor({ question, isFirst, isLast, onChange }) {
  const [prompt, setPrompt] = useState(question.prompt)
  const [newChoiceText, setNewChoiceText] = useState('')
  const [error, setError] = useState('')

  async function handleSavePrompt() {
    setError('')
    try {
      await updateAdminQuestion(question.id, prompt)
      await onChange()
    } catch {
      setError('Could not save this question.')
    }
  }

  async function handleMove(direction) {
    await moveAdminQuestion(question.id, direction)
    await onChange()
  }

  async function handleDeleteQuestion() {
    await deleteAdminQuestion(question.id)
    await onChange()
  }

  async function handleAddChoice(event) {
    event.preventDefault()
    if (!newChoiceText.trim()) return
    await createAdminChoice(question.id, newChoiceText.trim())
    setNewChoiceText('')
    await onChange()
  }

  return (
    <div className={styles.question}>
      <div className={styles.promptRow}>
        <span className={styles.position}>{question.position}.</span>
        <textarea
          className={styles.promptInput}
          rows={2}
          value={prompt}
          onChange={(event) => setPrompt(event.target.value)}
        />
      </div>
      <div className={styles.questionActions}>
        <button type="button" onClick={() => handleMove('up')} disabled={isFirst}>
          Move up
        </button>
        <button type="button" onClick={() => handleMove('down')} disabled={isLast}>
          Move down
        </button>
        <button type="button" onClick={handleSavePrompt} disabled={prompt === question.prompt}>
          Save
        </button>
        <button type="button" className={styles.dangerButton} onClick={handleDeleteQuestion}>
          Delete question
        </button>
      </div>
      {error && <p className={styles.fieldError}>{error}</p>}

      <ul className={styles.choices}>
        {question.choices.map((choice) => (
          <ChoiceRow key={choice.id} choice={choice} questionId={question.id} onChange={onChange} />
        ))}
      </ul>

      <form className={styles.addChoiceForm} onSubmit={handleAddChoice}>
        <input
          className={styles.choiceTextInput}
          type="text"
          placeholder="New choice text"
          value={newChoiceText}
          onChange={(event) => setNewChoiceText(event.target.value)}
        />
        <button type="submit">Add choice</button>
      </form>
    </div>
  )
}

export default QuestionEditor
