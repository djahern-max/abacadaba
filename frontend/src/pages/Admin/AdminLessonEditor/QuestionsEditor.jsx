import { forwardRef, useCallback, useEffect, useImperativeHandle, useRef, useState } from 'react'
import { createAdminQuestion } from '../../../api/admin'
import Button from '../../../components/Button/Button'
import QuestionEditor from './QuestionEditor'
import styles from './QuestionsEditor.module.css'

const QuestionsEditor = forwardRef(function QuestionsEditor({ lesson, objectives, onDirtyChange, onChange }, ref) {
  const [prompt, setPrompt] = useState('')
  const [adding, setAdding] = useState(false)
  const [error, setError] = useState('')
  const [dirtyCounts, setDirtyCounts] = useState(() => new Map())
  const questionRefs = useRef(new Map())
  const pendingFocusIdRef = useRef(null)

  const totalDirty = [...dirtyCounts.values()].reduce((sum, count) => sum + count, 0)

  useEffect(() => {
    onDirtyChange?.(totalDirty)
  }, [totalDirty, onDirtyChange])

  useEffect(() => {
    const pendingId = pendingFocusIdRef.current
    if (pendingId == null) return
    const questionRef = questionRefs.current.get(pendingId)
    if (!questionRef) return
    questionRef.focusPrompt()
    pendingFocusIdRef.current = null
  }, [lesson.questions])

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
      const created = await createAdminQuestion(lesson.id, prompt.trim())
      pendingFocusIdRef.current = created.id
      setPrompt('')
      await onChange()
    } catch {
      setError('Could not add the question.')
    } finally {
      setAdding(false)
    }
  }

  // Grouped by type rather than interleaved - an author needs to see the
  // two sets (review questions reinforce learning; assessment questions
  // gate credit) as two sets, not mixed by authored position.
  const reviewQuestions = lesson.questions.filter((question) => question.kind === 'review')
  const assessmentQuestions = lesson.questions.filter((question) => question.kind === 'assessment')

  function renderGroup(questions) {
    return questions.map((question, index) => (
      <QuestionEditor
        key={question.id}
        ref={(el) => {
          if (el) questionRefs.current.set(question.id, el)
          else questionRefs.current.delete(question.id)
        }}
        question={question}
        isFirst={index === 0}
        isLast={index === questions.length - 1}
        objectives={objectives}
        onDirtyChange={handleQuestionDirtyChange}
        onChange={onChange}
      />
    ))
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
        <Button type="submit" variant="secondary" disabled={adding || !prompt.trim()}>
          Add question
        </Button>
      </form>
      {error && <p className={styles.fieldError}>{error}</p>}

      <div className={styles.group}>
        <h3 className={styles.groupHeading}>Review questions ({reviewQuestions.length})</h3>
        <p className={styles.groupHint}>
          Reinforce learning during the program, at the end of this segment. No minimum passing rate.
        </p>
        {renderGroup(reviewQuestions)}
      </div>

      <div className={styles.group}>
        <h3 className={styles.groupHeading}>Assessment questions ({assessmentQuestions.length})</h3>
        <p className={styles.groupHint}>
          Served on the qualified assessment at the end of the course. Gate credit; no feedback until the
          course is complete.
        </p>
        {renderGroup(assessmentQuestions)}
      </div>
    </section>
  )
})

export default QuestionsEditor
