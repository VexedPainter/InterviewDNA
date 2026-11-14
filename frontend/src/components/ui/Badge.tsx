import React from 'react'
import { cn } from '../../lib/utils'

interface BadgeProps {
  variant?: 'default' | 'accent' | 'success' | 'warn' | 'danger' | 'outline'
  size?: 'sm' | 'md'
  children: React.ReactNode
  className?: string
  onClick?: () => void
}

export const Badge: React.FC<BadgeProps> = ({
  variant = 'default',
  size = 'md',
  children,
  className,
  onClick,
}) => {
  const variants = {
    default: 'bg-white/10 text-text border-border',
    accent: 'bg-accent/15 text-accent border-accent/30',
    success: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
    warn: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
    danger: 'bg-rose-500/15 text-rose-400 border-rose-500/30',
    outline: 'bg-transparent text-muted border-border hover:text-text',
  }

  const sizes = {
    sm: 'px-2 py-0.5 text-[10px]',
    md: 'px-2.5 py-1 text-xs',
  }

  return (
    <span
      onClick={onClick}
      className={cn(
        'inline-flex items-center font-medium rounded-full border transition-all duration-150',
        variants[variant],
        sizes[size],
        onClick && 'cursor-pointer hover:scale-105 active:scale-95',
        className
      )}
    >
      {children}
    </span>
  )
}
