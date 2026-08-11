import styles from './FileInput.module.css'

function FileInput({ id, accept, onChange, disabled, fileName, buttonLabel = 'Choose file' }) {
  return (
    <div className={styles.wrapper}>
      <input
        id={id}
        className={styles.input}
        type="file"
        accept={accept}
        onChange={onChange}
        disabled={disabled}
      />
      <label htmlFor={id} className={`${styles.button} ${disabled ? styles.disabled : ''}`}>
        {buttonLabel}
      </label>
      {fileName && <span className={styles.fileName}>{fileName}</span>}
    </div>
  )
}

export default FileInput
