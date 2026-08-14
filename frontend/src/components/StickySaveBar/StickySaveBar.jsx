import styles from './StickySaveBar.module.css'

function StickySaveBar({ count, saving, error, onSave }) {
  const inert = count === 0 && !saving

  return (
    <div className={`${styles.bar} ${inert ? styles.inert : ''}`}>
      <span className={styles.status}>
        {count === 0 ? 'No unsaved changes' : `${count} unsaved change${count === 1 ? '' : 's'}`}
      </span>
      {error && <span className={styles.error}>{error}</span>}
      <button type="button" className={styles.button} onClick={onSave} disabled={inert || saving}>
        {saving ? 'Saving…' : 'Save'}
      </button>
    </div>
  )
}

export default StickySaveBar
