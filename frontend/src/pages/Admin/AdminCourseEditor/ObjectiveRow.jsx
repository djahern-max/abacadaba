import { forwardRef, useEffect, useImperativeHandle, useState } from 'react'
import { deleteAdminObjective, moveAdminObjective, updateAdminObjective } from '../../../api/admin'
import Button from '../../../components/Button/Button'
import styles from '../AdminLessonEditor/QuestionEditor.module.css'

const ObjectiveRow = forwardRef(function ObjectiveRow({ objective, isFirst, isLast, onDirtyChange, onChange }, ref) {
  const [text, setText] = useState(objective.text)

  const dirty = text !== objective.text

  useEffect(() => {
    onDirtyChange?.(objective.id, dirty ? 1 : 0)
    return () => onDirtyChange?.(objective.id, 0)
  }, [objective.id, dirty, onDirtyChange])

  useImperativeHandle(ref, () => ({
    save: () => updateAdminObjective(objective.id, text),
  }))

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
          className={`${styles.promptInput} ${dirty ? styles.fieldDirty : ''}`}
          rows={2}
          value={text}
          onChange={(event) => setText(event.target.value)}
        />
      </div>
      <div className={styles.questionActions}>
        <Button variant="secondary" onClick={() => handleMove('up')} disabled={isFirst}>
          Move up
        </Button>
        <Button variant="secondary" onClick={() => handleMove('down')} disabled={isLast}>
          Move down
        </Button>
        <Button variant="danger" onClick={handleDelete}>
          Delete objective
        </Button>
      </div>
    </div>
  )
})

export default ObjectiveRow
