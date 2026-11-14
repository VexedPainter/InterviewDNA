/**
 * LogoMark.tsx — Animated DNA-helix-inspired SVG logo.
 *
 * Uses two interlocking sine-wave strands drawn as SVG paths that animate
 * on mount (draw-on effect via stroke-dashoffset) and gently loop.
 * Fully accessible with aria-hidden on the SVG (parent <Link> has text label).
 */
import React from 'react'
import { motion } from 'framer-motion'

interface LogoMarkProps {
  size?: number
  className?: string
}

export const LogoMark: React.FC<LogoMarkProps> = ({ size = 40, className = '' }) => {
  // Helix geometry: two sinusoidal paths over a 36×36 viewport
  // Strand A: peaks top-left, bottom-right
  // Strand B: peaks top-right, bottom-left (phase shifted by π)
  const W = 36
  const H = 36
  const cx = W / 2
  const amp = 8   // amplitude
  const freq = 2  // number of full waves
  const steps = 48

  const makeStrand = (phase: number) => {
    const pts = Array.from({ length: steps + 1 }, (_, i) => {
      const t = i / steps
      const x = cx + amp * Math.sin(2 * Math.PI * freq * t + phase)
      const y = H * t
      return `${i === 0 ? 'M' : 'L'}${x.toFixed(2)},${y.toFixed(2)}`
    })
    return pts.join(' ')
  }

  const strandA = makeStrand(0)
  const strandB = makeStrand(Math.PI)

  // Cross-rungs at every half-wavelength
  const rungs: Array<{ x1: number; y1: number; x2: number; y2: number }> = []
  const rungCount = freq * 2  // one rung per half wave
  for (let r = 0; r < rungCount; r++) {
    const t = (r + 0.5) / rungCount
    const y = H * t
    const xA = cx + amp * Math.sin(2 * Math.PI * freq * t)
    const xB = cx + amp * Math.sin(2 * Math.PI * freq * t + Math.PI)
    rungs.push({ x1: xA, y1: y, x2: xB, y2: y })
  }

  const pathLength = 200 // approximate, works for dash animation

  return (
    <svg
      width={size}
      height={size}
      viewBox={`-2 -2 ${W + 4} ${H + 4}`}
      fill="none"
      aria-hidden="true"
      className={className}
    >
      <defs>
        <linearGradient id="helix-grad-a" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="var(--accent-violet)" />
          <stop offset="100%" stopColor="var(--accent-cyan)" />
        </linearGradient>
        <linearGradient id="helix-grad-b" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor="var(--accent-cyan)" />
          <stop offset="100%" stopColor="var(--accent-magenta)" />
        </linearGradient>
      </defs>

      {/* Strand A */}
      <motion.path
        d={strandA}
        stroke="url(#helix-grad-a)"
        strokeWidth="2.5"
        strokeLinecap="round"
        initial={{ pathLength: 0, opacity: 0 }}
        animate={{ pathLength: 1, opacity: 1 }}
        transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
      />

      {/* Strand B */}
      <motion.path
        d={strandB}
        stroke="url(#helix-grad-b)"
        strokeWidth="2.5"
        strokeLinecap="round"
        initial={{ pathLength: 0, opacity: 0 }}
        animate={{ pathLength: 1, opacity: 1 }}
        transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1], delay: 0.15 }}
      />

      {/* Cross-rungs */}
      {rungs.map((r, i) => (
        <motion.line
          key={i}
          x1={r.x1}
          y1={r.y1}
          x2={r.x2}
          y2={r.y2}
          stroke="var(--accent)"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeOpacity="0.6"
          initial={{ scaleX: 0, opacity: 0 }}
          animate={{ scaleX: 1, opacity: 1 }}
          transition={{ duration: 0.3, delay: 0.6 + i * 0.08, ease: [0.16, 1, 0.3, 1] }}
          style={{ transformOrigin: `${(r.x1 + r.x2) / 2}px ${r.y1}px` }}
        />
      ))}
    </svg>
  )
}
