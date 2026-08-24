import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getPolicies } from '../../../api/policies'
import { updateAdminPolicy } from '../../../api/admin'
import Button from '../../../components/Button/Button'
import styles from '../AdminSponsorSettings/AdminSponsorSettings.module.css'
import localStyles from './AdminPolicies.module.css'

// Reuses AdminSponsorSettings.module.css directly - both pages are the same
// shape: one or more site-wide records edited on one plain form, no rich
// text editor, immediate feedback rather than a batched save bar.
function AdminPolicies() {
  const [state, setState] = useState({ status: 'loading', policies: [] })
  const [bodies, setBodies] = useState({})
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState(false)

  function refresh() {
    return getPolicies()
      .then((policies) => {
        setState({ status: 'loaded', policies })
        setBodies(Object.fromEntries(policies.map((policy) => [policy.slug, policy.body])))
      })
      .catch(() => setState({ status: 'error', policies: [] }))
  }

  useEffect(() => {
    refresh()
  }, [])

  function setBody(slug, value) {
    setSaved(false)
    setBodies((prev) => ({ ...prev, [slug]: value }))
  }

  const dirtyPolicies = state.policies.filter((policy) => bodies[policy.slug] !== policy.body)

  async function handleSave(event) {
    event.preventDefault()
    setError('')
    setSaving(true)
    try {
      await Promise.all(dirtyPolicies.map((policy) => updateAdminPolicy(policy.slug, { body: bodies[policy.slug] })))
      await refresh()
      setSaved(true)
    } catch {
      setError('Could not save these policies.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className={styles.page}>
      <Link to="/admin" className={styles.back}>
        &larr; All courses
      </Link>
      <h1 className={styles.heading}>Admin: policies</h1>
      <p className={styles.intro}>
        8.01.1 and 9.02: these four documents must be formalized, published, and made available to
        participants before any course can publish. Markdown - headings, lists, bold/italic, links.
      </p>

      {state.status === 'loading' && <p className={styles.message}>Loading&hellip;</p>}
      {state.status === 'error' && <p className={styles.message}>Couldn&apos;t load policies. Please try again later.</p>}

      {state.status === 'loaded' && (
        <form className={localStyles.form} onSubmit={handleSave}>
          {state.policies.map((policy) => (
            <div key={policy.slug} className={styles.field}>
              <label className={styles.label} htmlFor={`policy-${policy.slug}`}>
                {policy.title}
                {policy.is_placeholder && ' — not yet written'}
              </label>
              <textarea
                id={`policy-${policy.slug}`}
                className={styles.textarea}
                rows={8}
                value={bodies[policy.slug] ?? ''}
                onChange={(event) => setBody(policy.slug, event.target.value)}
              />
            </div>
          ))}

          <div className={styles.formActions}>
            <Button type="submit" variant="primary" disabled={saving || dirtyPolicies.length === 0}>
              {saving ? 'Saving…' : 'Save'}
            </Button>
            {saved && <span className={styles.savedMessage}>Saved.</span>}
          </div>
          {error && <p className={styles.fieldError}>{error}</p>}
        </form>
      )}
    </div>
  )
}

export default AdminPolicies
