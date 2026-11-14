import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatScore(val?: number | null, fallback = '--'): string {
  if (val === undefined || val === null || isNaN(val)) return fallback
  return val.toFixed(1)
}

export function formatPercentage(val?: number | null): string {
  if (val === undefined || val === null || isNaN(val)) return '0%'
  return `${Math.round(val)}%`
}

export function getScoreColor(score: number): { text: string; bg: string; border: string } {
  if (score >= 7.5) {
    return {
      text: 'text-emerald-400',
      bg: 'bg-emerald-500/10',
      border: 'border-emerald-500/30',
    }
  }
  if (score >= 5.5) {
    return {
      text: 'text-amber-400',
      bg: 'bg-amber-500/10',
      border: 'border-amber-500/30',
    }
  }
  return {
    text: 'text-rose-400',
    bg: 'bg-rose-500/10',
    border: 'border-rose-500/30',
  }
}
