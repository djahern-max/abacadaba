import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getPolicy } from '../../api/policies'
import { renderMarkdown } from '../../lib/markdown'
import styles from './Policy.module.css'

function Policy() {
  const { slug } = useParams()
  const [state, setState] = useState({ status: 'loading', policy: null })

  useEffect(() => {
    setState({ status: 'loading', policy: null })
    getPolicy(slug)
      .then((policy) => setState({ status: 'loaded', policy }))
      .catch((error) => {
        setState({ status: error.status === 404 ? 'not-found' : 'error', policy: null })
      })
  }, [slug])

  if (state.status === 'loading') {
    return <p className={styles.message}>Loading&hellip;</p>
  }

  if (state.status === 'not-found') {
    return (
      <div className={styles.message}>
        <p>We couldn&apos;t find that policy.</p>
        <Link to="/">Back home</Link>
      </div>
    )
  }

  if (state.status === 'error') {
    return <p className={styles.message}>Couldn&apos;t load this policy. Please try again later.</p>
  }

  const { policy } = state

  return (
    <article className={styles.page}>
      <Link to="/" className={styles.back}>
        &larr; Back home
      </Link>
      <h1 className={styles.title}>{policy.title}</h1>
      <p className={styles.updated}>Last updated {new Date(policy.updated_at).toLocaleDateString()}</p>
      {policy.is_placeholder ? (
        <p className={styles.placeholder}>This policy has not been written yet.</p>
      ) : (
        // policy.body is rendered through lib/markdown.js's escape-first
        // renderer, not raw admin input - see that file's own comment.
        <div className={styles.body} dangerouslySetInnerHTML={{ __html: renderMarkdown(policy.body) }} />
      )}
    </article>
  )
}

export default Policy
