import { useState } from 'react'
import { uploadAdminVideo } from '../../../api/admin'
import styles from './VideoUploader.module.css'

function VideoUploader({ lesson, onChange }) {
  const [progress, setProgress] = useState(null)
  const [error, setError] = useState('')

  async function handleFileChange(event) {
    const file = event.target.files[0]
    if (!file) return
    setError('')
    setProgress(0)
    try {
      await uploadAdminVideo(lesson.slug, file, setProgress)
      await onChange()
    } catch {
      setError('Video upload failed. Only MP4 or WebM files are accepted.')
    } finally {
      setProgress(null)
      event.target.value = ''
    }
  }

  return (
    <section className={styles.section}>
      <h2 className={styles.heading}>Video</h2>
      <p className={styles.status}>
        {lesson.video_key ? 'A video is uploaded for this lesson.' : 'No video uploaded yet.'}
      </p>
      <input
        type="file"
        accept="video/mp4,video/webm"
        onChange={handleFileChange}
        disabled={progress !== null}
      />
      {progress !== null && (
        <div className={styles.progressTrack}>
          <div className={styles.progressFill} style={{ width: `${progress}%` }} />
          <span className={styles.progressLabel}>{progress}%</span>
        </div>
      )}
      {error && <p className={styles.fieldError}>{error}</p>}
    </section>
  )
}

export default VideoUploader
