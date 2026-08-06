import { useState } from 'react'
import { deleteAdminChoice, moveAdminChoice, setCorrectChoice, updateAdminChoice } from '../../../api/admin'
import styles from './ChoiceRow.module.css'

function ChoiceRow({ choice, questionId, onChange }) {
  const [text, setText] = useState(choice.text)

  async function handleSave() {
    await updateAdminChoice(choice.id, text)
    await onChange()
  }

  async function handleCorrect() {
    await setCorrectChoice(questionId, choice.id)
    await onChange()
  }

  async function handleDelete() {
    await deleteAdminChoice(choice.id)
    await onChange()
  }

  async function handleMove(direction) {
    await moveAdminChoice(choice.id, direction)
    await onChange()
  }

  return (
    <li className={styles.row}>
      <input
        type="radio"
        name={`correct-${questionId}`}
        checked={choice.is_correct}
        onChange={handleCorrect}
        aria-label="Correct choice"
      />
      <input
        className={styles.textInput}
        type="text"
        value={text}
        onChange={(event) => setText(event.target.value)}
      />
      <button type="button" onClick={handleSave} disabled={text === choice.text}>
        Save
      </button>
      <button type="button" onClick={() => handleMove('up')}>
        Up
      </button>
      <button type="button" onClick={() => handleMove('down')}>
        Down
      </button>
      <button type="button" className={styles.dangerButton} onClick={handleDelete}>
        Delete
      </button>
    </li>
  )
}

export default ChoiceRow
