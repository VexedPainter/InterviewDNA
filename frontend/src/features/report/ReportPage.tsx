import React, { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import confetti from 'canvas-confetti'
import { usePageTitle } from '../../hooks/usePageTitle'
import {
  FileCheck2,
  Download,
  Calendar,
  CheckCircle2,
  AlertCircle,
  TrendingUp,
  Award,
  Sparkles,
  ArrowRight,
  RefreshCw,
} from 'lucide-react'
import { GlassCard } from '../../components/ui/GlassCard'
import { Badge } from '../../components/ui/Badge'
import { BenchmarkBarChart } from '../../components/charts/BenchmarkBarChart'
import { useSessionStore } from '../../store/sessionStore'
import { api } from '../../lib/api/client'

export const ReportPage: React.FC = () => {
  usePageTitle('Session Report')
  const { sessionId, company, role, latestReport } = useSessionStore()

  // Use latest report from store or sensible fallback for demo
  const report = latestReport || {
    session_id: sessionId || 'demo_session',
    company: company || 'Zoho',
    role: role || 'Software Developer',
    verdict: 'Selected Ready',
    final_verdict: 'Selected Ready',
    trend: 'upward',
    averages: {
      correctness: 8.6,
      depth: 8.2,
      communication: 8.8,
      overall: 8.5,
    },
    top_strengths: [
      'Two-pointer optimal memory manipulation',
      'Clear articulation of time vs space trade-offs',
      'Proactive edge case discussion',
    ],
    top_gaps: [
      'Detailed index tree depths in PostgreSQL',
      'System design scaling bounds',
    ],
    improvement_plan: [
      'Day 1: Implement iterative 2-pointer algorithms on LeetCode Medium.',
      'Day 2: Review B-Tree index scan depths and explain to a peer.',
      'Day 3: Practice STAR format on 3 challenging conflict scenarios.',
      'Day 4: Study system design caching strategies (Redis vs Memcached).',
      'Day 5: Solve 5 concurrency questions covering semaphores and mutexes.',
      'Day 6: Complete a full mock interview under strict 45-min timer.',
      'Day 7: Rest and conduct light review of Company DNA profile.',
    ],
    benchmark_comparison: {
      company: company || 'Zoho',
      role: role || 'Software Developer',
      avg_score_selected: 7.8,
      sample_size: 42,
    },
  }

  const overallScore = report.averages.overall || 8.5
  const benchmarkScore = report.benchmark_comparison?.avg_score_selected || 7.8
  const isSelected = overallScore >= benchmarkScore

  // Trigger confetti burst if candidate beats the benchmark!
  useEffect(() => {
    if (isSelected) {
      confetti({
        particleCount: 80,
        spread: 70,
        origin: { y: 0.6 },
        colors: ['#8b5cf6', '#06b6d4', '#ec4899', '#10b981'],
      })
    }
  }, [isSelected])

  const downloadPdf = () => {
    if (sessionId) {
      window.open(api.getReportPdfUrl(sessionId), '_blank')
    } else {
      alert('Session ID not active.')
    }
  }

  const downloadMd = () => {
    if (sessionId) {
      window.open(api.getReportMdUrl(sessionId), '_blank')
    } else {
      alert('Session ID not active.')
    }
  }

  return (
    <div className="pt-24 pb-16 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-8">
      {/* ── HEADER ──────────────────────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-accent">
            Comprehensive Evaluation Scorecard
          </span>
          <h1 className="text-3xl sm:text-4xl font-display font-bold text-text">
            Interview Performance Report
          </h1>
          <p className="text-sm text-muted">
            Calibrated for <strong className="text-text">{report.company}</strong> ({report.role})
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={downloadMd}
            className="inline-flex items-center px-4 py-2 rounded-xl text-xs font-semibold glass-card border border-border text-text hover:border-accent/40 transition-all"
          >
            <Download className="w-3.5 h-3.5 mr-1.5" />
            <span>Export Markdown</span>
          </button>
          <button
            onClick={downloadPdf}
            className="inline-flex items-center px-5 py-2.5 rounded-xl text-xs font-semibold text-white bg-gradient-to-r from-accent to-accent-cyan shadow-glow-violet hover:opacity-95 active:scale-95 transition-all"
          >
            <FileCheck2 className="w-4 h-4 mr-1.5" />
            <span>Download Official PDF</span>
          </button>
        </div>
      </div>

      {/* ── VERDICT BANNER ──────────────────────────────────────────────────── */}
      <GlassCard className="p-6 sm:p-8 bg-gradient-to-r from-accent/15 via-white/5 to-accent-cyan/15 border border-accent/30 relative overflow-hidden">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <Award className="w-6 h-6 text-emerald-400" />
              <span className="text-xs font-bold uppercase tracking-wider text-emerald-400">
                Evaluation Outcome
              </span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-display font-bold text-text">
              {report.final_verdict || report.verdict || 'Selected Ready'}
            </h2>
            <p className="text-xs sm:text-sm text-muted">
              {isSelected
                ? `Congratulations! Your score of ${overallScore.toFixed(1)}/10 surpasses the average for candidates selected by ${report.company} (${benchmarkScore.toFixed(1)}/10).`
                : `Solid effort. Follow the targeted 7-day roadmap below to push your score over the ${report.company} selection bar.`}
            </p>
          </div>

          <div className="flex items-center space-x-4 bg-white/5 p-4 rounded-2xl border border-white/10">
            <div className="text-center">
              <span className="text-[10px] text-muted uppercase font-bold">Overall Score</span>
              <div className="text-2xl sm:text-3xl font-display font-extrabold text-text tabular-nums">
                {overallScore.toFixed(1)}
              </div>
            </div>
            <div className="w-[1px] h-10 bg-border" />
            <div className="text-center">
              <span className="text-[10px] text-muted uppercase font-bold">Selected Benchmark</span>
              <div className="text-2xl sm:text-3xl font-display font-extrabold text-accent-cyan tabular-nums">
                {benchmarkScore.toFixed(1)}
              </div>
            </div>
          </div>
        </div>
      </GlassCard>

      {/* ── 2-COLUMN ANALYSIS GRID ─────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Benchmark Comparison Chart (7 Cols) */}
        <div className="lg:col-span-7">
          <GlassCard className="p-6 space-y-4 h-full flex flex-col justify-between">
            <div>
              <h3 className="text-base font-display font-bold text-text">
                Metric Comparison vs Selected Candidates
              </h3>
              <p className="text-xs text-muted">
                Your performance alongside verified placements at {report.company}
              </p>
            </div>

            <BenchmarkBarChart
              userScores={{
                correctness: report.averages.correctness || 8.6,
                depth: report.averages.depth || 8.2,
                communication: report.averages.communication || 8.8,
                overall: overallScore,
              }}
              benchmarkAvg={benchmarkScore}
            />
          </GlassCard>
        </div>

        {/* Right: Strengths & Gaps (5 Cols) */}
        <div className="lg:col-span-5 space-y-6">
          {/* Top Strengths */}
          <GlassCard className="p-6 space-y-3">
            <div className="flex items-center space-x-2 text-emerald-400">
              <CheckCircle2 className="w-4 h-4" />
              <h3 className="text-xs font-bold uppercase tracking-wider">Top Evaluated Strengths</h3>
            </div>
            <div className="space-y-2">
              {(report.top_strengths || report.strengths || []).map((s, i) => (
                <div
                  key={i}
                  className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs font-medium text-text flex items-start space-x-2"
                >
                  <span className="text-emerald-400 font-bold">•</span>
                  <span>{s}</span>
                </div>
              ))}
            </div>
          </GlassCard>

          {/* Key Technical Gaps */}
          <GlassCard className="p-6 space-y-3">
            <div className="flex items-center space-x-2 text-amber-400">
              <AlertCircle className="w-4 h-4" />
              <h3 className="text-xs font-bold uppercase tracking-wider">Key Growth Areas</h3>
            </div>
            <div className="space-y-2">
              {(report.top_gaps || report.gaps || []).map((g, i) => (
                <div
                  key={i}
                  className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs font-medium text-text flex items-start space-x-2"
                >
                  <span className="text-amber-400 font-bold">•</span>
                  <span>{g}</span>
                </div>
              ))}
            </div>
          </GlassCard>
        </div>
      </div>

      {/* ── 7-DAY IMPROVEMENT ROADMAP ──────────────────────────────────────── */}
      <GlassCard className="p-6 sm:p-8 space-y-6">
        <div className="flex items-center justify-between border-b border-border/60 pb-3">
          <div className="flex items-center space-x-2">
            <Calendar className="w-5 h-5 text-accent" />
            <h3 className="text-base font-display font-bold text-text">
              Personalized 7-Day Actionable Study Plan
            </h3>
          </div>
          <span className="text-xs text-muted font-medium">Daily incremental syllabus</span>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {report.improvement_plan.map((dayPlan, idx) => (
            <div
              key={idx}
              className="p-4 rounded-2xl glass-card flex flex-col justify-between space-y-3 border border-border/70 hover:border-accent/40 transition-colors"
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold font-mono text-accent">DAY {idx + 1}</span>
                <Sparkles className="w-3.5 h-3.5 text-muted" />
              </div>
              <p className="text-xs text-text/90 leading-relaxed font-medium">
                {dayPlan.replace(/^Day \d+:\s*/i, '')}
              </p>
            </div>
          ))}
        </div>
      </GlassCard>

      {/* ── RETEST CTA ──────────────────────────────────────────────────────── */}
      <div className="text-center pt-4">
        <Link
          to="/setup"
          className="inline-flex items-center px-8 py-3.5 rounded-2xl font-semibold text-white bg-gradient-to-r from-accent to-accent-cyan shadow-glow-violet hover:opacity-95 active:scale-95 transition-all text-sm"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          <span>Start Another Interview Session</span>
        </Link>
      </div>
    </div>
  )
}
