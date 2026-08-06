import { useState } from 'react'
import { createAdminQuestion } from '../../../api/admin'
import QuestionEditor from './QuestionEditor'
import styles from './QuestionsEditor.module.css'

function QuestionsEditor({ lesson, onChange }) {
  const [prompt, setPrompt] = useState('')
  const [adding, setAdding] = useState(false)
  const [error, setError] = useState('')

  async function handleAdd(event) {
    event.preventDefault()
    if (!prompt.trim()) return
    setError('')
    setAdding(true)
    try {
      await createAdminQuestion(lesson.id, prompt.trim())
      setPrompt('')
      await onChange()
    } catch {
      setError('Could not add the question.')
    } finally {
      setAdding(false)
    }
  }

  return (
    <section className={styles.section}>
      <h2 className={styles.heading}>Questions ({lesson.questions.length})</h2>

      {lesson.questions.map((question, index) => (
        <QuestionEditor
          key={question.id}
          question={question}
          isFirst={index === 0}
          isLast={index === lesson.questions.length - 1}
          onChange={onChange}
        />
      ))}

      <form className={styles.addForm} onSubmit={handleAdd}>
        <input
          className={styles.input}
          type="text"
          placeholder="New question prompt"
          value={prompt}
          onChange={(event) => setPrompt(event.target.value)}
          disabled={adding}
        />
        <button type="submit" className={styles.button} disabled={adding || !prompt.trim()}>
          Add question
        </button>
      </form>
      {error && <p className={styles.fieldError}>{error}</p>}
    </section>
  )
}

export default QuestionsEditor
