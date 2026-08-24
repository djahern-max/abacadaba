import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getPolicies } from '../../api/policies'
import styles from './Footer.module.css'

// Fetched rather than hardcoded, same reasoning as the policies table itself
// (current-feature.md, "Rows, not hardcoded JSX") - the footer should never
// drift from whatever four documents actually exist.
function Footer() {
  const [policies, setPolicies] = useState([])

  useEffect(() => {
    getPolicies()
      .then(setPolicies)
      .catch(() => {})
  }, [])

  return (
    <footer className={styles.footer}>
      <nav className={styles.links}>
        {policies.map((policy) => (
          <Link key={policy.slug} to={`/policies/${policy.slug}`}>
            {policy.title}
          </Link>
        ))}
      </nav>
    </footer>
  )
}

export default Footer
