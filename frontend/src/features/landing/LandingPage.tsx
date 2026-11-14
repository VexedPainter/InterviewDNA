import React from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { usePageTitle } from '../../hooks/usePageTitle'
import {
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Brain,
  Scale,
  Compass,
  FileSpreadsheet,
  CheckCircle2,
  ChevronRight,
  Database,
  Building,
  History,
} from 'lucide-react'
import { GlassCard } from '../../components/ui/GlassCard'
import { useQuery } from '@tanstack/react-query'
import { api } from '../../lib/api/client'

export const LandingPage: React.FC = () => {
  usePageTitle() // "InterviewDNA"
  const { data: companiesData } = useQuery({
    queryKey: ['companies'],
    queryFn: () => api.getCompanies(),
  })

  const companyCount = companiesData?.companies.length || 8

  return (
    <div className="relative pt-24 pb-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto space-y-32">
      {/* ── HERO SECTION ──────────────────────────────────────────────────────── */}
      <section className="relative text-center space-y-8 pt-8 lg:pt-16">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="inline-flex items-center space-x-2 px-4 py-1.5 rounded-full glass-panel border border-accent/30 text-xs sm:text-sm font-medium text-accent"
        >
          <Sparkles className="w-4 h-4 text-accent animate-pulse" />
          <span>Agentic RAG Engine Grounded in 10-Year Placement Archives</span>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.1 }}
          className="text-4xl sm:text-6xl lg:text-7xl font-display font-extrabold tracking-tight max-w-4xl mx-auto leading-[1.1]"
        >
          Interview like you've{' '}
          <span className="bg-gradient-to-r from-accent-violet via-accent to-accent-cyan bg-clip-text text-transparent">
            already been there.
          </span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.2 }}
          className="text-lg sm:text-xl text-muted max-w-2xl mx-auto leading-relaxed"
        >
          Not generic questions. InterviewDNA trains you against real company expectations,
          calibrated historical rubrics, and evidence-grounded coaching from 1,600+ real placements.
        </motion.p>

        {/* CTA Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4"
        >
          <Link
            to="/setup"
            className="w-full sm:w-auto inline-flex items-center justify-center px-8 py-4 rounded-2xl font-semibold text-white bg-gradient-to-r from-accent via-accent-violet to-accent-cyan shadow-glow-violet hover:opacity-95 hover:scale-[1.02] active:scale-95 transition-all text-base group"
          >
            <span>Start Mock Interview</span>
            <ArrowRight className="w-5 h-5 ml-2 transition-transform group-hover:translate-x-1" />
          </Link>
          <Link
            to="/dna"
            className="w-full sm:w-auto inline-flex items-center justify-center px-8 py-4 rounded-2xl font-semibold text-text glass-card border border-border hover:border-accent/40 hover:bg-white/5 transition-all text-base"
          >
            <span>Explore Company DNA</span>
          </Link>
        </motion.div>

        {/* Animated Metrics Bar */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.4 }}
          className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto pt-10"
        >
          {[
            { label: 'Years of Placement Data', value: '10 Years', icon: History },
            { label: 'Tier-1 Tech Companies', value: `${companyCount} Companies`, icon: Building },
            { label: 'Curated Archive Records', value: '1,600+ Records', icon: Database },
            { label: 'Specialized Agents', value: '4 Neural Agents', icon: Brain },
          ].map((stat, i) => {
            const Icon = stat.icon
            return (
              <GlassCard key={i} className="p-4 flex flex-col items-center justify-center text-center">
                <Icon className="w-5 h-5 text-accent mb-1.5 opacity-80" />
                <span className="text-xl sm:text-2xl font-display font-bold text-text tabular-nums">
                  {stat.value}
                </span>
                <span className="text-xs text-muted mt-0.5">{stat.label}</span>
              </GlassCard>
            )
          })}
        </motion.div>

        {/* 3D-Tilt Glass Hero Mockup */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 40 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          transition={{ duration: 0.9, delay: 0.5 }}
          className="pt-10 max-w-5xl mx-auto"
        >
          <div className="relative rounded-3xl p-1.5 bg-gradient-to-b from-white/20 via-white/5 to-transparent shadow-2xl hairline-border">
            <div className="glass-panel-elevated rounded-[22px] overflow-hidden p-6 sm:p-8 space-y-6 text-left border border-border/80">
              <div className="flex items-center justify-between border-b border-border/60 pb-4">
                <div className="flex items-center space-x-3">
                  <div className="w-3 h-3 rounded-full bg-rose-500/80" />
                  <div className="w-3 h-3 rounded-full bg-amber-500/80" />
                  <div className="w-3 h-3 rounded-full bg-emerald-500/80" />
                  <span className="text-xs text-muted ml-2 font-mono">session_live_interview.dna</span>
                </div>
                <div className="flex items-center space-x-2 text-xs font-semibold px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                  <span>Agentic RAG Active</span>
                </div>
              </div>

              <div className="grid md:grid-cols-3 gap-6">
                <div className="md:col-span-2 space-y-4">
                  <div className="p-4 rounded-2xl bg-white/5 border border-white/10 space-y-2">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-accent">
                      Interviewer Agent (Zoho • Technical Round)
                    </span>
                    <p className="text-sm sm:text-base font-medium text-text">
                      "Implement an in-place string compression algorithm in O(1) auxiliary space without using built-in methods."
                    </p>
                  </div>
                  <div className="p-4 rounded-2xl bg-accent/10 border border-accent/20 space-y-2">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-accent-cyan">
                      Candidate Response
                    </span>
                    <p className="text-xs sm:text-sm text-text/90">
                      "We can maintain a write index and a read pointer. Traverse consecutive character runs, update counts, and modify the buffer in O(N) time and O(1) space."
                    </p>
                  </div>
                </div>

                <div className="p-4 rounded-2xl bg-white/5 border border-white/10 flex flex-col justify-between space-y-3">
                  <div>
                    <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-400">
                      Evaluator Rubric Score
                    </span>
                    <div className="text-3xl font-display font-extrabold text-text mt-1">
                      8.7 <span className="text-xs text-muted font-normal">/ 10</span>
                    </div>
                  </div>
                  <div className="space-y-1.5 text-xs text-muted">
                    <div className="flex items-center text-emerald-400">
                      <CheckCircle2 className="w-3.5 h-3.5 mr-1.5 flex-shrink-0" />
                      <span>Two-pointer in-place verified</span>
                    </div>
                    <div className="flex items-center text-emerald-400">
                      <CheckCircle2 className="w-3.5 h-3.5 mr-1.5 flex-shrink-0" />
                      <span>O(1) space complexity matched</span>
                    </div>
                  </div>
                  <div className="pt-2 border-t border-border/60 text-[11px] text-muted font-mono">
                    Retrieved: 5 records • Fallback: None
                  </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </section>

      {/* ── 4 AGENTS FLOW DIAGRAM (ANIMATED) ─────────────────────────────────── */}
      <section className="space-y-12 text-center pt-10">
        <div className="space-y-3 max-w-2xl mx-auto">
          <span className="text-xs font-bold uppercase tracking-wider text-accent">
            Architecture
          </span>
          <h2 className="text-3xl sm:text-4xl font-display font-bold text-text">
            Four Autonomous Agents. One Cohesive Coach.
          </h2>
          <p className="text-muted text-sm sm:text-base">
            Every candidate answer flows through an intelligent pipeline designed to replicate
            the rigor and feedback loop of a real campus or corporate interview.
          </p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6 text-left">
          {[
            {
              step: '01',
              title: 'Interviewer Agent',
              role: 'Adaptive Questioner',
              desc: 'Selects company-specific questions, adapts difficulty up or down dynamically, and injects the company’s interviewer persona.',
              icon: Compass,
              accent: 'from-accent-violet to-accent',
            },
            {
              step: '02',
              title: 'Evaluator Agent',
              role: 'Multi-Criteria Rubric',
              desc: 'Scores Correctness (40%), Depth (35%), and Communication (25%) against archival expected points, detecting red flags.',
              icon: Scale,
              accent: 'from-accent to-accent-cyan',
            },
            {
              step: '03',
              title: 'Coach Agent',
              role: 'Evidence Grounding',
              desc: 'Synthesizes tailored feedback strictly grounded in real historical rejection patterns and citing verified record IDs.',
              icon: Brain,
              accent: 'from-accent-cyan to-emerald-400',
            },
            {
              step: '04',
              title: 'Report Agent',
              role: 'Actionable Roadmap',
              desc: 'Compares your scores against candidates actually selected by that company and compiles a 7-day targeted study roadmap.',
              icon: FileSpreadsheet,
              accent: 'from-emerald-400 to-accent-magenta',
            },
          ].map((agent, i) => {
            const Icon = agent.icon
            return (
              <GlassCard key={i} className="p-6 relative flex flex-col justify-between space-y-4 group">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono font-bold text-muted group-hover:text-accent transition-colors">
                      {agent.step}
                    </span>
                    <div className={`w-9 h-9 rounded-xl bg-gradient-to-tr ${agent.accent} flex items-center justify-center text-white shadow-md`}>
                      <Icon className="w-4 h-4" />
                    </div>
                  </div>
                  <div>
                    <h3 className="text-lg font-display font-bold text-text">{agent.title}</h3>
                    <p className="text-xs font-semibold text-accent mt-0.5">{agent.role}</p>
                  </div>
                  <p className="text-xs text-muted leading-relaxed">{agent.desc}</p>
                </div>

                <div className="pt-2 border-t border-border/40 flex items-center text-[11px] font-medium text-muted group-hover:text-text transition-colors">
                  <span>Explore agent specs</span>
                  <ChevronRight className="w-3.5 h-3.5 ml-1 transition-transform group-hover:translate-x-1" />
                </div>
              </GlassCard>
            )
          })}
        </div>
      </section>

      {/* ── FOOTER CALLOUT ─────────────────────────────────────────────────── */}
      <section className="glass-panel-elevated rounded-3xl p-8 sm:p-12 text-center space-y-6 relative overflow-hidden border border-accent/20">
        <div className="max-w-2xl mx-auto space-y-3">
          <h2 className="text-2xl sm:text-3xl font-display font-bold text-text">
            Ready to test your readiness for your dream company?
          </h2>
          <p className="text-sm text-muted">
            Configure your target company, role, and round mode in under 30 seconds.
          </p>
        </div>
        <Link
          to="/setup"
          className="inline-flex items-center justify-center px-8 py-3.5 rounded-2xl font-semibold text-white bg-gradient-to-r from-accent to-accent-cyan shadow-glow-violet hover:opacity-95 transition-all text-sm"
        >
          <span>Launch InterviewDNA Setup</span>
          <ArrowRight className="w-4 h-4 ml-2" />
        </Link>
      </section>
    </div>
  )
}
