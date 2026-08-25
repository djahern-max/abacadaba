import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getSiteStatus } from '../../api/meta'
import { getPolicies } from '../../api/policies'
import styles from './Footer.module.css'

// Fetched rather than hardcoded, same reasoning as the policies table itself
// (current-feature.md, "Rows, not hardcoded JSX") - the footer should never
// drift from whatever four documents actually exist.
//
// Feature 029, Part 6: shown only while at least one published course is
// offered as a CPE program - derived from show_policy_footer, not a second
// flag that could disagree with the per-course program_kind. A site with
// only general courses has nothing here to show; publishing one CPE-
// presented course again brings it back with no configuration.
function Footer() {
  const [policies, setPolicies] = useState([])
  const [showFooter, setShowFooter] = useState(false)

  useEffect(() => {
    getPolicies()
      .then(setPolicies)
      .catch(() => {})
    getSiteStatus()
      .then((status) => setShowFooter(status.show_policy_footer))
      .catch(() => {})
  }, [])

  if (!showFooter) return null

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
