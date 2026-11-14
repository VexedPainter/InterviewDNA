import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { usePageTitle } from '../../hooks/usePageTitle'
import {
  Building2,
  Briefcase,
  Layers,
  Sliders,
  ArrowRight,
  ArrowLeft,
  Check,
  Search,
  Timer,
  Sparkles,
} from 'lucide-react'
import { GlassCard } from '../../components/ui/GlassCard'
import { useSessionStore } from '../../store/sessionStore'
import { useQuery } from '@tanstack/react-query'
import { api } from '../../lib/api/client'

const COMPANY_COLORS: Record<string, string> = {
  Zoho: 'from-amber-500 to-red-500',
  Amazon: 'from-amber-400 to-orange-500',
  Google: 'from-blue-500 via-red-500 to-green-500',
  TCS: 'from-blue-600 to-cyan-500',
  Infosys: 'from-blue-500 to-indigo-600',
  Accenture: 'from-purple-600 to-pink-500',
  Deloitte: 'from-emerald-500 to-teal-600',
  Flipkart: 'from-yellow-400 to-blue-500',
}

const ROUND_MODES = ['Aptitude', 'Technical', 'Managerial', 'HR']

export const SetupWizard: React.FC = () => {
  usePageTitle('Setup — Configure your session')
  const navigate = useNavigate()
  const {
    nickname,
    company,
    role,
    roundMode,
    difficultyMode,
    pressureMode,
    pressureSeconds,
    setNickname,
    setConfig,
    startSession,
    setProcessing,
  } = useSessionStore()

  const [currentStep, setCurrentStep] = useState(1)
  const [searchQuery, setSearchQuery] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const { data: companiesData, isLoading } = useQuery({
    queryKey: ['companies'],
    queryFn: () => api.getCompanies(),
  })

  const companies = companiesData?.companies || [
    'Zoho', 'Amazon', 'Google', 'TCS', 'Infosys', 'Accenture', 'Deloitte', 'Flipkart'
  ]

  const availableRoles = companiesData?.roles[company] || [
    'Software Developer', 'Member Technical Staff', 'UI Developer', 'DevOps Engineer'
  ]

  const filteredCompanies = companies.filter((c) =>
    c.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const handleCreateSession = async () => {
    setIsSubmitting(true)
    setProcessing(true)
    try {
      const resp = await api.createSession({
        nickname: nickname.trim() || 'Student',
        company,
        role,
        round_mode: roundMode,
        difficulty_mode: difficultyMode,
        pressure_mode: pressureMode,
      })
      startSession(resp.session_id, resp.first_question)
      navigate('/interview')
    } catch (err) {
      console.error('Failed to create session:', err)
      alert('Could not connect to API server. Please make sure FastAPI backend is running on port 8000.')
    } finally {
      setIsSubmitting(false)
      setProcessing(false)
    }
  }

  const steps = [
    { num: 1, title: 'Company', icon: Building2 },
    { num: 2, title: 'Target Role', icon: Briefcase },
    { num: 3, title: 'Round Type', icon: Layers },
    { num: 4, title: 'Parameters', icon: Sliders },
  ]

  return (
    <div className="pt-24 pb-16 px-4 sm:px-6 lg:px-8 max-w-4xl mx-auto space-y-10">
      {/* Step Header & Progress */}
      <div className="text-center space-y-3">
        <span className="text-xs font-bold uppercase tracking-wider text-accent">
          Interview Configuration
        </span>
        <h1 className="text-3xl sm:text-4xl font-display font-bold text-text">
          Personalize Your Mock Simulation
        </h1>
        <p className="text-sm text-muted max-w-md mx-auto">
          Tailor questions to the exact company archive and testing parameters.
        </p>

        {/* Morphing Step Bar */}
        <div className="flex items-center justify-center space-x-3 pt-6 max-w-sm mx-auto">
          {steps.map((s) => {
            const isCompleted = s.num < currentStep
            const isCurrent = s.num === currentStep
            return (
              <div key={s.num} className="flex items-center flex-1">
                <button
                  onClick={() => s.num < currentStep && setCurrentStep(s.num)}
                  disabled={s.num > currentStep}
                  className={`w-9 h-9 rounded-full flex items-center justify-center font-display font-bold text-xs transition-all duration-300 ${
                    isCurrent
                      ? 'bg-accent text-white shadow-glow-violet scale-110'
                      : isCompleted
                      ? 'bg-emerald-500 text-white'
                      : 'bg-white/10 text-muted border border-border'
                  }`}
                >
                  {isCompleted ? <Check className="w-4 h-4" /> : s.num}
                </button>
                {s.num < steps.length && (
                  <div
                    className={`h-[2px] flex-1 mx-2 transition-colors duration-300 ${
                      s.num < currentStep ? 'bg-emerald-500' : 'bg-border'
                    }`}
                  />
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* Step Content Container */}
      <GlassCard className="p-6 sm:p-10 border border-border/80 shadow-2xl relative min-h-[420px] flex flex-col justify-between">
        <AnimatePresence mode="wait">
          {/* ── STEP 1: COMPANY ─────────────────────────────────────────── */}
          {currentStep === 1 && (
            <motion.div
              key="step-1"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-6"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <h2 className="text-xl font-display font-bold text-text">Select Target Company</h2>
                  <p className="text-xs text-muted">Retrieves curated archive distributions for this firm.</p>
                </div>
                <div className="relative w-full sm:w-64">
                  <Search className="w-4 h-4 text-muted absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    placeholder="Search company..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-9 pr-3 py-2 rounded-xl text-xs bg-white/5 border border-border text-text placeholder-muted focus:outline-none focus:border-accent"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                {filteredCompanies.map((c) => {
                  const isSelected = company === c
                  const grad = COMPANY_COLORS[c] || 'from-accent to-accent-cyan'
                  return (
                    <button
                      key={c}
                      onClick={() => setConfig({ company: c })}
                      className={`relative p-5 rounded-2xl glass-card flex flex-col items-center justify-center space-y-3 transition-all duration-200 group text-center ${
                        isSelected
                          ? 'border-accent shadow-glow-violet scale-[1.02] bg-accent/10'
                          : 'hover:border-accent/40 hover:-translate-y-1'
                      }`}
                    >
                      <div
                        className={`w-12 h-12 rounded-2xl bg-gradient-to-tr ${grad} flex items-center justify-center text-white font-display font-extrabold text-lg shadow-md group-hover:scale-105 transition-transform`}
                      >
                        {c.charAt(0)}
                      </div>
                      <span className="text-sm font-semibold text-text">{c}</span>
                      {isSelected && (
                        <div className="absolute top-2 right-2 w-5 h-5 rounded-full bg-accent text-white flex items-center justify-center">
                          <Check className="w-3 h-3" />
                        </div>
                      )}
                    </button>
                  )
                })}
              </div>
            </motion.div>
          )}

          {/* ── STEP 2: ROLE ────────────────────────────────────────────── */}
          {currentStep === 2 && (
            <motion.div
              key="step-2"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-6"
            >
              <div>
                <h2 className="text-xl font-display font-bold text-text">Choose Target Role at {company}</h2>
                <p className="text-xs text-muted">Aligns question sets and difficulty curves to this job specification.</p>
              </div>

              <div className="grid sm:grid-cols-2 gap-3.5">
                {availableRoles.map((r) => {
                  const isSelected = role === r
                  return (
                    <button
                      key={r}
                      onClick={() => setConfig({ role: r })}
                      className={`p-4 rounded-2xl glass-card flex items-center justify-between transition-all duration-200 text-left ${
                        isSelected
                          ? 'border-accent bg-accent/10 shadow-glow-violet'
                          : 'hover:border-accent/30'
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 rounded-xl bg-white/10 flex items-center justify-center text-text font-bold text-xs">
                          <Briefcase className="w-4 h-4 text-accent" />
                        </div>
                        <span className="text-sm font-semibold text-text">{r}</span>
                      </div>
                      {isSelected && <Check className="w-4 h-4 text-accent" />}
                    </button>
                  )
                })}
              </div>
            </motion.div>
          )}

          {/* ── STEP 3: ROUND MODE ──────────────────────────────────────── */}
          {currentStep === 3 && (
            <motion.div
              key="step-3"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-6"
            >
              <div>
                <h2 className="text-xl font-display font-bold text-text">Interview Round Mode</h2>
                <p className="text-xs text-muted">Pick the stage of the recruitment process you wish to simulate.</p>
              </div>

              <div className="grid sm:grid-cols-2 gap-4">
                {ROUND_MODES.map((rm) => {
                  const isSelected = roundMode === rm
                  const descs: Record<string, string> = {
                    Aptitude: 'Quantitative reasoning, probability, logical deduction, and pattern logic.',
                    Technical: 'Data structures, algorithms, system design, DBMS, and OOP implementation.',
                    Managerial: 'Behavioral scenarios, STAR methodology, leadership, and conflict resolution.',
                    HR: 'Company culture fit, career aspirations, salary expectations, and integrity probes.',
                  }
                  return (
                    <button
                      key={rm}
                      onClick={() => setConfig({ roundMode: rm })}
                      className={`p-5 rounded-2xl glass-card flex flex-col justify-between space-y-2 transition-all duration-200 text-left ${
                        isSelected
                          ? 'border-accent bg-accent/10 shadow-glow-violet'
                          : 'hover:border-accent/30'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-base font-display font-bold text-text">{rm} Round</span>
                        {isSelected && <Check className="w-4 h-4 text-accent" />}
                      </div>
                      <p className="text-xs text-muted leading-relaxed">{descs[rm]}</p>
                    </button>
                  )
                })}
              </div>
            </motion.div>
          )}

          {/* ── STEP 4: PARAMETERS ──────────────────────────────────────── */}
          {currentStep === 4 && (
            <motion.div
              key="step-4"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="space-y-6"
            >
              <div>
                <h2 className="text-xl font-display font-bold text-text">Testing Parameters & Pressure Mode</h2>
                <p className="text-xs text-muted">Customize session rigor and personal identifiers.</p>
              </div>

              <div className="grid sm:grid-cols-2 gap-6">
                {/* Candidate Nickname */}
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-text uppercase tracking-wider">Candidate Nickname</label>
                  <input
                    type="text"
                    value={nickname}
                    onChange={(e) => setNickname(e.target.value)}
                    placeholder="Enter your name or alias..."
                    className="w-full px-4 py-2.5 rounded-xl glass-card border border-border text-text placeholder-muted text-sm focus:outline-none focus:border-accent"
                  />
                  <span className="text-[11px] text-muted block">Used to track progress history in SQLite.</span>
                </div>

                {/* Difficulty Level Slider */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-semibold text-text uppercase tracking-wider">
                      Initial Difficulty: {difficultyMode} / 5
                    </label>
                    <span className="text-xs text-accent font-semibold">
                      {difficultyMode <= 2 ? 'Foundational' : difficultyMode <= 4 ? 'Intermediate' : 'Hardcore'}
                    </span>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="5"
                    value={difficultyMode}
                    onChange={(e) => setConfig({ difficultyMode: parseInt(e.target.value) })}
                    className="w-full accent-accent cursor-pointer"
                  />
                  <div className="flex justify-between text-[10px] text-muted font-mono">
                    <span>1 (Easy)</span>
                    <span>3 (Standard)</span>
                    <span>5 (Challenging)</span>
                  </div>
                </div>

                {/* Pressure Mode Toggle */}
                <div className="sm:col-span-2 p-4 rounded-2xl glass-card border border-border flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 rounded-xl bg-amber-500/10 flex items-center justify-center text-amber-400">
                      <Timer className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="text-sm font-semibold text-text">Simulated Pressure Timer</span>
                        <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-400 border border-amber-500/30">
                          {pressureMode ? 'Active' : 'Off'}
                        </span>
                      </div>
                      <p className="text-xs text-muted">
                        Adds a countdown timer (shifts green → amber → red) with pulse effects.
                      </p>
                    </div>
                  </div>

                  <button
                    onClick={() => setConfig({ pressureMode: !pressureMode })}
                    className={`w-12 h-6 rounded-full p-0.5 transition-colors duration-200 ${
                      pressureMode ? 'bg-accent' : 'bg-white/20'
                    }`}
                  >
                    <div
                      className={`w-5 h-5 rounded-full bg-white transition-transform duration-200 ${
                        pressureMode ? 'translate-x-6' : 'translate-x-0'
                      }`}
                    />
                  </button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Wizard Controls */}
        <div className="flex items-center justify-between pt-8 border-t border-border/60">
          <button
            onClick={() => setCurrentStep((prev) => Math.max(prev - 1, 1))}
            disabled={currentStep === 1 || isSubmitting}
            className="inline-flex items-center px-4 py-2 rounded-xl text-xs font-semibold text-text hover:bg-white/10 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          >
            <ArrowLeft className="w-4 h-4 mr-1.5" />
            <span>Previous</span>
          </button>

          {currentStep < 4 ? (
            <button
              onClick={() => setCurrentStep((prev) => Math.min(prev + 1, 4))}
              className="inline-flex items-center px-6 py-2.5 rounded-xl text-xs font-semibold text-white bg-accent hover:opacity-90 active:scale-95 transition-all shadow-glow-violet"
            >
              <span>Continue</span>
              <ArrowRight className="w-4 h-4 ml-1.5" />
            </button>
          ) : (
            <button
              onClick={handleCreateSession}
              disabled={isSubmitting}
              className="inline-flex items-center px-7 py-3 rounded-xl text-sm font-semibold text-white bg-gradient-to-r from-accent to-accent-cyan hover:opacity-95 active:scale-95 transition-all shadow-glow-violet disabled:opacity-50"
            >
              <Sparkles className="w-4 h-4 mr-2" />
              <span>{isSubmitting ? 'Initializing Agents...' : 'Start Mock Interview'}</span>
            </button>
          )}
        </div>
      </GlassCard>
    </div>
  )
}
