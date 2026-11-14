/**
 * KeyboardCheatSheet.tsx — press "?" to open/close the shortcut overlay.
 */
import React, { useState, useCallback } from 'react'
import { createPortal } from 'react-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Keyboard } from 'lucide-react'
import { useKeyboardShortcut } from '../../hooks/useKeyboardShortcut'
import { scalePop } from '../../lib/motion'

const SHORTCUTS = [
  { keys: ['?'], description: 'Open keyboard shortcuts' },
  { keys: ['Ctrl', 'K'], description: 'Open command palette' },
  { keys: ['Ctrl', 'Enter'], description: 'Send interview answer' },
  { keys: ['Esc'], description: 'Close dialogs / cancel' },
  { keys: ['Alt', 'T'], description: 'Toggle dark / light theme' },
  { keys: ['Alt', 'D'], description: 'Go to Dashboard' },
  { keys: ['Alt', 'I'], description: 'Go to Interview room' },
  { keys: ['Alt', 'C'], description: 'Go to Company DNA' },
  { keys: ['Alt', 'R'], description: 'Go to Report' },
]

function Kbd({ k }: { k: string }) {
  return (
    <kbd className="inline-flex items-center justify-center px-2 py-0.5 rounded-md border border-border bg-white/10 text-[11px] font-mono font-semibold text-muted">
      {k}
    </kbd>
  )
}

export const KeyboardCheatSheet: React.FC = () => {
  const [open, setOpen] = useState(false)

  const toggle = useCallback(() => setOpen((v) => !v), [])
  const close = useCallback(() => setOpen(false), [])

  useKeyboardShortcut({ key: '?' }, toggle)
  useKeyboardShortcut({ key: 'Escape' }, close)

  return createPortal(
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            key="backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.18 }}
            className="fixed inset-0 z-[150] bg-black/50 backdrop-blur-sm"
            onClick={close}
          />

          {/* Sheet */}
          <motion.div
            key="sheet"
            variants={scalePop}
            initial="initial"
            animate="animate"
            exit="exit"
            className="fixed z-[151] top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-sm glass-panel-elevated rounded-2xl p-6 shadow-2xl border border-accent/20"
          >
            {/* Header */}
            <div className="flex items-center justify-between mb-5">
              <div className="flex items-center gap-2">
                <Keyboard className="w-4 h-4 text-accent" />
                <h2 className="font-display font-bold text-text text-sm">Keyboard Shortcuts</h2>
              </div>
              <button onClick={close} className="text-muted hover:text-text transition-colors">
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Shortcut rows */}
            <ul className="space-y-3">
              {SHORTCUTS.map((s, i) => (
                <li key={i} className="flex items-center justify-between gap-4">
                  <span className="text-xs text-muted">{s.description}</span>
                  <div className="flex items-center gap-1 flex-shrink-0">
                    {s.keys.map((k, j) => (
                      <React.Fragment key={j}>
                        <Kbd k={k} />
                        {j < s.keys.length - 1 && (
                          <span className="text-muted text-[10px]">+</span>
                        )}
                      </React.Fragment>
                    ))}
                  </div>
                </li>
              ))}
            </ul>

            <p className="text-[11px] text-muted mt-5 border-t border-border pt-4 text-center">
              Press <Kbd k="?" /> again or <Kbd k="Esc" /> to close
            </p>
          </motion.div>
        </>
      )}
    </AnimatePresence>,
    document.body
  )
}
