/**
 * Footer.tsx — global site footer with credits.
 */
import React from 'react'
import { Link } from 'react-router-dom'
import { Heart, Github, Dna } from 'lucide-react'

export const Footer: React.FC = () => {
  const year = new Date().getFullYear()

  return (
    <footer className="relative mt-auto py-8 px-4 sm:px-6 border-t border-border/40">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-muted">
        {/* Brand */}
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-lg bg-gradient-to-tr from-accent-violet to-accent-cyan flex items-center justify-center">
            <Dna className="w-3.5 h-3.5 text-white" />
          </div>
          <span className="font-semibold text-text">InterviewDNA</span>
          <span className="text-muted/60">© {year}</span>
        </div>

        {/* Nav links */}
        <nav className="flex items-center gap-4" aria-label="Footer navigation">
          {[
            { to: '/', label: 'Home' },
            { to: '/setup', label: 'Start' },
            { to: '/dna', label: 'Company DNA' },
            { to: '/dashboard', label: 'Dashboard' },
          ].map(({ to, label }) => (
            <Link
              key={to}
              to={to}
              className="hover:text-text transition-colors"
            >
              {label}
            </Link>
          ))}
        </nav>

        {/* Credits */}
        <div className="flex items-center gap-1.5">
          <span>Built with</span>
          <Heart className="w-3 h-3 text-accent-magenta fill-accent-magenta" />
          <span>using React, FastAPI &amp; LangChain</span>
        </div>
      </div>

      {/* Acknowledgements */}
      <p className="text-center text-[11px] text-muted/50 mt-4">
        Academic project — data is synthetic and anonymised. Grounded in a 10-year institutional placement archive.
        Powered by Google Gemini (via LangChain) · ChromaDB · SQLite · Vite.
      </p>
    </footer>
  )
}
