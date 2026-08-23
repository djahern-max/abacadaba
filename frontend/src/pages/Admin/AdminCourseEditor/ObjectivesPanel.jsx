import { forwardRef, useCallback, useEffect, useImperativeHandle, useRef, useState } from 'react'
import { createAdminObjective } from '../../../api/admin'
import Button from '../../../components/Button/Button'
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

  // How many assessment questions test each objective - 6.01.2's 75%
  // coverage rule made checkable per-objective, right where an author is
  // already looking, rather than only surfaced later in the publish
  // checklist (021's stale-review lesson applied again).
  const assessmentQuestions = course.lessons.flatMap((lesson) =>
    lesson.questions.filter((question) => question.kind === 'assessment'),
  )
  const coverageCounts = new Map()
  for (const question of assessmentQuestions) {
    if (question.objective_id == null) continue
    coverageCounts.set(question.objective_id, (coverageCounts.get(question.objective_id) ?? 0) + 1)
  }

  return (
    <section className={styles.section}>
      <h2 className={styles.heading}>Learning objectives ({course.learning_objectives.length})</h2>

      {course.learning_objectives.map((objective, index) => (
        <div key={objective.id}>
          <ObjectiveRow
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
          <p className={(coverageCounts.get(objective.id) ?? 0) === 0 ? styles.fieldError : styles.groupHint}>
            {coverageCounts.get(objective.id) ?? 0} assessment question
            {coverageCounts.get(objective.id) === 1 ? '' : 's'} test this objective
            {(coverageCounts.get(objective.id) ?? 0) === 0 ? ' - not yet covered' : ''}
          </p>
        </div>
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
        <Button type="submit" variant="secondary" disabled={adding || !text.trim()}>
          Add objective
        </Button>
      </form>
      {error && <p className={styles.fieldError}>{error}</p>}
    </section>
  )
})

export default ObjectivesPanel
