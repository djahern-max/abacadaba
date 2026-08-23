import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getAdminSponsor, updateAdminSponsor } from '../../../api/admin'
import Button from '../../../components/Button/Button'
import styles from './AdminSponsorSettings.module.css'

const FIELDS = [
  { name: 'name', label: 'Sponsor name', type: 'input' },
  { name: 'national_registry_id', label: 'NASBA sponsor registry ID', type: 'input' },
  {
    name: 'state_registry_ids',
    label: 'State registry ID(s)',
    type: 'input',
    hint: 'Free form - only if this sponsor is separately registered with individual state boards.',
  },
  { name: 'website', label: 'Website', type: 'input' },
  { name: 'contact_email', label: 'Contact email', type: 'input' },
  { name: 'address', label: 'Address', type: 'textarea' },
]

// The sponsor identity record printed on every certificate (9.01 items 1,
// 8, 9) - a singleton, so there's nothing to list or create, only edit.
function AdminSponsorSettings() {
  const [state, setState] = useState({ status: 'loading', profile: null })
  const [values, setValues] = useState(null)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [saved, setSaved] = useState(false)

  function refresh() {
    return getAdminSponsor()
      .then((profile) => {
        setState({ status: 'loaded', profile })
        setValues(profile)
      })
      .catch(() => setState({ status: 'error', profile: null }))
  }

  useEffect(() => {
    refresh()
  }, [])

  function set(field, value) {
    setSaved(false)
    setValues((prev) => ({ ...prev, [field]: value }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setSaving(true)
    try {
      const profile = await updateAdminSponsor({
        name: values.name,
        national_registry_id: values.national_registry_id,
        state_registry_ids: values.state_registry_ids || null,
        website: values.website,
        contact_email: values.contact_email,
        address: values.address,
      })
      setState({ status: 'loaded', profile })
      setValues(profile)
      setSaved(true)
    } catch {
      setError('Could not save the sponsor profile.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className={styles.page}>
      <Link to="/admin" className={styles.back}>
        &larr; All courses
      </Link>
      <h1 className={styles.heading}>Admin: sponsor settings</h1>
      <p className={styles.intro}>
        The CPE program sponsor identity printed on every certificate. There is exactly one of these records.
      </p>

      {state.status === 'loading' && <p className={styles.message}>Loading&hellip;</p>}
      {state.status === 'error' && (
        <p className={styles.message}>Couldn&apos;t load the sponsor profile. Please try again later.</p>
      )}

      {state.status === 'loaded' && (
        <>
          {state.profile.missing_fields.length > 0 && (
            <p className={styles.warning}>
              Incomplete - courses can&apos;t be published until this record has:{' '}
              {state.profile.missing_fields.join(', ')}.
            </p>
          )}

          <form className={styles.form} onSubmit={handleSubmit}>
            {FIELDS.map((field) => (
              <div key={field.name} className={styles.field}>
                <label className={styles.label} htmlFor={`sponsor-${field.name}`}>
                  {field.label}
                </label>
                {field.type === 'textarea' ? (
                  <textarea
                    id={`sponsor-${field.name}`}
                    className={styles.textarea}
                    rows={3}
                    value={values[field.name] ?? ''}
                    onChange={(event) => set(field.name, event.target.value)}
                  />
                ) : (
                  <input
                    id={`sponsor-${field.name}`}
                    className={styles.input}
                    type="text"
                    value={values[field.name] ?? ''}
                    onChange={(event) => set(field.name, event.target.value)}
                  />
                )}
                {field.hint && <p className={styles.hint}>{field.hint}</p>}
              </div>
            ))}

            <div className={styles.formActions}>
              <Button type="submit" variant="primary" disabled={saving}>
                {saving ? 'Saving…' : 'Save'}
              </Button>
              {saved && <span className={styles.savedMessage}>Saved.</span>}
            </div>
            {error && <p className={styles.fieldError}>{error}</p>}
          </form>
        </>
      )}
    </div>
  )
}

export default AdminSponsorSettings
