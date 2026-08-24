import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
// Reuses Stats.module.css's table treatment directly, per current-feature.md:
// "Reuse that page's table treatment rather than designing a second one."
import styles from '../Stats/Stats.module.css'
import { getAdminCurrency } from '../../../api/admin'

function formatDate(isoString) {
  return new Date(isoString).toLocaleDateString()
}

function CourseLink({ courseId, title }) {
  return <Link to={`/admin/courses/${courseId}`}>{title}</Link>
}

function ReviewSection({ heading, rows, emptyMessage }) {
  return (
    <section className={styles.section}>
      <h2 className={styles.sectionHeading}>{heading}</h2>
      {rows.length === 0 ? (
        <p className={styles.message}>{emptyMessage}</p>
      ) : (
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Course</th>
              <th>Published</th>
              <th>Reviewed</th>
              <th>Cycle</th>
              <th>Due</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.course_id}>
                <td>
                  <CourseLink courseId={row.course_id} title={row.title} />
                </td>
                <td>{row.is_published ? 'Published' : 'Draft'}</td>
                <td>{formatDate(row.reviewed_at)}</td>
                <td>{row.review_cycle}</td>
                <td>
                  {formatDate(row.due_at)}
                  {row.days_overdue > 0 && ` (${row.days_overdue} day(s) overdue)`}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}

function PublishedButEditedSection({ rows }) {
  return (
    <section className={styles.section}>
      <h2 className={styles.sectionHeading}>Published but edited since review</h2>
      {rows.length === 0 ? (
        <p className={styles.message}>No published course has been edited since its last review.</p>
      ) : (
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Course</th>
              <th>Reviewed</th>
              <th>Content edited</th>
              <th>Days unreviewed</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.course_id} className={styles.flaggedRow}>
                <td>
                  <CourseLink courseId={row.course_id} title={row.title} />
                </td>
                <td>{formatDate(row.reviewed_at)}</td>
                <td>{formatDate(row.content_updated_at)}</td>
                <td>{row.days_since_edit}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}

function ExpirationSection({ rows }) {
  return (
    <section className={styles.section}>
      <h2 className={styles.sectionHeading}>Expired or expiring</h2>
      {rows.length === 0 ? (
        <p className={styles.message}>No course is expired or expiring within 60 days.</p>
      ) : (
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Course</th>
              <th>Published</th>
              <th>Expires</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.course_id} className={row.days_until_expiry < 0 ? styles.flaggedRow : undefined}>
                <td>
                  <CourseLink courseId={row.course_id} title={row.title} />
                </td>
                <td>{row.is_published ? 'Published' : 'Draft'}</td>
                <td>{formatDate(row.expires_on)}</td>
                <td>
                  {row.days_until_expiry < 0
                    ? `Expired ${Math.abs(row.days_until_expiry)} day(s) ago`
                    : `Expires in ${row.days_until_expiry} day(s)`}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}

function AdminCurrency() {
  const [state, setState] = useState({ status: 'loading', data: null })

  useEffect(() => {
    getAdminCurrency()
      .then((data) => setState({ status: 'loaded', data }))
      .catch(() => setState({ status: 'error', data: null }))
  }, [])

  if (state.status === 'loading') {
    return <p className={styles.message}>Loading&hellip;</p>
  }
  if (state.status === 'error') {
    return <p className={styles.message}>Couldn&apos;t load the currency dashboard.</p>
  }

  const { data } = state

  return (
    <div className={styles.page}>
      <Link to="/admin" className={styles.back}>
        &larr; All courses
      </Link>
      <h1 className={styles.heading}>Currency</h1>
      <p className={styles.message}>
        4.01 review cycles and 9.02.2 expiration dates, checked against the clock. A course can appear in more
        than one section below.
      </p>

      <ReviewSection
        heading="Overdue for review"
        rows={data.overdue_review}
        emptyMessage="No course is overdue for review."
      />
      <ReviewSection
        heading="Due for review soon (within 60 days)"
        rows={data.due_soon}
        emptyMessage="No course is due for review within 60 days."
      />
      <PublishedButEditedSection rows={data.published_but_edited} />
      <ExpirationSection rows={data.expired_or_expiring} />
    </div>
  )
}

export default AdminCurrency
