/**
 * GlassCard.tsx — glass-morphism card with centralised motion presets.
 */
import React from 'react'
import { motion, HTMLMotionProps } from 'framer-motion'
import { cn } from '../../lib/utils'
import { SPRING_SNAPPY } from '../../lib/motion'

interface GlassCardProps extends HTMLMotionProps<'div'> {
  elevated?: boolean
  glow?: 'none' | 'violet' | 'cyan' | 'magenta'
  children: React.ReactNode
}

const GLOW_STYLES = {
  none: '',
  violet: 'hover:shadow-glow-violet hover:border-accent/40',
  cyan: 'hover:shadow-glow-cyan hover:border-accent-cyan/40',
  magenta: 'hover:shadow-[0_0_25px_-5px_rgba(236,72,153,0.4)] hover:border-accent-magenta/40',
}

export const GlassCard: React.FC<GlassCardProps> = ({
  elevated = false,
  glow = 'none',
  className,
  children,
  whileHover,
  whileTap,
  ...props
}) => {
  return (
    <motion.div
      className={cn(
        elevated ? 'glass-panel-elevated' : 'glass-panel',
        'rounded-3xl p-6 relative overflow-hidden',
        GLOW_STYLES[glow],
        className
      )}
      whileHover={whileHover ?? { y: -2, transition: { ...SPRING_SNAPPY } }}
      whileTap={whileTap ?? { scale: 0.98 }}
      {...props}
    >
      {/* Subtle top hairline highlight */}
      <div
        className="absolute inset-x-0 top-0 h-[1px] bg-gradient-to-r from-transparent via-white/20 to-transparent pointer-events-none"
        aria-hidden="true"
      />
      {children}
    </motion.div>
  )
}
