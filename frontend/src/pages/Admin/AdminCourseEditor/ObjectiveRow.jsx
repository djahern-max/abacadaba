import { useState } from 'react'
import { deleteAdminObjective, moveAdminObjective, updateAdminObjective } from '../../../api/admin'
import styles from '../AdminLessonEditor/QuestionEditor.module.css'

function ObjectiveRow({ objective, isFirst, isLast, onChange }) {
  const [text, setText] = useState(objective.text)
  const [error, setError] = useState('')

  async function handleSave() {
    setError('')
    try {
      await updateAdminObjective(objective.id, text)
      await onChange()
    } catch {
      setError('Could not save this objective.')
    }
  }

  async function handleMove(direction) {
    await moveAdminObjective(objective.id, direction)
    await onChange()
  }

  async function handleDelete() {
    await deleteAdminObjective(objective.id)
    await onChange()
  }

  return (
    <div className={styles.question}>
      <div className={styles.promptRow}>
        <span className={styles.position}>{objective.position}.</span>
        <textarea
          className={styles.promptInput}
          rows={2}
          value={text}
          onChange={(event) => setText(event.target.value)}
        />
      </div>
      <div className={styles.questionActions}>
        <button type="button" onClick={() => handleMove('up')} disabled={isFirst}>
          Move up
        </button>
        <button type="button" onClick={() => handleMove('down')} disabled={isLast}>
          Move down
        </button>
        <button type="button" onClick={handleSave} disabled={text === objective.text}>
          Save
        </button>
        <button type="button" className={styles.dangerButton} onClick={handleDelete}>
          Delete objective
        </button>
      </div>
      {error && <p className={styles.fieldError}>{error}</p>}
    </div>
  )
}

export default ObjectiveRow
