import styles from './ProgressBar.module.css'

function ProgressBar({ current, total }) {
  const percent = Math.round((current / total) * 100)

  return (
    <div className={styles.wrapper}>
      <span className={styles.label}>
        Question {current} of {total}
      </span>
      <div
        className={styles.track}
        role="progressbar"
        aria-valuenow={current}
        aria-valuemin={1}
        aria-valuemax={total}
      >
        <div className={styles.fill} style={{ width: `${percent}%` }} />
      </div>
    </div>
  )
}

export default ProgressBar
