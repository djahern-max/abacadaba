import { useState } from 'react'
import { Link } from 'react-router-dom'
import styles from './Wordmark.module.css'

const SESSION_KEY = 'abacadaba:wordmark-animated'

// Letters split into spans read the word letter-by-letter to some screen
// readers, so the accessible name lives on the link instead and the spelled-
// out wordmark is aria-hidden. See current-feature.md, Part 2,
// "Accessibility, and this is the part that gets missed."
const LETTERS = [
  { char: 'a', accent: false },
  { char: 'b', accent: true },
  { char: 'a', accent: false },
  { char: 'c', accent: true },
  { char: 'a', accent: false },
  { char: 'd', accent: true },
  { char: 'a', accent: false },
  { char: 'b', accent: true },
  { char: 'a', accent: false },
]

function Wordmark() {
  // Read once, synchronously, so the very first render already knows
  // whether this is the first paint of the session - animating and then
  // immediately un-animating would flash.
  const [animate] = useState(() => {
    try {
      if (sessionStorage.getItem(SESSION_KEY)) return false
      sessionStorage.setItem(SESSION_KEY, '1')
      return true
    } catch {
      return false
    }
  })

  return (
    <Link to="/" className={styles.brand} aria-label="abacadaba, home">
      <span className={animate ? `${styles.wordmark} ${styles.animate}` : styles.wordmark} aria-hidden="true">
        {LETTERS.map((letter, index) =>
          letter.accent ? (
            <b key={index} className={styles.accent} style={{ '--i': index }}>
              {letter.char}
            </b>
          ) : (
            <i key={index} className={styles.constant} style={{ '--i': index }}>
              {letter.char}
            </i>
          ),
        )}
      </span>
      <span className={styles.descriptor} aria-hidden="true">
        Get Wicked Smart!
      </span>
    </Link>
  )
}

export default Wordmark
