import { forwardRef, useCallback, useEffect, useImperativeHandle, useRef, useState } from 'react'
import { createAdminQuestion } from '../../../api/admin'
import QuestionEditor from './QuestionEditor'
import styles from './QuestionsEditor.module.css'

const QuestionsEditor = forwardRef(function QuestionsEditor({ lesson, onDirtyChange, onChange }, ref) {
  const [prompt, setPrompt] = useState('')
  const [adding, setAdding] = useState(false)
  const [error, setError] = useState('')
  const [dirtyCounts, setDirtyCounts] = useState(() => new Map())
  const questionRefs = useRef(new Map())

  const totalDirty = [...dirtyCounts.values()].reduce((sum, count) => sum + count, 0)

  useEffect(() => {
    onDirtyChange?.(totalDirty)
  }, [totalDirty, onDirtyChange])

  const handleQuestionDirtyChange = useCallback((questionId, count) => {
    setDirtyCounts((prev) => {
      const already = prev.get(questionId) ?? 0
      if (already === count) return prev
      const next = new Map(prev)
      if (count > 0) next.set(questionId, count)
      else next.delete(questionId)
      return next
    })
  }, [])

  useImperativeHandle(ref, () => ({
    save: async () => {
      const tasks = []
      for (const questionId of dirtyCounts.keys()) {
        const questionRef = questionRefs.current.get(questionId)
        if (questionRef) tasks.push(questionRef.save())
      }
      await Promise.all(tasks)
    },
  }))

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

      <form className={styles.addQuestionForm} onSubmit={handleAdd}>
        <textarea
          className={styles.addQuestionTextarea}
          rows={2}
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

      {lesson.questions.map((question, index) => (
        <QuestionEditor
          key={question.id}
          ref={(el) => {
            if (el) questionRefs.current.set(question.id, el)
            else questionRefs.current.delete(question.id)
          }}
          question={question}
          isFirst={index === 0}
          isLast={index === lesson.questions.length - 1}
          onDirtyChange={handleQuestionDirtyChange}
          onChange={onChange}
        />
      ))}
    </section>
  )
})

export default QuestionsEditor
