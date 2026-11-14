import React from 'react'
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
} from 'recharts'

interface TopicRadarChartProps {
  data: Record<string, number>
  className?: string
}

export const TopicRadarChart: React.FC<TopicRadarChartProps> = ({ data, className = '' }) => {
  const chartData = Object.entries(data).map(([topic, percent]) => ({
    topic,
    weight: percent,
  }))

  if (!chartData.length) {
    return <div className="h-64 flex items-center justify-center text-sm text-muted">No topic data</div>
  }

  return (
    <div className={`w-full h-72 ${className}`}>
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="75%" data={chartData}>
          <PolarGrid stroke="var(--border)" strokeDasharray="3 3" />
          <PolarAngleAxis
            dataKey="topic"
            tick={{ fill: 'var(--muted)', fontSize: 11, fontFamily: 'Inter' }}
          />
          <PolarRadiusAxis
            angle={30}
            domain={[0, 'auto']}
            stroke="var(--border)"
            tick={{ fill: 'var(--muted)', fontSize: 9 }}
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
            formatter={(value: any) => [`${value}%`, 'Weight']}
          />
          <Radar
            name="Topic Distribution"
            dataKey="weight"
            stroke="#8b5cf6"
            fill="#8b5cf6"
            fillOpacity={0.35}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  )
}
