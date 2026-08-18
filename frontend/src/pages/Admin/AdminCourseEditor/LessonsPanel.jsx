import { useState } from 'react'
import { Link } from 'react-router-dom'
import { createAdminLesson, moveAdminLesson } from '../../../api/admin'
import Button from '../../../components/Button/Button'
import styles from './LessonsPanel.module.css'

function LessonsPanel({ course, onChange }) {
  const [title, setTitle] = useState('')
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState('')

  async function handleAdd(event) {
    event.preventDefault()
    if (!title.trim()) return
    setError('')
    setCreating(true)
    try {
      await createAdminLesson(course.id, { title: title.trim() })
      setTitle('')
      await onChange()
    } catch {
      setError('Could not add the lesson.')
    } finally {
      setCreating(false)
    }
  }

  async function handleMove(lessonId, direction) {
    await moveAdminLesson(lessonId, direction)
    await onChange()
  }

  return (
    <section className={styles.section}>
      <h2 className={styles.heading}>Lessons ({course.lessons.length})</h2>

      {course.lessons.length === 0 && (
        <p className={styles.emptyState}>
          A lesson is one video segment plus its questions. A course is one or more lessons, taken in order.
          Add the first one below.
        </p>
      )}

      <ol className={styles.list}>
        {course.lessons.map((lesson, index) => (
          <li key={lesson.id} className={styles.row}>
            <div className={styles.rowMain}>
              <Link to={`/admin/lessons/${lesson.id}`}>
                {lesson.position}. {lesson.title}
              </Link>
              <span className={`${styles.badge} ${lesson.is_published ? styles.published : styles.draft}`}>
                {lesson.is_published ? 'Published' : 'Draft'}
              </span>
            </div>
            <div className={styles.rowMeta}>
              <span>{lesson.questions.length} question(s)</span>
              <span>{lesson.video_key ? 'Has video' : 'No video'}</span>
              <div className={styles.moveButtons}>
                <Button
                  variant="secondary"
                  onClick={() => handleMove(lesson.id, 'up')}
                  disabled={index === 0}
                  aria-label="Move lesson up"
                >
                  &uarr;
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => handleMove(lesson.id, 'down')}
                  disabled={index === course.lessons.length - 1}
                  aria-label="Move lesson down"
                >
                  &darr;
                </Button>
              </div>
            </div>
          </li>
        ))}
      </ol>

      <form className={styles.addForm} onSubmit={handleAdd}>
        <input
          className={styles.input}
          type="text"
          placeholder="New lesson title"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          disabled={creating}
        />
        <Button type="submit" variant="secondary" disabled={creating || !title.trim()}>
          {creating ? 'Adding…' : 'Add lesson'}
        </Button>
      </form>
      {error && <p className={styles.fieldError}>{error}</p>}
    </section>
  )
}

export default LessonsPanel
