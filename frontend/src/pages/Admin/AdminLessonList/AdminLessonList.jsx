import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { createAdminLesson, getAdminLessons } from '../../../api/admin'
import styles from './AdminLessonList.module.css'

function AdminLessonList() {
  const navigate = useNavigate()
  const [state, setState] = useState({ status: 'loading', lessons: [] })
  const [title, setTitle] = useState('')
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    getAdminLessons()
      .then((lessons) => setState({ status: 'loaded', lessons }))
      .catch(() => setState({ status: 'error', lessons: [] }))
  }, [])

  async function handleCreate(event) {
    event.preventDefault()
    if (!title.trim()) return
    setError('')
    setCreating(true)
    try {
      const lesson = await createAdminLesson({ title: title.trim() })
      navigate(`/admin/lessons/${lesson.id}`)
    } catch {
      setError('Could not create the lesson. Try a different title.')
      setCreating(false)
    }
  }

  return (
    <div className={styles.page}>
      <h1 className={styles.heading}>Admin: lessons</h1>

      <form className={styles.createForm} onSubmit={handleCreate}>
        <input
          className={styles.input}
          type="text"
          placeholder="New lesson title"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          disabled={creating}
        />
        <button type="submit" className={styles.button} disabled={creating || !title.trim()}>
          {creating ? 'Creating…' : 'Create lesson'}
        </button>
      </form>
      {error && <p className={styles.fieldError}>{error}</p>}

      {state.status === 'loading' && <p className={styles.message}>Loading&hellip;</p>}
      {state.status === 'error' && (
        <p className={styles.message}>Couldn&apos;t load lessons. Please try again later.</p>
      )}

      {state.status === 'loaded' && (
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Title</th>
              <th>Status</th>
              <th>Questions</th>
              <th>Video</th>
              <th>Stats</th>
            </tr>
          </thead>
          <tbody>
            {state.lessons.map((lesson) => (
              <tr key={lesson.id}>
                <td>
                  <Link to={`/admin/lessons/${lesson.id}`}>{lesson.title}</Link>
                </td>
                <td>
                  <span
                    className={`${styles.badge} ${lesson.is_published ? styles.published : styles.draft}`}
                  >
                    {lesson.is_published ? 'Published' : 'Draft'}
                  </span>
                </td>
                <td>{lesson.question_count}</td>
                <td>{lesson.has_video ? 'Yes' : 'No'}</td>
                <td>
                  <Link to={`/admin/lessons/${lesson.id}/stats`}>View stats</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

export default AdminLessonList
