/**
 * motion.ts — Centralised animation presets for InterviewDNA
 *
 * All motion values live here. Import from this module instead of
 * scattering magic numbers across components.
 */

import type { Transition, Variants } from 'framer-motion'

// ─── Easing Curves ───────────────────────────────────────────────────────────

/** Primary ease: snappy decelerate (like Material You standard easing). */
export const EASE_OUT = [0.16, 1, 0.3, 1] as const

/** Secondary ease: gentle both-sides ease for floats/pulses. */
export const EASE_INOUT = [0.4, 0, 0.2, 1] as const

/** Overshoot spring for card lifts, button presses, etc. */
export const SPRING_SNAPPY = { type: 'spring', stiffness: 500, damping: 30 } as const

/** Soft spring for page-level enters and large elements. */
export const SPRING_SOFT = { type: 'spring', stiffness: 180, damping: 24 } as const

/** Gentle bounce for icon micro-animations. */
export const SPRING_BOUNCY = { type: 'spring', stiffness: 600, damping: 20 } as const

// ─── Duration Tokens ─────────────────────────────────────────────────────────

export const DURATION = {
  instant: 0.1,
  fast: 0.18,
  normal: 0.28,
  slow: 0.5,
  xslow: 0.8,
} as const

// ─── Standard Transitions ─────────────────────────────────────────────────────

export const tFast: Transition = { duration: DURATION.fast, ease: EASE_OUT }
export const tNormal: Transition = { duration: DURATION.normal, ease: EASE_OUT }
export const tSlow: Transition = { duration: DURATION.slow, ease: EASE_OUT }

// ─── Page / Route Transition Variants ────────────────────────────────────────

export const pageVariants: Variants = {
  initial: { opacity: 0, y: 10 },
  animate: { opacity: 1, y: 0, transition: { ...tNormal } },
  exit: { opacity: 0, y: -6, transition: { duration: DURATION.fast, ease: EASE_INOUT } },
}

// ─── Fade-up stagger for lists ────────────────────────────────────────────────

export const listContainer: Variants = {
  initial: {},
  animate: { transition: { staggerChildren: 0.07, delayChildren: 0.05 } },
}

export const listItem: Variants = {
  initial: { opacity: 0, y: 14 },
  animate: { opacity: 1, y: 0, transition: { duration: DURATION.normal, ease: EASE_OUT } },
}

// ─── Card hover variants ──────────────────────────────────────────────────────

export const cardHover = {
  rest: { y: 0, boxShadow: '0 4px 16px -4px rgba(0,0,0,0.2)' },
  hover: { y: -3, boxShadow: '0 12px 32px -8px rgba(139,92,246,0.25)', transition: tFast },
  tap: { scale: 0.98, transition: tFast },
}

// ─── Slide-in from right (drawer / side panel) ────────────────────────────────

export const slideInRight: Variants = {
  initial: { x: '100%', opacity: 0 },
  animate: { x: 0, opacity: 1, transition: SPRING_SOFT },
  exit: { x: '100%', opacity: 0, transition: tFast },
}

// ─── Scale pop (tooltips, badges, chips) ─────────────────────────────────────

export const scalePop: Variants = {
  initial: { scale: 0.8, opacity: 0 },
  animate: { scale: 1, opacity: 1, transition: SPRING_BOUNCY },
  exit: { scale: 0.8, opacity: 0, transition: tFast },
}

// ─── Reduced-motion safe wrapper ─────────────────────────────────────────────

/**
 * Returns `variants` as-is in full-motion environments, or collapses them to
 * simple opacity fades when `prefers-reduced-motion: reduce` is active.
 */
export function motionSafe<V extends Variants>(variants: V): V {
  if (typeof window === 'undefined') return variants
  if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) return variants
  // Collapse to opacity-only fade
  const safe: Variants = {}
  for (const key of Object.keys(variants)) {
    safe[key] = key === 'initial'
      ? { opacity: 0 }
      : key === 'exit'
      ? { opacity: 0 }
      : { opacity: 1 }
  }
  return safe as V
}
