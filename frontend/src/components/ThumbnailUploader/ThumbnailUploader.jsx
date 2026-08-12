import { useEffect, useState } from 'react'
import { uploadAdminThumbnail } from '../../../api/admin'
import { getThumbnailUrl } from '../../../api/lessons'
import FileInput from '../../../components/FileInput/FileInput'
import styles from './ThumbnailUploader.module.css'

function ThumbnailUploader({ lesson, onUploadingChange, onChange }) {
  const [fileName, setFileName] = useState('')
  const [uploadStatus, setUploadStatus] = useState(null)
  const [error, setError] = useState('')
  const [warning, setWarning] = useState('')
  const [previewUrl, setPreviewUrl] = useState(null)

  useEffect(() => {
    setPreviewUrl(null)
    if (!lesson.thumbnail_key) return
    let cancelled = false
    getThumbnailUrl(lesson.slug)
      .then(({ url }) => {
        if (!cancelled) setPreviewUrl(url)
      })
      .catch(() => {})
    return () => {
      cancelled = true
    }
  }, [lesson.thumbnail_key, lesson.slug])

  async function handleFileChange(event) {
    const file = event.target.files[0]
    if (!file) return
    setError('')
    setWarning('')
    setFileName(file.name)
    setPreviewUrl(URL.createObjectURL(file))
    onUploadingChange?.(true)

    setUploadStatus({ status: 'uploading', percent: 0 })
    try {
      const result = await uploadAdminThumbnail(lesson.id, file, (percent) => {
        setUploadStatus(percent >= 100 ? { status: 'processing' } : { status: 'uploading', percent })
      })
      setWarning(result.warning ?? '')
      await onChange()
    } catch (uploadError) {
      setError(
        uploadError.body?.detail ??
          'Thumbnail upload failed. Only JPEG, PNG, or WebP files up to 2 MB are accepted.',
      )
    } finally {
      setUploadStatus(null)
      onUploadingChange?.(false)
      event.target.value = ''
    }
  }

  return (
    <section className={styles.section}>
      <h2 className={styles.heading}>Thumbnail</h2>
      <p className={styles.status}>
        {lesson.thumbnail_key ? 'A thumbnail is uploaded for this lesson.' : 'No thumbnail uploaded yet.'}
      </p>
      {previewUrl && <img src={previewUrl} alt="" className={styles.preview} />}
      <FileInput
        id="thumbnail-file"
        accept="image/jpeg,image/png,image/webp"
        onChange={handleFileChange}
        disabled={uploadStatus !== null}
        fileName={fileName}
        buttonLabel="Choose thumbnail"
      />
      <p className={styles.hint}>Recommended size: 1280&times;720 (16:9). JPEG, PNG, or WebP, up to 2 MB.</p>
      {uploadStatus && (
        <p className={styles.uploadStatus}>
          {uploadStatus.status === 'uploading' && `Uploading… ${uploadStatus.percent}%`}
          {uploadStatus.status === 'processing' && 'Processing…'}
        </p>
      )}
      {warning && <p className={styles.warning}>{warning}</p>}
      {error && <p className={styles.fieldError}>{error}</p>}
    </section>
  )
}

export default ThumbnailUploader
