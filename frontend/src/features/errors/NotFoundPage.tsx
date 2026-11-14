/**
 * NotFoundPage.tsx — 404 screen with animated DNA logo and nav links.
 */
import React from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Home, ArrowLeft, Search } from 'lucide-react'
import { GlassCard } from '../../components/ui/GlassCard'
import { LogoMark } from '../../components/ui/LogoMark'
import { usePageTitle } from '../../hooks/usePageTitle'
import { listContainer, listItem } from '../../lib/motion'

export const NotFoundPage: React.FC = () => {
  usePageTitle('404 — Page Not Found')

  return (
    <div className="min-h-screen flex items-center justify-center px-4 pt-20">
      <motion.div
        className="text-center space-y-8 max-w-lg w-full"
        variants={listContainer}
        initial="initial"
        animate="animate"
      >
        {/* Animated Logo */}
        <motion.div variants={listItem} className="flex justify-center">
          <div className="w-20 h-20 rounded-3xl bg-gradient-to-tr from-accent-violet via-accent to-accent-cyan flex items-center justify-center shadow-glow-violet">
            <LogoMark size={48} />
          </div>
        </motion.div>

        {/* 404 Heading */}
        <motion.div variants={listItem} className="space-y-3">
          <span className="text-8xl font-display font-extrabold tracking-tighter bg-gradient-to-r from-accent-violet via-accent to-accent-cyan bg-clip-text text-transparent">
            404
          </span>
          <h1 className="text-2xl font-display font-bold text-text">
            This page doesn't exist in the archive.
          </h1>
          <p className="text-muted text-sm leading-relaxed">
            Our 10-year placement database is thorough — but this route isn't in it.
            Let's get you back on track.
          </p>
        </motion.div>

        {/* Action Cards */}
        <motion.div variants={listItem} className="grid sm:grid-cols-3 gap-3">
          {[
            { to: '/', icon: Home, label: 'Home', desc: 'Back to landing' },
            { to: '/setup', icon: Search, label: 'Start Session', desc: 'Begin interview' },
            { to: '/dashboard', icon: ArrowLeft, label: 'Dashboard', desc: 'Your progress' },
          ].map(({ to, icon: Icon, label, desc }) => (
            <Link key={to} to={to}>
              <GlassCard className="p-4 flex flex-col items-center text-center space-y-2 cursor-pointer hover:border-accent/40 transition-all">
                <div className="w-9 h-9 rounded-xl bg-accent/10 flex items-center justify-center">
                  <Icon className="w-4 h-4 text-accent" />
                </div>
                <span className="text-sm font-semibold text-text">{label}</span>
                <span className="text-xs text-muted">{desc}</span>
              </GlassCard>
            </Link>
          ))}
        </motion.div>
      </motion.div>
    </div>
  )
}
