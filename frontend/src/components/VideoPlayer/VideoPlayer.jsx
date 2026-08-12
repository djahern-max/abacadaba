import { useCallback, useEffect, useRef, useState } from 'react'
import { getLessonThumbnailUrl, getLessonVideoUrl } from '../../api/courses'
import { getWatchProgress, sendHeartbeat } from '../../api/watch'
import styles from './VideoPlayer.module.css'

const HEARTBEAT_INTERVAL_SECONDS = 10

function formatTime(seconds) {
  const total = Math.max(0, Math.round(seconds))
  const minutes = Math.floor(total / 60)
  const secs = total % 60
  return `${minutes}:${String(secs).padStart(2, '0')}`
}

function VideoPlayer({ courseSlug, lessonSlug, onProgressChange }) {
  const [state, setState] = useState({ status: 'loading', url: null })
  const [progress, setProgress] = useState(null)
  const [barRatio, setBarRatio] = useState(0)
  const [posterUrl, setPosterUrl] = useState(null)
  const videoRef = useRef(null)
  const lastHeartbeatAtRef = useRef(0)

  const fetchUrl = useCallback(() => {
    setState({ status: 'loading', url: null })
    getLessonVideoUrl(courseSlug, lessonSlug)
      .then(({ url }) => setState({ status: 'playing', url }))
      .catch((error) => {
        setState({ status: error.status === 404 ? 'no-video' : 'error', url: null })
      })
  }, [courseSlug, lessonSlug])

  useEffect(() => {
    fetchUrl()
  }, [fetchUrl])

  useEffect(() => {
    getLessonThumbnailUrl(courseSlug, lessonSlug)
      .then(({ url }) => setPosterUrl(url))
      .catch(() => setPosterUrl(null))
  }, [courseSlug, lessonSlug])

  useEffect(() => {
    getWatchProgress(courseSlug, lessonSlug)
      .then((data) => {
        setProgress(data)
        onProgressChange?.(data)
      })
      .catch(() => {})
  }, [courseSlug, lessonSlug, onProgressChange])

  // The server response is always the source of truth for the bar; it
  // corrects any drift from the timeupdate-driven estimate below.
  useEffect(() => {
    if (progress) {
      setBarRatio(progress.ratio)
    }
  }, [progress])

  const flushHeartbeat = useCallback(
    (position) => {
      lastHeartbeatAtRef.current = Date.now()
      sendHeartbeat(courseSlug, lessonSlug, Math.max(0, Math.floor(position)))
        .then((data) => {
          setProgress(data)
          onProgressChange?.(data)
        })
        .catch(() => {})
    },
    [courseSlug, lessonSlug, onProgressChange],
  )

  useEffect(() => {
    function handleVisibilityChange() {
      const video = videoRef.current
      if (document.visibilityState === 'hidden' && video && !video.paused && !video.ended) {
        flushHeartbeat(video.currentTime)
      }
    }
    document.addEventListener('visibilitychange', handleVisibilityChange)
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
  }, [flushHeartbeat])

  function handleTimeUpdate(event) {
    const video = event.target
    if (video.paused || video.seeking) return

    // Keep the heartbeat cadence for writes, but let the bar itself move
    // with every timeupdate tick so it doesn't visibly jump in 10s steps.
    if (progress?.required_seconds) {
      setBarRatio(Math.min(video.currentTime / progress.required_seconds, 1))
    }

    const secondsSinceLastHeartbeat = (Date.now() - lastHeartbeatAtRef.current) / 1000
    if (secondsSinceLastHeartbeat >= HEARTBEAT_INTERVAL_SECONDS) {
      flushHeartbeat(video.currentTime)
    }
  }

  function handleEnded(event) {
    flushHeartbeat(event.target.currentTime)
  }

  if (state.status === 'loading') {
    return <div className={styles.frame}>Loading video&hellip;</div>
  }

  if (state.status === 'no-video') {
    return <div className={styles.frame}>Video coming soon</div>
  }

  if (state.status === 'error') {
    return (
      <div className={styles.frame}>
        <div className={styles.errorState}>
          <p>This video couldn&apos;t be played.</p>
          <button type="button" className={styles.reloadButton} onClick={fetchUrl}>
            Reload video
          </button>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className={styles.frame}>
        <video
          ref={videoRef}
          className={styles.video}
          src={state.url}
          poster={posterUrl || undefined}
          controls
          preload="metadata"
          onTimeUpdate={handleTimeUpdate}
          onEnded={handleEnded}
          onError={() => setState({ status: 'error', url: null })}
        />
      </div>
      {progress && (
        <div className={styles.progressWrap}>
          <div className={styles.progressTrack}>
            <div className={styles.progressFill} style={{ width: `${Math.round(barRatio * 100)}%` }} />
          </div>
          <p className={styles.progressText}>
            {progress.duration_seconds == null
              ? 'Watching this video is not required for this lesson.'
              : progress.unlocked
                ? 'Watched'
                : `${formatTime(Math.min(progress.watched_seconds, progress.duration_seconds))} of ${formatTime(progress.duration_seconds)} watched`}
          </p>
        </div>
      )}
    </div>
  )
}

export default VideoPlayer
