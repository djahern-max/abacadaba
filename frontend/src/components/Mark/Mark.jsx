// The circle-beside-a-stem mark: same geometry as favicon.svg's bowl and
// stem, at header scale. See current-feature.md, "The idea the design is
// built on" - it is also a constructed lowercase `a`, which is why it can
// stand directly in front of the wordmark's own single-storey `a` without
// reading as a second, unrelated logo.
function Mark(props) {
  return (
    <svg viewBox="0 0 32 32" width="28" height="28" {...props}>
      <circle cx="12.6" cy="19" r="7.2" fill="var(--bead)" />
      <rect x="21.4" y="11.8" width="3.4" height="14.4" rx="1.7" fill="var(--ink)" />
    </svg>
  )
}

export default Mark
