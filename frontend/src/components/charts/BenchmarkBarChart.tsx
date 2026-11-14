import React from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'

interface BenchmarkBarChartProps {
  userScores: {
    correctness: number
    depth: number
    communication: number
    overall: number
  }
  benchmarkAvg?: number
  className?: string
}

export const BenchmarkBarChart: React.FC<BenchmarkBarChartProps> = ({
  userScores,
  benchmarkAvg = 7.5,
  className = '',
}) => {
  const chartData = [
    {
      metric: 'Correctness',
      Candidate: Number((userScores.correctness || 0).toFixed(1)),
      'Selected Avg': Number((benchmarkAvg * 0.98).toFixed(1)),
    },
    {
      metric: 'Depth',
      Candidate: Number((userScores.depth || 0).toFixed(1)),
      'Selected Avg': Number((benchmarkAvg * 0.95).toFixed(1)),
    },
    {
      metric: 'Communication',
      Candidate: Number((userScores.communication || 0).toFixed(1)),
      'Selected Avg': Number((benchmarkAvg * 1.02).toFixed(1)),
    },
    {
      metric: 'Overall',
      Candidate: Number((userScores.overall || 0).toFixed(1)),
      'Selected Avg': Number(benchmarkAvg.toFixed(1)),
    },
  ]

  return (
    <div className={`w-full h-72 ${className}`}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 20, right: 20, left: -20, bottom: 5 }}>
          <XAxis dataKey="metric" stroke="var(--muted)" fontSize={11} tickLine={false} axisLine={false} />
          <YAxis domain={[0, 10]} stroke="var(--muted)" fontSize={11} tickLine={false} axisLine={false} />
          <Tooltip
            contentStyle={{
              backgroundColor: 'var(--surface-elevated)',
              borderColor: 'var(--border)',
              borderRadius: '12px',
              color: 'var(--text)',
              fontSize: '12px',
              boxShadow: '0 8px 30px rgba(0,0,0,0.3)',
            }}
          />
          <Legend
            verticalAlign="top"
            height={36}
            formatter={(value) => (
              <span className="text-xs text-muted font-medium">{value}</span>
            )}
          />
          <Bar dataKey="Candidate" fill="#8b5cf6" radius={[6, 6, 0, 0]} />
          <Bar dataKey="Selected Avg" fill="#06b6d4" radius={[6, 6, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
