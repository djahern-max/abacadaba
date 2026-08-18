import { useState } from 'react'
import { createAdminSource, deleteAdminSource, moveAdminSource } from '../../../api/admin'
import Button from '../../../components/Button/Button'
import styles from './LessonsPanel.module.css'

// Recorded, not required for publish - see current-feature.md, "Sources are
// recorded, not required". Add/reorder/delete take effect immediately, like
// LessonsPanel, rather than joining the page's batched save.
function SourcesPanel({ course, onChange }) {
  const [citation, setCitation] = useState('')
  const [url, setUrl] = useState('')
  const [adding, setAdding] = useState(false)
  const [error, setError] = useState('')

  async function handleAdd(event) {
    event.preventDefault()
    if (!citation.trim()) return
    setError('')
    setAdding(true)
    try {
      await createAdminSource(course.id, { citation: citation.trim(), url: url.trim() || null })
      setCitation('')
      setUrl('')
      await onChange()
    } catch {
      setError('Could not add the source.')
    } finally {
      setAdding(false)
    }
  }

  async function handleMove(sourceId, direction) {
    await moveAdminSource(sourceId, direction)
    await onChange()
  }

  async function handleDelete(sourceId) {
    await deleteAdminSource(sourceId)
    await onChange()
  }

  return (
    <section>
      <h3 className={styles.heading}>Sources ({course.sources.length})</h3>
      <p className={styles.emptyState}>
        The references this course was built from. Not required to publish, but shown here for the reviewer
        to see before signing off.
      </p>

      {course.sources.length > 0 && (
        <ol className={styles.list}>
          {course.sources.map((source, index) => (
            <li key={source.id} className={styles.row}>
              <div className={styles.rowMain}>
                {source.position}. {source.citation}
                {source.url && (
                  <>
                    {' '}
                    &mdash;{' '}
                    <a href={source.url} target="_blank" rel="noreferrer">
                      {source.url}
                    </a>
                  </>
                )}
              </div>
              <div className={styles.rowMeta}>
                <Button
                  variant="secondary"
                  onClick={() => handleMove(source.id, 'up')}
                  disabled={index === 0}
                  aria-label="Move source up"
                >
                  &uarr;
                </Button>
                <Button
                  variant="secondary"
                  onClick={() => handleMove(source.id, 'down')}
                  disabled={index === course.sources.length - 1}
                  aria-label="Move source down"
                >
                  &darr;
                </Button>
                <Button variant="danger" onClick={() => handleDelete(source.id)}>
                  Delete
                </Button>
              </div>
            </li>
          ))}
        </ol>
      )}

      <form className={styles.addForm} onSubmit={handleAdd}>
        <input
          className={styles.input}
          type="text"
          placeholder="Citation"
          value={citation}
          onChange={(event) => setCitation(event.target.value)}
          disabled={adding}
        />
        <input
          className={styles.input}
          type="text"
          placeholder="URL (optional)"
          value={url}
          onChange={(event) => setUrl(event.target.value)}
          disabled={adding}
        />
        <Button type="submit" variant="secondary" disabled={adding || !citation.trim()}>
          Add source
        </Button>
      </form>
      {error && <p className={styles.fieldError}>{error}</p>}
    </section>
  )
}

export default SourcesPanel
