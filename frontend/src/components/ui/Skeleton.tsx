import React from 'react'
import { cn } from '../../lib/utils'

/**
 * Skeleton — shimmer placeholder loader.
 * Uses the .skeleton CSS class (defined in index.css) for the shimmer animation,
 * so it works regardless of Tailwind JIT purge behaviour.
 */
export const Skeleton: React.FC<{ className?: string }> = ({ className }) => {
  return (
    <div
      className={cn('skeleton', className)}
      role="status"
      aria-busy="true"
      aria-label="Loading…"
    />
  )
}
