/**
 * OnboardingTour.tsx — first-visit 3-step spotlight tour.
 *
 * Uses a full-screen overlay with a spotlight cutout (box-shadow trick)
 * that animates to highlight three anchor elements in sequence.
 * Stored completion state in localStorage so it only fires once.
 */
import React, { useState, useEffect, useCallback } from 'react'
import { createPortal } from 'react-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { ArrowRight, X } from 'lucide-react'

const TOUR_KEY = 'interviewdna-tour-done'

interface Step {
  targetId: string
  title: string
  body: string
  position: 'top' | 'bottom' | 'left' | 'right'
}

const STEPS: Step[] = [
  {
    targetId: 'nav-logo',
    title: '👋 Welcome to InterviewDNA',
    body: 'An Agentic RAG system trained on 10 years of real placement data. Click the logo any time to return home.',
    position: 'bottom',
  },
  {
    targetId: 'nav-start-session',
    title: '🚀 Start a Mock Interview',
    body: 'Pick your target company, role, and round mode. The system will tailor questions from the historical archive.',
    position: 'bottom',
  },
  {
    targetId: 'nav-theme-toggle',
    title: '🎨 Theme Toggle',
    body: 'Switch between dark and light mode with a full-screen circular reveal animation.',
    position: 'bottom',
  },
]

function getRect(id: string): DOMRect | null {
  return document.getElementById(id)?.getBoundingClientRect() ?? null
}

export const OnboardingTour: React.FC = () => {
  const [step, setStep] = useState<number | null>(null)
  const [rect, setRect] = useState<DOMRect | null>(null)

  useEffect(() => {
    if (localStorage.getItem(TOUR_KEY)) return
    // Start tour after a brief delay so the page has painted
    const t = setTimeout(() => setStep(0), 1200)
    return () => clearTimeout(t)
  }, [])

  useEffect(() => {
    if (step === null) return
    const id = STEPS[step]?.targetId
    if (!id) return
    setRect(getRect(id))
  }, [step])

  const advance = useCallback(() => {
    if (step === null) return
    if (step >= STEPS.length - 1) {
      localStorage.setItem(TOUR_KEY, '1')
      setStep(null)
      return
    }
    setStep(step + 1)
  }, [step])

  const dismiss = useCallback(() => {
    localStorage.setItem(TOUR_KEY, '1')
    setStep(null)
  }, [])

  if (step === null || !rect) return null

  const PAD = 10
  const spotX = rect.left - PAD
  const spotY = rect.top - PAD
  const spotW = rect.width + PAD * 2
  const spotH = rect.height + PAD * 2

  // Tooltip placement: below by default
  const tooltipLeft = Math.max(12, Math.min(rect.left, window.innerWidth - 320))
  const tooltipTop = rect.bottom + 16

  const current = STEPS[step]

  return createPortal(
    <AnimatePresence>
      <motion.div
        key={`tour-${step}`}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.25 }}
        className="fixed inset-0 z-[200] pointer-events-none"
        style={{
          boxShadow: `0 0 0 9999px rgba(0,0,0,0.65)`,
          clipPath: `polygon(
            0% 0%, 100% 0%, 100% 100%, 0% 100%,
            0% ${spotY}px,
            ${spotX}px ${spotY}px,
            ${spotX}px ${spotY + spotH}px,
            ${spotX + spotW}px ${spotY + spotH}px,
            ${spotX + spotW}px ${spotY}px,
            0% ${spotY}px
          )`,
        }}
      />

      {/* Tooltip */}
      <motion.div
        key={`tooltip-${step}`}
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
        className="fixed z-[201] w-72 glass-panel-elevated rounded-2xl p-5 shadow-2xl border border-accent/30"
        style={{ left: tooltipLeft, top: tooltipTop, pointerEvents: 'all' }}
      >
        <div className="flex items-start justify-between mb-2">
          <h3 className="font-display font-bold text-text text-sm leading-snug">{current.title}</h3>
          <button onClick={dismiss} className="text-muted hover:text-text transition-colors ml-2 flex-shrink-0">
            <X className="w-4 h-4" />
          </button>
        </div>
        <p className="text-xs text-muted leading-relaxed mb-4">{current.body}</p>
        <div className="flex items-center justify-between">
          {/* Step dots */}
          <div className="flex gap-1.5">
            {STEPS.map((_, i) => (
              <span
                key={i}
                className={`w-1.5 h-1.5 rounded-full transition-colors ${
                  i === step ? 'bg-accent' : 'bg-border'
                }`}
              />
            ))}
          </div>
          <button
            onClick={advance}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-accent text-white text-xs font-semibold hover:opacity-90 transition-all"
          >
            {step < STEPS.length - 1 ? (
              <>Next <ArrowRight className="w-3 h-3" /></>
            ) : (
              'Got it ✓'
            )}
          </button>
        </div>
      </motion.div>
    </AnimatePresence>,
    document.body
  )
}
