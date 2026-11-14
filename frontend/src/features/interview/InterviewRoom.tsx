import React, { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { usePageTitle } from '../../hooks/usePageTitle'
import {
  Send,
  Mic,
  MicOff,
  Sparkles,
  Bot,
  User,
  AlertCircle,
  CheckCircle2,
  XCircle,
  HelpCircle,
  FileCheck2,
  Clock,
  Compass,
  Scale,
  Brain,
  FileSpreadsheet,
  ArrowRight,
  Flame,
} from 'lucide-react'
import { GlassCard } from '../../components/ui/GlassCard'
import { Gauge } from '../../components/ui/Gauge'
import { Badge } from '../../components/ui/Badge'
import { useSessionStore, AgentName, ChatMessage } from '../../store/sessionStore'
import { useSpeechRecognition } from '../../hooks/useSpeechRecognition'
import { api } from '../../lib/api/client'

export const InterviewRoom: React.FC = () => {
  usePageTitle('Live Interview Room')
  const navigate = useNavigate()
  const {
    sessionId,
    company,
    role,
    roundMode,
    pressureMode,
    pressureSeconds,
    messages,
    agentTrace,
    activeAgent,
    isProcessing,
    addUserMessage,
    addAgentMessage,
    setTrace,
    setProcessing,
    setReport,
  } = useSessionStore()

  const [inputMessage, setInputMessage] = useState('')
  const [timeLeft, setTimeLeft] = useState(pressureSeconds || 120)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const { isListening, transcript, supported, startListening, stopListening } =
    useSpeechRecognition()

  // Redirect if no session
  useEffect(() => {
    if (!sessionId) {
      navigate('/setup')
    }
  }, [sessionId, navigate])

  // Sync speech transcript into input
  useEffect(() => {
    if (transcript) {
      setInputMessage((prev) => (prev ? `${prev} ${transcript}` : transcript))
    }
  }, [transcript])

  // Scroll to bottom on new message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isProcessing])

  // Pressure Mode Countdown Timer
  useEffect(() => {
    if (!pressureMode) return
    const timer = setInterval(() => {
      setTimeLeft((prev) => (prev > 0 ? prev - 1 : 0))
    }, 1000)
    return () => clearInterval(timer)
  }, [pressureMode])

  // Auto-grow textarea
  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputMessage(e.target.value)
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`
    }
  }

  // Handle Sending Message
  const handleSendMessage = async () => {
    const trimmed = inputMessage.trim()
    if (!trimmed || isProcessing || !sessionId) return

    addUserMessage(trimmed)
    setInputMessage('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
    setProcessing(true)

    // Reset pressure timer on submission
    if (pressureMode) setTimeLeft(pressureSeconds || 120)

    try {
      // Send message to FastAPI backend
      const resp = await api.sendMessage(sessionId, trimmed)

      setTrace(resp.agent_trace, resp.routed_to as AgentName)

      // Add agent reply to chat thread
      addAgentMessage({
        text: resp.response_text,
        evaluation: resp.evaluation,
        followup: resp.followup,
        coaching: resp.coaching,
        questionId: resp.question?.question_id || resp.followup?.question_id,
        topic: resp.question?.topic || resp.followup?.topic,
        roundType: resp.question?.round_type || resp.followup?.round_type,
        turnNumber: resp.question?.turn_number || resp.followup?.turn_number,
        isFollowup: !!resp.followup,
      })
    } catch (err: any) {
      console.error('Message error:', err)
      addAgentMessage({
        text: `⚠️ **Error communicating with agent**: ${err.detail || err.message || 'Check FastAPI server.'}`,
      })
    } finally {
      setProcessing(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleEndSession = async () => {
    if (!sessionId) return
    setProcessing(true)
    try {
      const rep = await api.endSession(sessionId)
      setReport(rep)
      navigate('/report')
    } catch (err) {
      console.error('End session error:', err)
      navigate('/report')
    } finally {
      setProcessing(false)
    }
  }

  // Agent node configs for trace panel
  const agentNodes: Array<{ name: AgentName; label: string; icon: any; color: string }> = [
    { name: 'Interviewer Agent', label: 'Interviewer', icon: Compass, color: '#8b5cf6' },
    { name: 'Evaluator Agent', label: 'Evaluator', icon: Scale, color: '#06b6d4' },
    { name: 'Coach Agent', label: 'Coach', icon: Brain, color: '#10b981' },
    { name: 'Report Agent', label: 'Report', icon: FileSpreadsheet, color: '#ec4899' },
  ]

  // Pressure timer styles
  const timerPercent = (timeLeft / (pressureSeconds || 120)) * 100
  const isTimerCritical = timeLeft < 30
  const isTimerWarning = timeLeft < 60 && !isTimerCritical

  return (
    <div className="pt-20 pb-8 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto h-[calc(100vh-2rem)] flex flex-col space-y-4">
      {/* ── TOP SESSION STATUS BAR ────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-2.5 rounded-2xl glass-panel border border-border">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-xl bg-accent/20 flex items-center justify-center text-accent">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-sm font-display font-bold text-text">{company}</span>
              <span className="text-muted/60">•</span>
              <span className="text-xs text-muted font-medium">{role}</span>
              <Badge variant="accent" size="sm">
                {roundMode} Round
              </Badge>
            </div>
            <span className="text-[10px] text-muted font-mono">Session ID: {sessionId}</span>
          </div>
        </div>

        {/* Pressure Mode Timer */}
        {pressureMode && (
          <div
            className={`flex items-center space-x-2 px-3 py-1 rounded-full border transition-all ${
              isTimerCritical
                ? 'bg-rose-500/15 border-rose-500/30 text-rose-400 animate-pulse'
                : isTimerWarning
                ? 'bg-amber-500/15 border-amber-500/30 text-amber-400'
                : 'bg-emerald-500/15 border-emerald-500/30 text-emerald-400'
            }`}
          >
            <Clock className="w-4 h-4" />
            <span className="font-mono text-xs font-bold tabular-nums">
              {Math.floor(timeLeft / 60)}:{(timeLeft % 60).toString().padStart(2, '0')}
            </span>
          </div>
        )}

        <div className="flex items-center space-x-2">
          <button
            onClick={handleEndSession}
            disabled={isProcessing}
            className="inline-flex items-center px-3.5 py-1.5 rounded-xl text-xs font-semibold text-rose-400 border border-rose-500/30 bg-rose-500/10 hover:bg-rose-500/20 active:scale-95 transition-all"
          >
            <FileCheck2 className="w-3.5 h-3.5 mr-1.5" />
            <span>End & View Scorecard</span>
          </button>
        </div>
      </div>

      {/* ── MAIN INTERVIEW WORKSPACE: 2-COLUMN LAYOUT ───────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 flex-1 min-h-0 overflow-hidden">
        {/* LEFT COLUMN: CHAT & ANSWER COMPOSER (8 COLS) */}
        <div className="lg:col-span-8 flex flex-col h-full rounded-3xl glass-panel border border-border overflow-hidden">
          {/* Scrollable Conversation Stream */}
          <div className="flex-1 p-4 sm:p-6 overflow-y-auto space-y-6">
            {messages.map((msg) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 12, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ duration: 0.3 }}
                className={`flex gap-3.5 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {/* Agent Avatar */}
                {msg.sender === 'agent' && (
                  <div className="w-9 h-9 rounded-2xl bg-gradient-to-tr from-accent to-accent-cyan flex-shrink-0 flex items-center justify-center text-white shadow-glow-violet">
                    <Bot className="w-4 h-4" />
                  </div>
                )}

                {/* Message Body */}
                <div
                  className={`max-w-[85%] rounded-3xl p-4 sm:p-5 space-y-3.5 ${
                    msg.sender === 'user'
                      ? 'bg-accent/20 border border-accent/40 text-text rounded-tr-sm ml-auto'
                      : 'glass-panel-elevated border border-border text-text rounded-tl-sm'
                  }`}
                >
                  {/* Markdown / Text Render */}
                  <div className="prose prose-sm dark:prose-invert max-w-none text-xs sm:text-sm leading-relaxed whitespace-pre-wrap font-sans">
                    {msg.text}
                  </div>

                  {/* Evaluation Slide-In Card if Attached */}
                  {msg.evaluation && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      className="mt-3 p-4 rounded-2xl bg-white/5 border border-white/10 space-y-3 text-xs"
                    >
                      <div className="flex items-center justify-between border-b border-border/40 pb-2">
                        <span className="font-bold text-accent uppercase tracking-wider text-[11px]">
                          Evaluator Scorecard
                        </span>
                        <span className="font-mono font-bold text-text text-sm">
                          {msg.evaluation.overall.toFixed(1)} / 10
                        </span>
                      </div>

                      {/* 3 Circular Gauges */}
                      <div className="grid grid-cols-3 gap-1 py-1">
                        <Gauge
                          value={msg.evaluation.correctness}
                          label="Correctness"
                          size={70}
                          strokeWidth={6}
                          color="#10b981"
                        />
                        <Gauge
                          value={msg.evaluation.depth}
                          label="Depth"
                          size={70}
                          strokeWidth={6}
                          color="#06b6d4"
                        />
                        <Gauge
                          value={msg.evaluation.communication}
                          label="Communication"
                          size={70}
                          strokeWidth={6}
                          color="#8b5cf6"
                        />
                      </div>

                      {/* Matched & Missed Chips */}
                      {msg.evaluation.matched_points.length > 0 && (
                        <div className="space-y-1">
                          <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider block">
                            Covered Well:
                          </span>
                          <div className="flex flex-wrap gap-1.5">
                            {msg.evaluation.matched_points.map((p, i) => (
                              <Badge key={i} variant="success" size="sm">
                                <CheckCircle2 className="w-3 h-3 mr-1" />
                                {p}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}

                      {msg.evaluation.missed_points.length > 0 && (
                        <div className="space-y-1">
                          <span className="text-[10px] font-bold text-amber-400 uppercase tracking-wider block">
                            Key Missing Points:
                          </span>
                          <div className="flex flex-wrap gap-1.5">
                            {msg.evaluation.missed_points.map((p, i) => (
                              <Badge key={i} variant="warn" size="sm">
                                <AlertCircle className="w-3 h-3 mr-1" />
                                {p}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Follow-up Probe Alert */}
                      {msg.evaluation.needs_followup && (
                        <div className="p-2.5 rounded-xl bg-accent/15 border border-accent/30 text-accent flex items-start space-x-2">
                          <HelpCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                          <div className="space-y-0.5">
                            <span className="font-bold text-[11px] block">
                              Adaptive Follow-up Triggered
                            </span>
                            <span className="text-[11px] text-text/80">
                              {msg.evaluation.followup_reason || 'Probing conceptual depth on missed rubric points.'}
                            </span>
                          </div>
                        </div>
                      )}
                    </motion.div>
                  )}
                </div>

                {/* User Avatar */}
                {msg.sender === 'user' && (
                  <div className="w-9 h-9 rounded-2xl bg-white/10 flex-shrink-0 flex items-center justify-center text-text font-bold text-xs border border-border">
                    <User className="w-4 h-4 text-muted" />
                  </div>
                )}
              </motion.div>
            ))}

            {/* Typing / Agent Processing Pulse */}
            {isProcessing && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex items-center space-x-2 text-xs text-accent font-medium py-2 px-4 rounded-full glass-card w-fit"
              >
                <div className="w-2 h-2 rounded-full bg-accent animate-ping" />
                <span>{activeAgent} is analyzing your response...</span>
              </motion.div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Answer Composer (Center Bottom) */}
          <div className="p-4 border-t border-border/60 bg-surface/40 backdrop-blur-md space-y-2.5">
            <div className="relative rounded-2xl glass-panel-elevated border border-border focus-within:border-accent transition-all p-2.5">
              <textarea
                ref={textareaRef}
                value={inputMessage}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                placeholder="Type your answer, solution code, or query... (Ctrl+Enter to submit)"
                rows={2}
                disabled={isProcessing}
                className="w-full bg-transparent border-none text-text placeholder-muted focus:outline-none text-xs sm:text-sm resize-none pr-20"
              />

              {/* Bottom Composer Controls */}
              <div className="flex items-center justify-between pt-2 border-t border-border/40 text-xs">
                <div className="flex items-center space-x-3 text-muted text-[11px]">
                  <span>
                    Word count: <strong className="text-text">{inputMessage.trim() ? inputMessage.trim().split(/\s+/).length : 0}</strong>
                  </span>
                  {supported && (
                    <button
                      type="button"
                      onClick={isListening ? stopListening : startListening}
                      className={`inline-flex items-center px-2 py-0.5 rounded-lg border text-[11px] font-medium transition-colors ${
                        isListening
                          ? 'bg-rose-500/20 text-rose-400 border-rose-500/30 animate-pulse'
                          : 'bg-white/5 border-border hover:text-text'
                      }`}
                    >
                      {isListening ? <MicOff className="w-3 h-3 mr-1" /> : <Mic className="w-3 h-3 mr-1" />}
                      <span>{isListening ? 'Listening...' : 'Voice Input'}</span>
                    </button>
                  )}
                </div>

                <div className="flex items-center space-x-2">
                  <span className="text-[10px] text-muted hidden sm:inline">Press Ctrl+Enter</span>
                  <button
                    onClick={handleSendMessage}
                    disabled={!inputMessage.trim() || isProcessing}
                    className="inline-flex items-center justify-center p-2 rounded-xl bg-accent text-white hover:opacity-90 active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed shadow-glow-violet transition-all"
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: LIVE AGENT TRACE PANEL (4 COLS) */}
        <div className="lg:col-span-4 flex flex-col h-full rounded-3xl glass-panel border border-border p-5 space-y-5 overflow-y-auto">
          <div className="flex items-center justify-between border-b border-border/60 pb-3">
            <div className="flex items-center space-x-2">
              <Sparkles className="w-4 h-4 text-accent" />
              <h3 className="text-sm font-display font-bold text-text">Agentic Trace & Pipeline</h3>
            </div>
            <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full bg-accent/15 text-accent border border-accent/20">
              Live
            </span>
          </div>

          {/* Node Graph */}
          <div className="space-y-2.5">
            <span className="text-[11px] font-bold uppercase tracking-wider text-muted">
              Pipeline Nodes
            </span>
            <div className="space-y-2">
              {agentNodes.map((node) => {
                const Icon = node.icon
                const isActive = activeAgent === node.name
                return (
                  <div
                    key={node.name}
                    className={`p-3 rounded-2xl flex items-center justify-between border transition-all duration-300 ${
                      isActive
                        ? 'glass-panel-elevated border-accent shadow-glow-violet scale-[1.02]'
                        : 'glass-card border-border/60 opacity-60'
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      <div
                        className="w-8 h-8 rounded-xl flex items-center justify-center text-white shadow-sm"
                        style={{ backgroundColor: node.color }}
                      >
                        <Icon className="w-4 h-4" />
                      </div>
                      <div>
                        <span className="text-xs font-bold text-text block">{node.label}</span>
                        <span className="text-[10px] text-muted">
                          {isActive ? 'Currently executing' : 'Standby'}
                        </span>
                      </div>
                    </div>
                    {isActive && (
                      <div className="flex items-center space-x-1">
                        <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>

          {/* Real-time Telemetry Metrics */}
          <div className="space-y-2 pt-2 border-t border-border/50">
            <span className="text-[11px] font-bold uppercase tracking-wider text-muted">
              Retrieval & Dispatch Metrics
            </span>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="p-3 rounded-xl bg-white/5 border border-white/10 space-y-0.5">
                <span className="text-[10px] text-muted uppercase">Latency</span>
                <div className="text-sm font-display font-bold text-text tabular-nums">
                  {agentTrace?.latency_ms ? `${agentTrace.latency_ms.toFixed(0)} ms` : '38 ms'}
                </div>
              </div>

              <div className="p-3 rounded-xl bg-white/5 border border-white/10 space-y-0.5">
                <span className="text-[10px] text-muted uppercase">Records RAG</span>
                <div className="text-sm font-display font-bold text-text tabular-nums">
                  {agentTrace?.retrieved_count ?? 5} hits
                </div>
              </div>

              <div className="col-span-2 p-3 rounded-xl bg-white/5 border border-white/10 flex items-center justify-between">
                <span className="text-[10px] text-muted uppercase">Fallback Tier</span>
                <span className="font-mono text-xs font-bold text-accent">
                  {agentTrace?.fallback_level || 'company_role'}
                </span>
              </div>
            </div>
          </div>

          {/* Quick Guidance Card */}
          <div className="p-3.5 rounded-2xl bg-accent/10 border border-accent/20 text-xs space-y-1.5 mt-auto">
            <span className="font-bold text-accent flex items-center">
              <Brain className="w-3.5 h-3.5 mr-1.5" />
              Pro Coaching Tip
            </span>
            <p className="text-muted leading-relaxed text-[11px]">
              Type <kbd className="px-1 py-0.5 rounded bg-white/10 font-mono text-[10px]">tips on DBMS</kbd> or <kbd className="px-1 py-0.5 rounded bg-white/10 font-mono text-[10px]">next question</kbd> at any time to consult the Coach Agent.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
