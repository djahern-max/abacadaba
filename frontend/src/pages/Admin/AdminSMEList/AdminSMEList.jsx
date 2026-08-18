import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { createAdminSME, getAdminSMEs } from '../../../api/admin'
import Button from '../../../components/Button/Button'
import SMEForm from './SMEForm'
import SMERow from './SMERow'
import styles from './AdminSMEList.module.css'

// Deliberately not tied to users - see current-feature.md, "Subject matter
// experts are not users". Plain list/create/edit, no cleverness.
function AdminSMEList() {
  const [state, setState] = useState({ status: 'loading', smes: [] })
  const [showCreate, setShowCreate] = useState(false)

  function refresh() {
    return getAdminSMEs()
      .then((smes) => setState({ status: 'loaded', smes }))
      .catch(() => setState({ status: 'error', smes: [] }))
  }

  useEffect(() => {
    refresh()
  }, [])

  return (
    <div className={styles.page}>
      <Link to="/admin" className={styles.back}>
        &larr; All courses
      </Link>
      <h1 className={styles.heading}>Admin: subject matter experts</h1>
      <p className={styles.intro}>
        The developers and reviewers named on a course. A person can have both a record here and a user
        account, but the two are unrelated - this is the record an audit reads.
      </p>

      {showCreate ? (
        <SMEForm
          submitLabel="Add subject matter expert"
          onCancel={() => setShowCreate(false)}
          onSubmit={async (values) => {
            await createAdminSME(values)
            setShowCreate(false)
            await refresh()
          }}
        />
      ) : (
        <Button variant="secondary" onClick={() => setShowCreate(true)}>
          Add subject matter expert
        </Button>
      )}

      {state.status === 'loading' && <p className={styles.muted}>Loading&hellip;</p>}
      {state.status === 'error' && (
        <p className={styles.muted}>Couldn&apos;t load subject matter experts. Please try again later.</p>
      )}
      {state.status === 'loaded' && state.smes.length === 0 && (
        <p className={styles.muted}>No one has been added yet.</p>
      )}
      {state.status === 'loaded' && state.smes.length > 0 && (
        <ul className={styles.list}>
          {state.smes.map((sme) => (
            <SMERow key={sme.id} sme={sme} onChange={refresh} />
          ))}
        </ul>
      )}
    </div>
  )
}

export default AdminSMEList
