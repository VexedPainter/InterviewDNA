import React from 'react'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

interface DifficultyAreaChartProps {
  data: Record<string, number>
  className?: string
}

export const DifficultyAreaChart: React.FC<DifficultyAreaChartProps> = ({ data, className = '' }) => {
  const chartData = Object.entries(data)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([year, difficulty]) => ({
      year,
      difficulty: Number(difficulty.toFixed(2)),
    }))

  return (
    <div className={`w-full h-64 ${className}`}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="difficultyGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" vertical={false} />
          <XAxis
            dataKey="year"
            stroke="var(--muted)"
            fontSize={11}
            tickLine={false}
            axisLine={false}
          />
          <YAxis
            stroke="var(--muted)"
            domain={[1, 5]}
            ticks={[1, 2, 3, 4, 5]}
            fontSize={11}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'var(--surface-elevated)',
              borderColor: 'var(--border)',
              borderRadius: '12px',
              color: 'var(--text)',
              fontSize: '12px',
              boxShadow: '0 8px 30px rgba(0,0,0,0.3)',
            }}
            formatter={(value: any) => [`${value} / 5.0`, 'Average Difficulty']}
          />
          <Area
            type="monotone"
            dataKey="difficulty"
            stroke="#06b6d4"
            strokeWidth={2.5}
            fillOpacity={1}
            fill="url(#difficultyGrad)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}
