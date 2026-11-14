import React from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'

interface RejectionBarChartProps {
  data: Array<{ tag: string; count: number }>
  className?: string
}

export const RejectionBarChart: React.FC<RejectionBarChartProps> = ({ data, className = '' }) => {
  const chartData = data.slice(0, 5)

  return (
    <div className={`w-full h-64 ${className}`}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          layout="vertical"
          data={chartData}
          margin={{ top: 5, right: 30, left: 40, bottom: 5 }}
        >
          <XAxis type="number" stroke="var(--muted)" fontSize={11} tickLine={false} axisLine={false} />
          <YAxis
            type="category"
            dataKey="tag"
            stroke="var(--muted)"
            fontSize={11}
            tickLine={false}
            axisLine={false}
            width={120}
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
            formatter={(value: any) => [`${value} mentions`, 'Frequency']}
          />
          <Bar dataKey="count" radius={[0, 8, 8, 0]}>
            {chartData.map((_, index) => (
              <Cell
                key={`cell-${index}`}
                fill={index === 0 ? '#ef4444' : index === 1 ? '#f59e0b' : '#ec4899'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
