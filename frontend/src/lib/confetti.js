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

const BIG_BURST_VOLLEYS = [
  { delay: 0, particleCount: 120, spread: 100, startVelocity: 45, origin: { x: 0.3, y: 0.6 } },
  { delay: 300, particleCount: 120, spread: 100, startVelocity: 45, origin: { x: 0.7, y: 0.6 } },
  { delay: 650, particleCount: 140, spread: 130, startVelocity: 55, origin: { x: 0.5, y: 0.5 } },
]

export function bigBurst() {
  if (prefersReducedMotion()) return

  for (const volley of BIG_BURST_VOLLEYS) {
    const { delay, ...options } = volley
    setTimeout(() => confetti(options), delay)
  }
}
