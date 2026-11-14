/**
 * AuroraBackground.tsx
 *
 * Animated aurora gradient blobs + dotted-grid + mouse spotlight.
 * Automatically disables GPU-heavy animations when the user prefers
 * reduced motion (via CSS media query — Framer Motion also respects this).
 */
import React, { useEffect, useState, useRef } from 'react'

export const AuroraBackground: React.FC = () => {
  const [mousePos, setMousePos] = useState({ x: -1000, y: -1000 })
  const rafRef = useRef<number | null>(null)
  const latestPos = useRef({ x: -1000, y: -1000 })

  useEffect(() => {
    // Check reduced-motion preference; skip spotlight tracking if set
    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (prefersReduced) return

    const handleMouseMove = (e: MouseEvent) => {
      latestPos.current = { x: e.clientX, y: e.clientY }
      if (rafRef.current === null) {
        rafRef.current = requestAnimationFrame(() => {
          setMousePos({ ...latestPos.current })
          rafRef.current = null
        })
      }
    }

    window.addEventListener('mousemove', handleMouseMove, { passive: true })
    return () => {
      window.removeEventListener('mousemove', handleMouseMove)
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current)
    }
  }, [])

  return (
    <div
      className="fixed inset-0 pointer-events-none -z-10 overflow-hidden"
      aria-hidden="true"
    >
      {/* Aurora blob 1 — top-left violet */}
      <div
        className="absolute -top-[25%] -left-[10%] w-[60vw] h-[60vw] rounded-full filter blur-[120px] opacity-70 animate-aurora-drift will-change-transform"
        style={{
          background: 'radial-gradient(circle, var(--aurora-1) 0%, transparent 70%)',
          // Respect reduced-motion: CSS @media rule in index.css will disable animation
        }}
      />
      {/* Aurora blob 2 — right cyan */}
      <div
        className="absolute top-[20%] -right-[15%] w-[55vw] h-[55vw] rounded-full filter blur-[140px] opacity-60 animate-aurora-drift will-change-transform"
        style={{
          animationDelay: '-7s',
          background: 'radial-gradient(circle, var(--aurora-2) 0%, transparent 70%)',
        }}
      />
      {/* Aurora blob 3 — bottom magenta */}
      <div
        className="absolute -bottom-[20%] left-[20%] w-[50vw] h-[50vw] rounded-full filter blur-[130px] opacity-50 animate-aurora-drift will-change-transform"
        style={{
          animationDelay: '-14s',
          background: 'radial-gradient(circle, var(--aurora-3) 0%, transparent 70%)',
        }}
      />

      {/* Dotted Grid Texture */}
      <div
        className="absolute inset-0 opacity-[0.20] dark:opacity-[0.15]"
        style={{
          backgroundImage: `radial-gradient(var(--border) 1.2px, transparent 1.2px)`,
          backgroundSize: '32px 32px',
        }}
      />

      {/* Mouse Spotlight Glow — only renders when mouse has moved */}
      {mousePos.x > -900 && (
        <div
          className="absolute w-[560px] h-[560px] rounded-full pointer-events-none opacity-20 dark:opacity-15"
          style={{
            transform: `translate(${mousePos.x - 280}px, ${mousePos.y - 280}px)`,
            background: 'radial-gradient(circle, var(--accent) 0%, transparent 70%)',
            filter: 'blur(48px)',
            willChange: 'transform',
          }}
        />
      )}
    </div>
  )
}
