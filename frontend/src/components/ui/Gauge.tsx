import React from 'react'
import { motion } from 'framer-motion'

interface GaugeProps {
  value: number // typically 0 to 10
  max?: number
  label: string
  sublabel?: string
  size?: number
  strokeWidth?: number
  color?: string
}

export const Gauge: React.FC<GaugeProps> = ({
  value,
  max = 10,
  label,
  sublabel,
  size = 110,
  strokeWidth = 9,
  color = '#8b5cf6',
}) => {
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const percent = Math.min(Math.max(value / max, 0), 1)
  const offset = circumference - percent * circumference

  return (
    <div className="flex flex-col items-center justify-center p-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="rotate-[-90deg]">
          {/* Background Track */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="transparent"
            stroke="currentColor"
            strokeWidth={strokeWidth}
            className="text-border/40"
          />
          {/* Animated Value Arc */}
          <motion.circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="transparent"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
            strokeLinecap="round"
          />
        </svg>

        {/* Center Text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-xl font-bold font-display tabular-nums text-text">
            {value.toFixed(1)}
          </span>
          <span className="text-[10px] text-muted font-medium">/{max}</span>
        </div>
      </div>

      <span className="mt-2 text-xs font-semibold text-text text-center">{label}</span>
      {sublabel && <span className="text-[10px] text-muted text-center">{sublabel}</span>}
    </div>
  )
}
