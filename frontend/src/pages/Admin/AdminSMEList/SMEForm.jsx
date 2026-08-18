import { useState } from 'react'
import Button from '../../../components/Button/Button'
import styles from './AdminSMEList.module.css'

const EMPTY = {
  name: '',
  credentials: '',
  affiliation: '',
  bio: '',
  license_jurisdiction: '',
  is_licensed_cpa: false,
  is_tax_attorney: false,
  is_enrolled_agent: false,
}

// Shared by the create form and each row's inline edit, so the eight SME
// fields are declared once.
function SMEForm({ initialValues, onSubmit, onCancel, submitLabel }) {
  const [values, setValues] = useState({ ...EMPTY, ...initialValues })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  function set(field, value) {
    setValues((prev) => ({ ...prev, [field]: value }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    if (!values.name.trim() || !values.credentials.trim()) return
    setError('')
    setSaving(true)
    try {
      await onSubmit({
        ...values,
        affiliation: values.affiliation.trim() || null,
        bio: values.bio.trim() || null,
        license_jurisdiction: values.license_jurisdiction.trim() || null,
      })
    } catch {
      setError('Could not save this person.')
      setSaving(false)
    }
  }

  return (
    <form className={styles.form} onSubmit={handleSubmit}>
      <label className={styles.label} htmlFor="sme-name">
        Name
      </label>
      <input
        id="sme-name"
        className={styles.input}
        value={values.name}
        onChange={(event) => set('name', event.target.value)}
      />

      <label className={styles.label} htmlFor="sme-credentials">
        Credentials
      </label>
      <input
        id="sme-credentials"
        className={styles.input}
        placeholder='e.g. "CPA, active, NH #12345"'
        value={values.credentials}
        onChange={(event) => set('credentials', event.target.value)}
      />

      <label className={styles.label} htmlFor="sme-affiliation">
        Affiliation
      </label>
      <input
        id="sme-affiliation"
        className={styles.input}
        value={values.affiliation ?? ''}
        onChange={(event) => set('affiliation', event.target.value)}
      />

      <label className={styles.label} htmlFor="sme-jurisdiction">
        License jurisdiction
      </label>
      <input
        id="sme-jurisdiction"
        className={styles.input}
        value={values.license_jurisdiction ?? ''}
        onChange={(event) => set('license_jurisdiction', event.target.value)}
      />

      <label className={styles.label} htmlFor="sme-bio">
        Bio
      </label>
      <textarea
        id="sme-bio"
        className={styles.textarea}
        rows={3}
        value={values.bio ?? ''}
        onChange={(event) => set('bio', event.target.value)}
      />
      <p className={styles.hint}>Bio and affiliation are internal - not shown on the public course page.</p>

      <div className={styles.checkboxRow}>
        <label>
          <input
            type="checkbox"
            checked={values.is_licensed_cpa}
            onChange={(event) => set('is_licensed_cpa', event.target.checked)}
          />
          Licensed CPA
        </label>
        <label>
          <input
            type="checkbox"
            checked={values.is_tax_attorney}
            onChange={(event) => set('is_tax_attorney', event.target.checked)}
          />
          Tax attorney
        </label>
        <label>
          <input
            type="checkbox"
            checked={values.is_enrolled_agent}
            onChange={(event) => set('is_enrolled_agent', event.target.checked)}
          />
          Enrolled agent
        </label>
      </div>

      <div className={styles.formActions}>
        <Button type="submit" variant="primary" disabled={saving || !values.name.trim() || !values.credentials.trim()}>
          {saving ? 'Saving…' : submitLabel}
        </Button>
        {onCancel && (
          <Button type="button" variant="secondary" onClick={onCancel}>
            Cancel
          </Button>
        )}
      </div>
      {error && <p className={styles.fieldError}>{error}</p>}
    </form>
  )
}

export default SMEForm
