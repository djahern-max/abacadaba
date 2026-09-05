import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { adminCompletionsCsvUrl, getAdminCompletions, getAdminCourses } from '../../../api/admin'
import styles from './AdminCompletions.module.css'

const EMPTY_FILTERS = { courseId: '', startDate: '', endDate: '', passed: '' }

function formatDate(isoString) {
  return new Date(isoString).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

// Plain table, no charts - feature 012 settled that argument. This is the
// audit artifact's screen: every completed attempt, filterable, exportable.
function AdminCompletions() {
  const [courses, setCourses] = useState([])
  const [filters, setFilters] = useState(EMPTY_FILTERS)
  const [state, setState] = useState({ status: 'loading', rows: [] })

  useEffect(() => {
    getAdminCourses().then(setCourses).catch(() => setCourses([]))
  }, [])

  useEffect(() => {
    setState({ status: 'loading', rows: [] })
    getAdminCompletions(filters)
      .then((rows) => setState({ status: 'loaded', rows }))
      .catch(() => setState({ status: 'error', rows: [] }))
  }, [filters])

  function setFilter(field, value) {
    setFilters((prev) => ({ ...prev, [field]: value }))
  }

  return (
    <div className={styles.page}>
      <Link to="/admin" className={styles.back}>
        &larr; All courses
      </Link>
      <h1 className={styles.heading}>Admin: completions</h1>
      <p className={styles.intro}>Every completed attempt, pass or fail - the record a sponsor produces on audit.</p>

      <div className={styles.filters}>
        <select
          className={styles.courseSelect}
          value={filters.courseId}
          onChange={(event) => setFilter('courseId', event.target.value)}
        >
          <option value="">All courses</option>
          {courses.map((course) => (
            <option key={course.id} value={course.id}>
              {course.title}
            </option>
          ))}
        </select>

        <select
          className={styles.select}
          value={filters.passed}
          onChange={(event) => setFilter('passed', event.target.value)}
        >
          <option value="">Passed or failed</option>
          <option value="true">Passed only</option>
          <option value="false">Failed only</option>
        </select>

        <label className={styles.dateLabel}>
          From
          <input
            type="date"
            className={styles.dateInput}
            value={filters.startDate}
            onChange={(event) => setFilter('startDate', event.target.value)}
          />
        </label>
        <label className={styles.dateLabel}>
          To
          <input
            type="date"
            className={styles.dateInput}
            value={filters.endDate}
            onChange={(event) => setFilter('endDate', event.target.value)}
          />
        </label>

        <a className={styles.downloadButton} href={adminCompletionsCsvUrl(filters)}>
          Download CSV
        </a>
      </div>

      {state.status === 'loading' && <p className={styles.message}>Loading&hellip;</p>}
      {state.status === 'error' && (
        <p className={styles.message}>Couldn&apos;t load completions. Please try again later.</p>
      )}
      {state.status === 'loaded' && state.rows.length === 0 && (
        <p className={styles.message}>No completions match these filters.</p>
      )}

      {state.status === 'loaded' && state.rows.length > 0 && (
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Course</th>
              <th>Participant</th>
              <th>Email</th>
              <th>Credit</th>
              <th>Completed</th>
              <th>Result</th>
              <th>Certificate code</th>
            </tr>
          </thead>
          <tbody>
            {state.rows.map((row) => (
              <tr key={row.attempt_id}>
                <td>{row.course_title}</td>
                <td>{row.participant_name || '—'}</td>
                <td>{row.participant_email || '—'}</td>
                <td>{row.credit_award ?? '—'}</td>
                <td>{formatDate(row.completed_at)}</td>
                <td>
                  <span className={row.passed ? styles.passed : styles.failed}>
                    {row.passed ? 'Passed' : 'Failed'}
                  </span>
                </td>
                <td>{row.certificate_code || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

export default AdminCompletions
