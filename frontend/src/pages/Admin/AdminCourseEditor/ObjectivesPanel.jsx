import { useState } from 'react'
import { createAdminObjective } from '../../../api/admin'
import ObjectiveRow from './ObjectiveRow'
import styles from '../AdminLessonEditor/QuestionsEditor.module.css'

function ObjectivesPanel({ course, onChange }) {
  const [text, setText] = useState('')
  const [adding, setAdding] = useState(false)
  const [error, setError] = useState('')

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
          objective={objective}
          isFirst={index === 0}
          isLast={index === course.learning_objectives.length - 1}
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
}

export default ObjectivesPanel
