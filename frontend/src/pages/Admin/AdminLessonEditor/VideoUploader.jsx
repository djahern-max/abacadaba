import { useState } from 'react'
import { uploadAdminVideo } from '../../../api/admin'
import FileInput from '../../../components/FileInput/FileInput'
import styles from './VideoUploader.module.css'

function readVideoDuration(file) {
  return new Promise((resolve) => {
    const video = document.createElement('video')
    video.preload = 'metadata'
    const url = URL.createObjectURL(file)
    video.onloadedmetadata = () => {
      URL.revokeObjectURL(url)
      resolve(Math.floor(video.duration))
    }
    video.onerror = () => {
      URL.revokeObjectURL(url)
      resolve(null)
    }
    video.src = url
  })
}

function VideoUploader({ lesson, onDurationDetected, onUploadingChange, onChange }) {
  const [fileName, setFileName] = useState('')
  const [uploadStatus, setUploadStatus] = useState(null)
  const [error, setError] = useState('')

  async function handleFileChange(event) {
    const file = event.target.files[0]
    if (!file) return
    setError('')
    setFileName(file.name)
    onUploadingChange?.(true)

    readVideoDuration(file).then((seconds) => {
      if (seconds != null && Number.isFinite(seconds)) onDurationDetected?.(seconds)
    })

    setUploadStatus({ status: 'uploading', percent: 0 })
    try {
      await uploadAdminVideo(lesson.slug, file, (percent) => {
        setUploadStatus(percent >= 100 ? { status: 'processing' } : { status: 'uploading', percent })
      })
      await onChange()
    } catch {
      setError('Video upload failed. Only MP4 or WebM files are accepted.')
    } finally {
      setUploadStatus(null)
      onUploadingChange?.(false)
      event.target.value = ''
    }
  }

  return (
    <section className={styles.section}>
      <h2 className={styles.heading}>Video</h2>
      <p className={styles.status}>
        {lesson.video_key ? 'A video is uploaded for this lesson.' : 'No video uploaded yet.'}
      </p>
      <FileInput
        id="video-file"
        accept="video/mp4,video/webm"
        onChange={handleFileChange}
        disabled={uploadStatus !== null}
        fileName={fileName}
        buttonLabel="Choose video"
      />
      <p className={styles.hint}>
        This saves immediately when you choose a file — unlike the rest of this page, there is no separate
        save step.
      </p>
      {uploadStatus && (
        <p className={styles.uploadStatus}>
          {uploadStatus.status === 'uploading' && `Uploading… ${uploadStatus.percent}%`}
          {uploadStatus.status === 'processing' && 'Processing…'}
          <br />
          <span className={styles.uploadWarning}>
            The upload is running now. Leaving this page cancels it.
          </span>
        </p>
      )}
      {error && <p className={styles.fieldError}>{error}</p>}
    </section>
  )
}

export default VideoUploader
