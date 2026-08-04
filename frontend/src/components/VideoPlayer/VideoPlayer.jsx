import { useCallback, useEffect, useState } from 'react'
import { getVideoUrl } from '../../api/lessons'
import styles from './VideoPlayer.module.css'

function VideoPlayer({ slug }) {
  const [state, setState] = useState({ status: 'loading', url: null })

  const fetchUrl = useCallback(() => {
    setState({ status: 'loading', url: null })
    getVideoUrl(slug)
      .then(({ url }) => setState({ status: 'playing', url }))
      .catch((error) => {
        setState({ status: error.status === 404 ? 'no-video' : 'error', url: null })
      })
  }, [slug])

  useEffect(() => {
    fetchUrl()
  }, [fetchUrl])

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
    <div className={styles.frame}>
      <video
        className={styles.video}
        src={state.url}
        controls
        preload="metadata"
        onError={() => setState({ status: 'error', url: null })}
      />
    </div>
  )
}

export default VideoPlayer
