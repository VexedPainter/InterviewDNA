import React from 'react'
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'

interface RoundDonutChartProps {
  data: Record<string, number>
  className?: string
}

const COLORS = ['#8b5cf6', '#06b6d4', '#ec4899', '#10b981', '#f59e0b']

export const RoundDonutChart: React.FC<RoundDonutChartProps> = ({ data, className = '' }) => {
  const chartData = Object.entries(data).map(([round, percent]) => ({
    name: round,
    value: percent,
  }))

  return (
    <div className={`w-full h-64 ${className}`}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Tooltip
            contentStyle={{
              backgroundColor: 'var(--surface-elevated)',
              borderColor: 'var(--border)',
              borderRadius: '12px',
              color: 'var(--text)',
              fontSize: '12px',
              boxShadow: '0 8px 30px rgba(0,0,0,0.3)',
            }}
            formatter={(value: any) => [`${value}%`, 'Share']}
          />
          <Legend
            verticalAlign="bottom"
            height={36}
            formatter={(value) => (
              <span className="text-xs text-muted font-medium">{value}</span>
            )}
          />
          <Pie
            data={chartData}
            cx="50%"
            cy="45%"
            innerRadius={55}
            outerRadius={80}
            paddingAngle={4}
            dataKey="value"
          >
            {chartData.map((_, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}
