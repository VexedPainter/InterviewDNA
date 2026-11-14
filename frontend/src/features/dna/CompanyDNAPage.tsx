import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { usePageTitle } from '../../hooks/usePageTitle'
import {
  Dna,
  Building2,
  TrendingUp,
  Percent,
  Compass,
  AlertTriangle,
  Layers,
  Sparkles,
  Quote,
} from 'lucide-react'
import { GlassCard } from '../../components/ui/GlassCard'
import { TopicRadarChart } from '../../components/charts/TopicRadarChart'
import { DifficultyAreaChart } from '../../components/charts/DifficultyAreaChart'
import { RoundDonutChart } from '../../components/charts/RoundDonutChart'
import { RejectionBarChart } from '../../components/charts/RejectionBarChart'
import { useQuery } from '@tanstack/react-query'
import { api } from '../../lib/api/client'
import { useSessionStore } from '../../store/sessionStore'

const COMPANIES = ['Zoho', 'Amazon', 'Google', 'TCS', 'Infosys', 'Accenture', 'Deloitte', 'Flipkart']

export const CompanyDNAPage: React.FC = () => {
  usePageTitle('Company DNA')
  const { company: selectedCompany, setConfig } = useSessionStore()
  const [activeCompany, setActiveCompany] = useState(selectedCompany || 'Zoho')

  const { data: dna, isLoading } = useQuery({
    queryKey: ['dna', activeCompany],
    queryFn: () => api.getCompanyDNA(activeCompany),
  })

  const handleSelectCompany = (comp: string) => {
    setActiveCompany(comp)
    setConfig({ company: comp })
  }

  return (
    <div className="pt-24 pb-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-8">
      {/* ── HEADER & COMPANY SWITCHER ────────────────────────────────────────── */}
      <div className="space-y-4">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-accent">
            Institutional Intelligence
          </span>
          <h1 className="text-3xl sm:text-4xl font-display font-bold text-text">
            Company DNA Explorer
          </h1>
          <p className="text-sm text-muted">
            Unpacking the 10-year hiring patterns, difficulty curves, and evaluation preferences.
          </p>
        </div>

        {/* Company Pills */}
        <div className="flex items-center space-x-2 overflow-x-auto pb-2 scrollbar-none">
          {COMPANIES.map((c) => {
            const isSelected = activeCompany === c
            return (
              <button
                key={c}
                onClick={() => handleSelectCompany(c)}
                className={`px-4 py-2 rounded-2xl text-xs font-semibold whitespace-nowrap transition-all duration-200 ${
                  isSelected
                    ? 'bg-accent text-white shadow-glow-violet scale-105'
                    : 'glass-card border border-border text-muted hover:text-text hover:border-accent/40'
                }`}
              >
                {c}
              </button>
            )
          })}
        </div>
      </div>

      {/* ── STATS ROW ───────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <GlassCard className="p-4 flex flex-col justify-between space-y-1">
          <div className="flex items-center justify-between text-muted">
            <span className="text-xs font-bold uppercase tracking-wider">Archive Size</span>
            <Building2 className="w-4 h-4 text-accent" />
          </div>
          <div className="text-2xl font-display font-bold text-text tabular-nums">
            {dna?.total_records ?? 220}
          </div>
          <span className="text-[11px] text-muted">Verified placement records</span>
        </GlassCard>

        <GlassCard className="p-4 flex flex-col justify-between space-y-1">
          <div className="flex items-center justify-between text-muted">
            <span className="text-xs font-bold uppercase tracking-wider">Historical Select</span>
            <Percent className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-display font-bold text-emerald-400 tabular-nums">
            {dna?.selection_rate ? `${dna.selection_rate.toFixed(1)}%` : '38.5%'}
          </div>
          <span className="text-[11px] text-muted">Selection conversion rate</span>
        </GlassCard>

        <GlassCard className="p-4 flex flex-col justify-between space-y-1">
          <div className="flex items-center justify-between text-muted">
            <span className="text-xs font-bold uppercase tracking-wider">Avg Difficulty</span>
            <TrendingUp className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-display font-bold text-text tabular-nums">
            {dna?.avg_difficulty ? `${dna.avg_difficulty.toFixed(1)} / 5.0` : '3.4 / 5.0'}
          </div>
          <span className="text-[11px] text-muted">10-year normalized mean</span>
        </GlassCard>

        <GlassCard className="p-4 flex flex-col justify-between space-y-1">
          <div className="flex items-center justify-between text-muted">
            <span className="text-xs font-bold uppercase tracking-wider">Core Focus</span>
            <Compass className="w-4 h-4 text-accent-cyan" />
          </div>
          <div className="text-xl font-display font-bold text-accent-cyan truncate">
            {dna ? Object.keys(dna.topic_distribution)[0] : 'DSA & Algorithms'}
          </div>
          <span className="text-[11px] text-muted">Primary testing area</span>
        </GlassCard>
      </div>

      {/* ── INTERVIEWER STYLE QUOTE CARD ───────────────────────────────────── */}
      <GlassCard className="p-6 sm:p-8 bg-gradient-to-r from-accent/10 via-white/5 to-accent-cyan/10 border border-accent/20">
        <div className="flex items-start space-x-4">
          <div className="w-10 h-10 rounded-2xl bg-accent/20 text-accent flex items-center justify-center flex-shrink-0 mt-1">
            <Quote className="w-5 h-5" />
          </div>
          <div className="space-y-2">
            <span className="text-xs font-bold uppercase tracking-wider text-accent">
              Interviewer Persona & Evaluation Mindset: {activeCompany}
            </span>
            <p className="text-sm sm:text-base text-text/90 italic font-medium leading-relaxed">
              "{dna?.interviewer_style_summary ||
                `${activeCompany} interviewers emphasize in-depth fundamentals, demanding hands-on implementation from scratch and penalizing superficial recall or unaddressed space complexity.`}"
            </p>
          </div>
        </div>
      </GlassCard>

      {/* ── CHARTS GRID ─────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Radar: Topic Distribution */}
        <GlassCard className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-display font-bold text-text">Topic Weight Distribution</h3>
              <p className="text-xs text-muted">Relative frequency across historical interviews</p>
            </div>
            <Sparkles className="w-4 h-4 text-accent" />
          </div>
          <TopicRadarChart
            data={
              dna?.topic_distribution || {
                DSA: 30,
                Aptitude: 22,
                Behavioral: 14,
                OOP: 12,
                DBMS: 9,
                OS: 6,
              }
            }
          />
        </GlassCard>

        {/* Area: Difficulty Trend by Year */}
        <GlassCard className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-display font-bold text-text">Difficulty Trend (2016 - 2025)</h3>
              <p className="text-xs text-muted">Year-over-year rigor calibration</p>
            </div>
            <TrendingUp className="w-4 h-4 text-accent-cyan" />
          </div>
          <DifficultyAreaChart
            data={
              dna?.difficulty_trend_by_year || {
                '2021': 3.1,
                '2022': 3.3,
                '2023': 3.5,
                '2024': 3.6,
                '2025': 3.7,
              }
            }
          />
        </GlassCard>

        {/* Donut: Round Type Breakdown */}
        <GlassCard className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-display font-bold text-text">Round Type Progression</h3>
              <p className="text-xs text-muted">Proportion of candidate elimination stages</p>
            </div>
            <Layers className="w-4 h-4 text-accent-magenta" />
          </div>
          <RoundDonutChart
            data={
              dna?.round_distribution || {
                Technical: 55,
                Aptitude: 25,
                HR: 15,
                Managerial: 5,
              }
            }
          />
        </GlassCard>

        {/* Bar: Top Rejection Traps */}
        <GlassCard className="p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-display font-bold text-text">Top Disqualification Reasons</h3>
              <p className="text-xs text-muted">Most common candidate rejection tags</p>
            </div>
            <AlertTriangle className="w-4 h-4 text-rose-400" />
          </div>
          <RejectionBarChart
            data={
              dna?.top_rejection_tags || [
                { tag: "couldn't optimise", count: 50 },
                { tag: 'weak OOP design', count: 48 },
                { tag: 'brute force only', count: 35 },
                { tag: 'weak complexity analysis', count: 26 },
              ]
            }
          />
        </GlassCard>
      </div>
    </div>
  )
}
