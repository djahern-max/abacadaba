import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { createAdminCourse, getAdminCourses } from '../../../api/admin'
import Button from '../../../components/Button/Button'
import styles from './AdminCourseList.module.css'

function AdminCourseList() {
  const navigate = useNavigate()
  const [state, setState] = useState({ status: 'loading', courses: [] })
  const [title, setTitle] = useState('')
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    getAdminCourses()
      .then((courses) => setState({ status: 'loaded', courses }))
      .catch(() => setState({ status: 'error', courses: [] }))
  }, [])

  async function handleCreate(event) {
    event.preventDefault()
    if (!title.trim()) return
    setError('')
    setCreating(true)
    try {
      const course = await createAdminCourse({ title: title.trim() })
      navigate(`/admin/courses/${course.id}`)
    } catch {
      setError('Could not create the course. Try a different title.')
      setCreating(false)
    }
  }

  return (
    <div className={styles.page}>
      <div className={styles.headerRow}>
        <h1 className={styles.heading}>Admin: courses</h1>
        <nav className={styles.nav}>
          <Link to="/admin/smes" className={styles.smeLink}>
            Subject matter experts
          </Link>
          <Link to="/admin/sponsor" className={styles.smeLink}>
            Sponsor settings
          </Link>
          <Link to="/admin/policies" className={styles.smeLink}>
            Policies
          </Link>
          <Link to="/admin/currency" className={styles.smeLink}>
            Currency
          </Link>
          <Link to="/admin/completions" className={styles.smeLink}>
            Completions
          </Link>
        </nav>
      </div>

      <form className={styles.createForm} onSubmit={handleCreate}>
        <input
          className={styles.input}
          type="text"
          placeholder="New course title"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
          disabled={creating}
        />
        <Button type="submit" variant="secondary" disabled={creating || !title.trim()}>
          {creating ? 'Creating…' : 'Create course'}
        </Button>
      </form>
      {error && <p className={styles.fieldError}>{error}</p>}

      {state.status === 'loading' && <p className={styles.message}>Loading&hellip;</p>}
      {state.status === 'error' && (
        <p className={styles.message}>Couldn&apos;t load courses. Please try again later.</p>
      )}

      {state.status === 'loaded' && (
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Title</th>
              <th>Status</th>
              <th>Lessons</th>
              <th>Stats</th>
              <th>Evaluations</th>
            </tr>
          </thead>
          <tbody>
            {state.courses.map((course) => (
              <tr key={course.id}>
                <td>
                  <Link to={`/admin/courses/${course.id}`}>{course.title}</Link>
                </td>
                <td>
                  <span
                    className={`${styles.badge} ${course.is_published ? styles.published : styles.draft}`}
                  >
                    {course.is_published ? 'Published' : 'Draft'}
                  </span>
                </td>
                <td>{course.lesson_count}</td>
                <td>
                  <Link to={`/admin/courses/${course.id}/stats`}>View stats</Link>
                </td>
                <td>
                  <Link to={`/admin/courses/${course.id}/evaluations`}>View evaluations</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

export default AdminCourseList
