/**
 * Sidebar.tsx — icon sidebar with ARIA labels and accessible tooltips.
 */
import React from 'react'
import { NavLink } from 'react-router-dom'
import {
  Home,
  LayoutDashboard,
  PlayCircle,
  Dna,
  Lightbulb,
  FileCheck2,
  SlidersHorizontal,
} from 'lucide-react'

const NAV_ITEMS = [
  { to: '/',          label: 'Home',                  icon: Home,             shortcut: '' },
  { to: '/dashboard', label: 'Dashboard',             icon: LayoutDashboard,  shortcut: 'Alt+D' },
  { to: '/interview', label: 'Live Interview',        icon: PlayCircle,       shortcut: 'Alt+I' },
  { to: '/dna',       label: 'Company DNA',           icon: Dna,              shortcut: 'Alt+C' },
  { to: '/coaching',  label: 'Coaching & Evidence',  icon: Lightbulb,        shortcut: '' },
  { to: '/report',    label: 'Scorecard & Report',   icon: FileCheck2,       shortcut: 'Alt+R' },
  { to: '/setup',     label: 'Configure Session',     icon: SlidersHorizontal,shortcut: '' },
]

export const Sidebar: React.FC = () => {
  return (
    <aside
      className="fixed left-4 top-24 bottom-6 z-30 hidden md:flex flex-col items-center py-4 px-2 rounded-3xl glass-panel-elevated border border-[var(--border)] shadow-xl"
      aria-label="Site navigation"
    >
      <nav className="flex flex-col space-y-1.5" role="navigation">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              aria-label={item.label + (item.shortcut ? ` (${item.shortcut})` : '')}
              className={({ isActive }) =>
                `relative p-3 rounded-2xl flex items-center justify-center transition-all duration-200 group focus-visible:outline-none focus-visible:shadow-[var(--focus-ring)] ${
                  isActive
                    ? 'bg-accent text-white shadow-glow-violet scale-105'
                    : 'text-muted hover:text-text hover:bg-white/10'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <Icon className="w-5 h-5 transition-transform group-hover:scale-110" aria-hidden="true" />

                  {/* Active indicator pip */}
                  {isActive && (
                    <span className="absolute -left-1 top-1/2 -translate-y-1/2 w-1.5 h-5 bg-accent-cyan rounded-r-full" aria-hidden="true" />
                  )}

                  {/* Floating tooltip — elevated z-index above sidebar */}
                  <span
                    className="absolute left-14 z-50 px-2.5 py-1.5 rounded-xl glass-panel-elevated text-xs font-medium text-text opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity duration-150 whitespace-nowrap shadow-lg border border-[var(--border)]"
                    role="tooltip"
                  >
                    {item.label}
                    {item.shortcut && (
                      <span className="ml-2 text-muted text-[10px]">{item.shortcut}</span>
                    )}
                  </span>
                </>
              )}
            </NavLink>
          )
        })}
      </nav>

      {/* Divider */}
      <div className="w-8 h-px bg-[var(--border)] mt-auto mb-1" aria-hidden="true" />
    </aside>
  )
}
