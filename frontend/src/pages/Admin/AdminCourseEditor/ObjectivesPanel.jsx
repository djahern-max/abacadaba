import { forwardRef, useCallback, useEffect, useImperativeHandle, useRef, useState } from 'react'
import { createAdminObjective } from '../../../api/admin'
import ObjectiveRow from './ObjectiveRow'
import styles from '../AdminLessonEditor/QuestionsEditor.module.css'

const ObjectivesPanel = forwardRef(function ObjectivesPanel({ course, onDirtyChange, onChange }, ref) {
  const [text, setText] = useState('')
  const [adding, setAdding] = useState(false)
  const [error, setError] = useState('')
  const [dirtyCounts, setDirtyCounts] = useState(() => new Map())
  const objectiveRefs = useRef(new Map())

  const totalDirty = [...dirtyCounts.values()].reduce((sum, count) => sum + count, 0)

  useEffect(() => {
    onDirtyChange?.(totalDirty)
  }, [totalDirty, onDirtyChange])

  const handleObjectiveDirtyChange = useCallback((objectiveId, count) => {
    setDirtyCounts((prev) => {
      const already = prev.get(objectiveId) ?? 0
      if (already === count) return prev
      const next = new Map(prev)
      if (count > 0) next.set(objectiveId, count)
      else next.delete(objectiveId)
      return next
    })
  }, [])

  useImperativeHandle(ref, () => ({
    save: async () => {
      const tasks = []
      for (const objectiveId of dirtyCounts.keys()) {
        const objectiveRef = objectiveRefs.current.get(objectiveId)
        if (objectiveRef) tasks.push(objectiveRef.save())
      }
      await Promise.all(tasks)
    },
  }))

  async function handleAdd(event) {
    event.preventDefault()
    if (!text.trim()) return
    setError('')
    setAdding(true)
    try {
      await createAdminObjective(course.id, text.trim())
      setText('')
      await onChange()
    } catch {
      setError('Could not add the learning objective.')
    } finally {
      setAdding(false)
    }
  }

  return (
    <section className={styles.section}>
      <h2 className={styles.heading}>Learning objectives ({course.learning_objectives.length})</h2>

      {course.learning_objectives.map((objective, index) => (
        <ObjectiveRow
          key={objective.id}
          ref={(el) => {
            if (el) objectiveRefs.current.set(objective.id, el)
            else objectiveRefs.current.delete(objective.id)
          }}
          objective={objective}
          isFirst={index === 0}
          isLast={index === course.learning_objectives.length - 1}
          onDirtyChange={handleObjectiveDirtyChange}
          onChange={onChange}
        />
      ))}

      <form className={styles.addForm} onSubmit={handleAdd}>
        <input
          className={styles.input}
          type="text"
          placeholder="New learning objective"
          value={text}
          onChange={(event) => setText(event.target.value)}
          disabled={adding}
        />
        <button type="submit" className={styles.button} disabled={adding || !text.trim()}>
          Add objective
        </button>
      </form>
      {error && <p className={styles.fieldError}>{error}</p>}
    </section>
  )
})

export default ObjectivesPanel
