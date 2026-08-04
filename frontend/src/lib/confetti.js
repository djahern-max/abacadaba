import confetti from 'canvas-confetti'

function prefersReducedMotion() {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

export function smallBurst(originElement) {
  if (prefersReducedMotion()) return

  let origin = { x: 0.5, y: 0.5 }
  if (originElement) {
    const rect = originElement.getBoundingClientRect()
    origin = {
      x: (rect.left + rect.width / 2) / window.innerWidth,
      y: (rect.top + rect.height / 2) / window.innerHeight,
    }
  }

  confetti({
    particleCount: 40,
    spread: 60,
    startVelocity: 30,
    origin,
  })
}

// Big burst arrives with feature 006, once passing at 4/5 is a real outcome.
export function bigBurst() {
  if (prefersReducedMotion()) return
}
