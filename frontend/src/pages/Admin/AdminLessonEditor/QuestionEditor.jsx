import { forwardRef, useCallback, useEffect, useImperativeHandle, useRef, useState } from 'react'
import { createAdminChoice, deleteAdminQuestion, moveAdminQuestion, updateAdminQuestion } from '../../../api/admin'
import Button from '../../../components/Button/Button'
import ChoiceRow from './ChoiceRow'
import styles from './QuestionEditor.module.css'

const QuestionEditor = forwardRef(function QuestionEditor(
  { question, isFirst, isLast, onDirtyChange, onChange },
  ref,
) {
  const [prompt, setPrompt] = useState(question.prompt)
  const [newChoiceText, setNewChoiceText] = useState('')
  const [dirtyChoiceCounts, setDirtyChoiceCounts] = useState(() => new Map())
  const choiceRefs = useRef(new Map())
  const promptRef = useRef(null)

  const promptDirty = prompt !== question.prompt
  const choicesDirtyTotal = [...dirtyChoiceCounts.values()].reduce((sum, count) => sum + count, 0)
  const ownDirtyCount = (promptDirty ? 1 : 0) + choicesDirtyTotal

  useEffect(() => {
    onDirtyChange?.(question.id, ownDirtyCount)
    return () => onDirtyChange?.(question.id, 0)
  }, [question.id, ownDirtyCount, onDirtyChange])

  const handleChoiceDirtyChange = useCallback((choiceId, count) => {
    setDirtyChoiceCounts((prev) => {
      const already = prev.get(choiceId) ?? 0
      if (already === count) return prev
      const next = new Map(prev)
      if (count > 0) next.set(choiceId, count)
      else next.delete(choiceId)
      return next
    })
  }, [])

  useImperativeHandle(ref, () => ({
    save: async () => {
      const tasks = []
      if (promptDirty) tasks.push(updateAdminQuestion(question.id, prompt))
      for (const choiceId of dirtyChoiceCounts.keys()) {
        const choiceRef = choiceRefs.current.get(choiceId)
        if (choiceRef) tasks.push(choiceRef.save())
      }
      await Promise.all(tasks)
    },
    focusPrompt: () => {
      promptRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
      promptRef.current?.focus()
    },
  }))

  async function handleMove(direction) {
    await moveAdminQuestion(question.id, direction)
    await onChange()
  }

  async function handleDeleteQuestion() {
    await deleteAdminQuestion(question.id)
    await onChange()
  }

  async function handleAddChoice(event) {
    event.preventDefault()
    if (!newChoiceText.trim()) return
    await createAdminChoice(question.id, newChoiceText.trim())
    setNewChoiceText('')
    await onChange()
  }

  return (
    <div className={styles.question}>
      <div className={styles.promptRow}>
        <span className={styles.position}>{question.position}.</span>
        <textarea
          ref={promptRef}
          className={`${styles.promptInput} ${promptDirty ? styles.fieldDirty : ''}`}
          rows={2}
          value={prompt}
          onChange={(event) => setPrompt(event.target.value)}
        />
      </div>
      <div className={styles.questionActions}>
        <Button variant="secondary" onClick={() => handleMove('up')} disabled={isFirst}>
          Move up
        </Button>
        <Button variant="secondary" onClick={() => handleMove('down')} disabled={isLast}>
          Move down
        </Button>
        <Button variant="danger" onClick={handleDeleteQuestion}>
          Delete question
        </Button>
      </div>

      <div className={styles.choicesBlock}>
        <ul className={styles.choices}>
          {question.choices.map((choice) => (
            <ChoiceRow
              key={choice.id}
              ref={(el) => {
                if (el) choiceRefs.current.set(choice.id, el)
                else choiceRefs.current.delete(choice.id)
              }}
              choice={choice}
              questionId={question.id}
              onDirtyChange={handleChoiceDirtyChange}
              onChange={onChange}
            />
          ))}
        </ul>

        <form className={styles.addChoiceForm} onSubmit={handleAddChoice}>
          <input
            className={styles.choiceTextInput}
            type="text"
            placeholder="New choice text"
            value={newChoiceText}
            onChange={(event) => setNewChoiceText(event.target.value)}
          />
          <Button type="submit" variant="secondary">
            Add choice
          </Button>
        </form>
      </div>
    </div>
  )
})

export default QuestionEditor
