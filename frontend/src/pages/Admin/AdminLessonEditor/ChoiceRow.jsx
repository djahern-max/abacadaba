import { forwardRef, useEffect, useImperativeHandle, useState } from 'react'
import { deleteAdminChoice, moveAdminChoice, setCorrectChoice, updateAdminChoice } from '../../../api/admin'
import styles from './ChoiceRow.module.css'

const ChoiceRow = forwardRef(function ChoiceRow({ choice, questionId, onDirtyChange, onChange }, ref) {
  const [text, setText] = useState(choice.text)

  const dirty = text !== choice.text

  useEffect(() => {
    onDirtyChange?.(choice.id, dirty ? 1 : 0)
    return () => onDirtyChange?.(choice.id, 0)
  }, [choice.id, dirty, onDirtyChange])

  useImperativeHandle(ref, () => ({
    save: () => updateAdminChoice(choice.id, text),
  }))

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
})

export default ChoiceRow
