import { useState } from 'react'
import { updateAdminSME } from '../../../api/admin'
import Button from '../../../components/Button/Button'
import SMEForm from './SMEForm'
import styles from './AdminSMEList.module.css'

function credentialTags(sme) {
  const tags = []
  if (sme.is_licensed_cpa) tags.push('Licensed CPA')
  if (sme.is_tax_attorney) tags.push('Tax attorney')
  if (sme.is_enrolled_agent) tags.push('Enrolled agent')
  return tags
}

function SMERow({ sme, onChange }) {
  const [editing, setEditing] = useState(false)

  if (editing) {
    return (
      <li className={styles.card}>
        <SMEForm
          initialValues={sme}
          submitLabel="Save"
          onCancel={() => setEditing(false)}
          onSubmit={async (values) => {
            await updateAdminSME(sme.id, values)
            setEditing(false)
            await onChange()
          }}
        />
      </li>
    )
  }

  return (
    <li className={styles.card}>
      <div className={styles.cardHeader}>
        <div>
          <strong>{sme.name}</strong> &mdash; {sme.credentials}
          {sme.license_jurisdiction && <span className={styles.muted}> ({sme.license_jurisdiction})</span>}
        </div>
        <Button variant="secondary" onClick={() => setEditing(true)}>
          Edit
        </Button>
      </div>
      {sme.affiliation && <p className={styles.muted}>{sme.affiliation}</p>}
      {credentialTags(sme).length > 0 && (
        <div className={styles.tags}>
          {credentialTags(sme).map((tag) => (
            <span key={tag} className={styles.tag}>
              {tag}
            </span>
          ))}
        </div>
      )}
    </li>
  )
}

export default SMERow
