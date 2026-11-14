import React from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { usePageTitle } from '../../hooks/usePageTitle'
import {
  Sparkles,
  PlayCircle,
  Dna,
  History,
  TrendingUp,
  AlertTriangle,
  Award,
  ArrowRight,
  Flame,
  CheckCircle2,
} from 'lucide-react'
import { GlassCard } from '../../components/ui/GlassCard'
import { Gauge } from '../../components/ui/Gauge'
import { TopicRadarChart } from '../../components/charts/TopicRadarChart'
import { useSessionStore } from '../../store/sessionStore'
import { useQuery } from '@tanstack/react-query'
import { api } from '../../lib/api/client'

export const DashboardPage: React.FC = () => {
  usePageTitle('Dashboard')
  const { nickname, company, role } = useSessionStore()

  const { data: progressData } = useQuery({
    queryKey: ['progress', nickname],
    queryFn: () => api.getUserProgress(nickname),
  })

  const { data: dnaData } = useQuery({
    queryKey: ['dna', company, role],
    queryFn: () => api.getCompanyDNA(company, role),
  })

  const sessions = progressData?.sessions || []
  const completedSessions = sessions.filter((s) => s.status === 'COMPLETED' || s.overall_score > 0)
  const avgScore = completedSessions.length
    ? completedSessions.reduce((acc, s) => acc + s.overall_score, 0) / completedSessions.length
    : 7.2

  const readinessPercent = Math.min(Math.round((avgScore / 10) * 100), 100)

  // Top rejection tags as weak areas
  const weakTopics = dnaData?.top_rejection_tags.slice(0, 3) || [
    { tag: "Couldn't optimise time complexity", count: 42 },
    { tag: 'Weak OOP interface abstraction', count: 35 },
    { tag: 'Superficial DBMS index reasoning', count: 28 },
  ]

  return (
    <div className="pt-24 pb-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-8">
      {/* ── HEADER ──────────────────────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl sm:text-3xl font-display font-bold text-text">
              Welcome back, {nickname || 'Candidate'}
            </h1>
            <span className="text-xl">👋</span>
          </div>
          <p className="text-sm text-muted">
            Targeting <span className="text-text font-semibold">{company}</span> ({role})
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <Link
            to="/dna"
            className="inline-flex items-center px-4 py-2 rounded-xl text-xs font-semibold glass-card border border-border text-text hover:border-accent/40 transition-all"
          >
            <Dna className="w-4 h-4 mr-1.5 text-accent" />
            <span>View {company} DNA</span>
          </Link>
          <Link
            to="/setup"
            className="inline-flex items-center px-5 py-2.5 rounded-xl text-xs font-semibold text-white bg-gradient-to-r from-accent to-accent-cyan shadow-glow-violet hover:opacity-95 active:scale-95 transition-all"
          >
            <PlayCircle className="w-4 h-4 mr-1.5" />
            <span>Launch Mock Interview</span>
          </Link>
        </div>
      </div>

      {/* ── BENTO GRID ──────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">
        {/* Tile 1: Readiness Score Ring */}
        <GlassCard className="p-6 flex flex-col justify-between space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-muted">
              Readiness Score
            </span>
            <Award className="w-4 h-4 text-accent" />
          </div>

          <div className="flex items-center justify-center py-2">
            <Gauge
              value={avgScore}
              max={10}
              label={`${readinessPercent}% Ready`}
              sublabel={`Calibrated for ${company}`}
              size={130}
              strokeWidth={10}
              color={avgScore >= 7.5 ? '#10b981' : avgScore >= 5.5 ? '#f59e0b' : '#ef4444'}
            />
          </div>

          <div className="pt-2 border-t border-border/50 text-[11px] text-muted text-center">
            Based on {completedSessions.length} evaluated session{completedSessions.length === 1 ? '' : 's'}
          </div>
        </GlassCard>

        {/* Tile 2: Practice Streak & Heatmap */}
        <GlassCard className="p-6 flex flex-col justify-between space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-muted">
              Consistency Streak
            </span>
            <div className="flex items-center text-amber-400 text-xs font-bold">
              <Flame className="w-4 h-4 mr-1 fill-amber-400" />
              <span>3 Days</span>
            </div>
          </div>

          <div className="space-y-3">
            <div className="text-2xl font-display font-extrabold text-text">
              12 Practice Turns
            </div>
            <p className="text-xs text-muted">Weekly commitment heatmap</p>

            {/* Micro 4-Week Activity Heatmap */}
            <div className="grid grid-cols-7 gap-1.5 pt-1">
              {Array.from({ length: 28 }).map((_, i) => {
                const active = [3, 4, 10, 11, 12, 18, 19, 25, 26, 27].includes(i)
                return (
                  <div
                    key={i}
                    title={`Day ${i + 1}`}
                    className={`h-4 rounded-md transition-colors ${
                      active ? 'bg-accent shadow-sm' : 'bg-white/5 border border-white/5'
                    }`}
                  />
                )
              })}
            </div>
          </div>

          <div className="pt-2 border-t border-border/50 text-[11px] text-muted flex items-center justify-between">
            <span>Keep streak alive</span>
            <span className="text-emerald-400 font-semibold">+15% retention</span>
          </div>
        </GlassCard>

        {/* Tile 3 & 4 (Span 2 cols): Company DNA Mini-Radar */}
        <GlassCard className="md:col-span-1 lg:col-span-2 p-6 flex flex-col justify-between space-y-2">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-accent">
                {company} DNA Profile
              </span>
              <h3 className="text-base font-display font-bold text-text">
                Topic Distribution Radar
              </h3>
            </div>
            <Link to="/dna" className="text-xs text-muted hover:text-accent flex items-center">
              <span>Full View</span>
              <ArrowRight className="w-3.5 h-3.5 ml-1" />
            </Link>
          </div>

          <div className="h-60">
            <TopicRadarChart
              data={
                dnaData?.topic_distribution || {
                  DSA: 35,
                  DBMS: 20,
                  OOP: 18,
                  Aptitude: 15,
                  OS: 12,
                }
              }
            />
          </div>
        </GlassCard>

        {/* Tile 5 (Span 2 cols): Weakest Topics & Critical Rejection Traps */}
        <GlassCard className="md:col-span-1 lg:col-span-2 p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-rose-400" />
              <span className="text-xs font-bold uppercase tracking-wider text-rose-400">
                Top Rejection Traps at {company}
              </span>
            </div>
            <span className="text-xs text-muted">From Archive</span>
          </div>

          <div className="space-y-3">
            {weakTopics.map((item, i) => (
              <div
                key={i}
                className="p-3 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-between hover:border-rose-500/30 transition-colors"
              >
                <div className="flex items-center space-x-3">
                  <div className="w-6 h-6 rounded-lg bg-rose-500/15 text-rose-400 flex items-center justify-center font-bold text-xs">
                    {i + 1}
                  </div>
                  <span className="text-xs sm:text-sm font-medium text-text">{item.tag}</span>
                </div>
                <span className="text-xs font-mono font-semibold text-rose-400 bg-rose-500/10 px-2.5 py-0.5 rounded-full">
                  {item.count} rejects
                </span>
              </div>
            ))}
          </div>

          <div className="pt-2">
            <Link
              to="/coaching"
              className="text-xs font-semibold text-accent hover:underline flex items-center justify-end"
            >
              <span>Review grounded coaching advice for these traps</span>
              <ArrowRight className="w-3.5 h-3.5 ml-1" />
            </Link>
          </div>
        </GlassCard>

        {/* Tile 6 (Span 2 cols): Recent Evaluation Sessions */}
        <GlassCard className="md:col-span-2 lg:col-span-2 p-6 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <History className="w-4 h-4 text-accent" />
              <span className="text-xs font-bold uppercase tracking-wider text-text">
                Recent Session History
              </span>
            </div>
            <Link to="/report" className="text-xs text-muted hover:text-accent">
              View latest report
            </Link>
          </div>

          {sessions.length === 0 ? (
            <div className="py-8 text-center text-xs text-muted space-y-2">
              <p>No past sessions recorded yet under nickname "{nickname}".</p>
              <Link
                to="/setup"
                className="inline-block text-accent font-semibold hover:underline"
              >
                Start your first interview session →
              </Link>
            </div>
          ) : (
            <div className="space-y-2.5">
              {sessions.slice(0, 3).map((sess, idx) => (
                <div
                  key={idx}
                  className="p-3.5 rounded-2xl glass-card flex items-center justify-between hover:border-accent/40 transition-all text-xs"
                >
                  <div className="space-y-0.5">
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold text-text">{sess.company}</span>
                      <span className="text-muted/60">•</span>
                      <span className="text-muted">{sess.round_type}</span>
                    </div>
                    <span className="text-[11px] text-muted">
                      {new Date(sess.created_at).toLocaleDateString()}
                    </span>
                  </div>

                  <div className="flex items-center space-x-3">
                    <span
                      className={`font-display font-bold text-sm tabular-nums ${
                        sess.overall_score >= 7.5
                          ? 'text-emerald-400'
                          : sess.overall_score >= 5.5
                          ? 'text-amber-400'
                          : 'text-rose-400'
                      }`}
                    >
                      {sess.overall_score > 0 ? `${sess.overall_score.toFixed(1)}/10` : 'In Progress'}
                    </span>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-white/10 text-muted">
                      {sess.final_verdict || sess.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </GlassCard>
      </div>
    </div>
  )
}
