import React, { useState, useEffect } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Sparkles, Command } from 'lucide-react'
import { ThemeToggle } from '../ui/ThemeToggle'
import { LogoMark } from '../ui/LogoMark'
import { useSessionStore } from '../../store/sessionStore'
import { useKeyboardShortcut } from '../../hooks/useKeyboardShortcut'

export const Navbar: React.FC = () => {
  const [scrolled, setScrolled] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()
  const { company, role } = useSessionStore()

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  // Alt+* nav shortcuts
  useKeyboardShortcut({ key: 'd', alt: true }, () => navigate('/dashboard'))
  useKeyboardShortcut({ key: 'i', alt: true }, () => navigate('/interview'))
  useKeyboardShortcut({ key: 'c', alt: true }, () => navigate('/dna'))
  useKeyboardShortcut({ key: 'r', alt: true }, () => navigate('/report'))
  // Alt+T -> theme toggle dispatched via ThemeToggle's own handler
  useKeyboardShortcut({ key: 't', alt: true }, () => {
    const btn = document.getElementById('nav-theme-toggle')?.querySelector('button')
    btn?.click()
  })

  const isInterview = location.pathname === '/interview'

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-40 transition-all duration-300 ${
        scrolled
          ? 'glass-panel-elevated py-3 border-b border-[var(--border)] shadow-lg'
          : 'bg-transparent py-4 border-b border-transparent'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between gap-3">
        {/* Brand Logo */}
        <Link
          id="nav-logo"
          to="/"
          className="flex items-center space-x-3 group flex-shrink-0"
          aria-label="InterviewDNA home"
        >
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-accent-violet via-accent to-accent-cyan flex items-center justify-center shadow-glow-violet group-hover:scale-105 transition-transform duration-200 overflow-hidden">
            <LogoMark size={32} />
          </div>
          <div className="hidden sm:block">
            <div className="flex items-center space-x-1.5">
              <span className="font-display font-bold text-xl tracking-tight text-text">
                InterviewDNA
              </span>
              <span className="text-[10px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded-full bg-accent/15 text-accent border border-accent/20 select-none">
                Agentic
              </span>
            </div>
            <p className="text-[11px] text-muted leading-none mt-0.5">
              10-Year Historical Placement Intelligence
            </p>
          </div>
        </Link>

        {/* Current Company Indicator & Command Trigger */}
        <div className="hidden md:flex items-center space-x-2 min-w-0 flex-1 justify-center">
          <Link
            to="/dna"
            className="flex items-center space-x-2 px-3 py-1.5 rounded-full glass-card border border-[var(--border)] text-xs font-medium hover:border-accent/40 transition-all min-w-0 max-w-[280px]"
            title="Active target context — click to explore Company DNA"
          >
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping flex-shrink-0" aria-hidden="true" />
            <span className="text-muted flex-shrink-0">Target:</span>
            <span className="text-text font-semibold truncate max-w-[80px]" title={company}>{company}</span>
            <span className="text-muted/60 flex-shrink-0">•</span>
            <span className="text-muted truncate max-w-[100px]" title={role}>{role}</span>
          </Link>

          <button
            onClick={() => {
              window.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', ctrlKey: true }))
            }}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-full glass-card border border-[var(--border)] text-xs text-muted hover:text-text hover:border-accent/40 transition-all flex-shrink-0"
            aria-label="Open command palette (Ctrl+K)"
          >
            <Command className="w-3.5 h-3.5" aria-hidden="true" />
            <span className="hidden lg:inline">Search</span>
            <kbd className="px-1.5 py-0.5 rounded bg-white/10 text-[10px] font-mono">⌘K</kbd>
          </button>
        </div>

        {/* Right Actions */}
        <div className="flex items-center space-x-2 flex-shrink-0">
          <div id="nav-theme-toggle">
            <ThemeToggle />
          </div>

          {!isInterview && (
            <Link
              id="nav-start-session"
              to="/setup"
              className="relative inline-flex items-center justify-center px-4 py-2 text-xs sm:text-sm font-semibold text-white rounded-full bg-gradient-to-r from-accent to-accent-cyan shadow-glow-violet hover:opacity-95 hover:scale-[1.02] active:scale-95 transition-all duration-200"
              aria-label="Start a new interview session"
            >
              <Sparkles className="w-4 h-4 mr-1.5" aria-hidden="true" />
              <span>Start Session</span>
            </Link>
          )}
        </div>
      </div>
    </header>
  )
}
