import Button from '../Button/Button'
import styles from './StickySaveBar.module.css'

function StickySaveBar({ count, saving, error, onSave }) {
  const dirty = count > 0

  return (
    <div className={`${styles.bar} ${dirty ? styles.visible : ''}`} aria-live="polite">
      {dirty && (
        <>
          <span className={styles.status}>{`${count} unsaved change${count === 1 ? '' : 's'}`}</span>
          {error && <span className={styles.error}>{error}</span>}
          <Button variant="primary" className={styles.button} onClick={onSave} disabled={saving}>
            {saving ? 'Saving…' : 'Save'}
          </Button>
        </>
      )}
    </div>
  )
}

export default StickySaveBar
