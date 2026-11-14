import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Search,
  LayoutDashboard,
  PlayCircle,
  Dna,
  Lightbulb,
  FileText,
  Sliders,
  Moon,
  Sun,
  Building2,
  X,
} from 'lucide-react'
import { useThemeStore } from '../../store/themeStore'
import { useSessionStore } from '../../store/sessionStore'

const COMPANIES = ['Zoho', 'Amazon', 'Google', 'TCS', 'Infosys', 'Accenture', 'Deloitte', 'Flipkart']

export const CommandPalette: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false)
  const [query, setQuery] = useState('')
  const navigate = useNavigate()
  const { theme, toggleTheme } = useThemeStore()
  const { setConfig } = useSessionStore()

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        setIsOpen((prev) => !prev)
      } else if (e.key === 'Escape' && isOpen) {
        setIsOpen(false)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen])

  const handleAction = (callback: () => void) => {
    callback()
    setIsOpen(false)
    setQuery('')
  }

  const navItems = [
    { label: 'Go to Dashboard', icon: LayoutDashboard, action: () => navigate('/dashboard') },
    { label: 'Start Mock Interview', icon: PlayCircle, action: () => navigate('/interview') },
    { label: 'Explore Company DNA', icon: Dna, action: () => navigate('/dna') },
    { label: 'Grounded Coaching & Evidence', icon: Lightbulb, action: () => navigate('/coaching') },
    { label: 'Post-Interview Scorecard', icon: FileText, action: () => navigate('/report') },
    { label: 'Configure Session Setup', icon: Sliders, action: () => navigate('/setup') },
    { label: `Toggle Theme (${theme === 'dark' ? 'Light' : 'Dark'})`, icon: theme === 'dark' ? Sun : Moon, action: () => toggleTheme() },
  ]

  const filteredNav = navItems.filter((i) => i.label.toLowerCase().includes(query.toLowerCase()))
  const filteredCompanies = COMPANIES.filter((c) => c.toLowerCase().includes(query.toLowerCase()))

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-24 px-4 bg-black/60 backdrop-blur-sm">
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: -20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -20 }}
            transition={{ duration: 0.15 }}
            className="w-full max-w-xl glass-panel-elevated rounded-2xl overflow-hidden shadow-2xl border border-border"
          >
            {/* Search Input Bar */}
            <div className="flex items-center px-4 py-3.5 border-b border-border/80">
              <Search className="w-5 h-5 text-muted mr-3" />
              <input
                type="text"
                autoFocus
                placeholder="Type a command, page, or company name... (Esc to close)"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="w-full bg-transparent border-none text-text placeholder-muted focus:outline-none text-base font-medium"
              />
              <button
                onClick={() => setIsOpen(false)}
                className="p-1 rounded-lg text-muted hover:text-text hover:bg-white/10"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Command Results */}
            <div className="max-h-80 overflow-y-auto p-2 space-y-1">
              <div className="text-[11px] font-semibold text-muted uppercase tracking-wider px-3 py-1.5">
                Quick Navigation
              </div>
              {filteredNav.map((item, idx) => {
                const Icon = item.icon
                return (
                  <button
                    key={idx}
                    onClick={() => handleAction(item.action)}
                    className="w-full flex items-center px-3 py-2.5 rounded-xl text-sm font-medium text-text hover:bg-accent/15 hover:text-accent transition-colors text-left group"
                  >
                    <Icon className="w-4 h-4 mr-3 text-muted group-hover:text-accent" />
                    {item.label}
                  </button>
                )
              })}

              <div className="text-[11px] font-semibold text-muted uppercase tracking-wider px-3 pt-3 py-1.5">
                Switch Target Company
              </div>
              <div className="grid grid-cols-2 gap-1 px-1">
                {filteredCompanies.map((comp) => (
                  <button
                    key={comp}
                    onClick={() =>
                      handleAction(() => {
                        setConfig({ company: comp })
                        navigate('/dashboard')
                      })
                    }
                    className="flex items-center px-3 py-2 rounded-xl text-xs font-medium text-text hover:bg-accent/15 hover:text-accent transition-colors text-left group"
                  >
                    <Building2 className="w-3.5 h-3.5 mr-2 text-muted group-hover:text-accent" />
                    {comp}
                  </button>
                ))}
              </div>
            </div>

            <div className="px-4 py-2 border-t border-border/60 bg-surface/40 flex items-center justify-between text-xs text-muted">
              <span>ProTip: Press <kbd className="px-1.5 py-0.5 rounded bg-white/10 border border-white/20">Ctrl</kbd> + <kbd className="px-1.5 py-0.5 rounded bg-white/10 border border-white/20">K</kbd> anywhere</span>
              <span>InterviewDNA v1.0</span>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  )
}
