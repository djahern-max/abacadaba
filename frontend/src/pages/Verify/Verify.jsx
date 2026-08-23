import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { verifyCertificate } from '../../api/certificates'
import styles from './Verify.module.css'

function formatDate(isoString) {
  return new Date(isoString).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

function Verify() {
  const { code } = useParams()
  const [state, setState] = useState({ status: 'loading', data: null })

  useEffect(() => {
    setState({ status: 'loading', data: null })
    verifyCertificate(code)
      .then((data) => setState({ status: data.valid ? 'valid' : 'not-found', data }))
      .catch(() => setState({ status: 'error', data: null }))
  }, [code])

  if (state.status === 'loading') {
    return <p className={styles.message}>Checking certificate&hellip;</p>
  }

  if (state.status === 'error') {
    return <p className={styles.message}>Couldn&apos;t check this certificate. Please try again later.</p>
  }

  if (state.status === 'not-found') {
    return (
      <div className={styles.message}>
        <h1 className={styles.heading}>Certificate not found</h1>
        <p>We couldn&apos;t find a certificate with code {code}.</p>
        <Link to="/">Back home</Link>
      </div>
    )
  }

  const { data } = state

  return (
    <div className={styles.card}>
      <h1 className={styles.heading}>Certificate verified</h1>
      <p className={styles.explainer}>
        An attempt with code {data.certificate_code} passed this course on {formatDate(data.completed_at)} with a
        score of {data.score} out of {data.question_count}.{' '}
        {data.is_account_holder
          ? 'The name below is the account holder who took the quiz.'
          : 'The name below was typed in by the person who took the quiz and is not an authenticated identity.'}
      </p>
      <dl className={styles.details}>
        <dt>Name</dt>
        <dd>{data.recipient_name}</dd>
        <dt>Course</dt>
        <dd>{data.course_title}</dd>
        <dt>Score</dt>
        <dd>
          {data.score} out of {data.question_count}
        </dd>
        <dt>Date</dt>
        <dd>{formatDate(data.completed_at)}</dd>
        <dt>Field of study</dt>
        <dd>{data.field_of_study}</dd>
        <dt>Delivery method</dt>
        <dd>{data.delivery_method}</dd>
        <dt>CPE credit awarded</dt>
        <dd>{data.credit_award ?? '—'}</dd>
        <dt>Sponsor</dt>
        <dd>
          {data.sponsor_name} (NASBA registry ID {data.sponsor_registry_id}
          {data.sponsor_state_registry_ids ? `, state registry ID(s) ${data.sponsor_state_registry_ids}` : ''})
        </dd>
      </dl>
      <p className={styles.timeStatement}>
        CPE credit has been granted based on a 50-minute hour, per NASBA Standards.
      </p>
      <Link to="/">Back home</Link>
    </div>
  )
}

export default Verify
