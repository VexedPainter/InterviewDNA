/**
 * useKeyboardShortcut.ts — fires a callback on a specific key combo.
 */
import { useEffect } from 'react'

interface Options {
  key: string
  ctrl?: boolean
  shift?: boolean
  meta?: boolean
  alt?: boolean
}

export function useKeyboardShortcut(opts: Options, handler: () => void) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (opts.ctrl !== undefined && e.ctrlKey !== opts.ctrl) return
      if (opts.meta !== undefined && e.metaKey !== opts.meta) return
      if (opts.shift !== undefined && e.shiftKey !== opts.shift) return
      if (opts.alt !== undefined && e.altKey !== opts.alt) return
      if (e.key.toLowerCase() !== opts.key.toLowerCase()) return
      // Don't fire while typing in a text field (unless it's a cmd combo)
      if (!opts.ctrl && !opts.meta) {
        const tag = (e.target as HTMLElement)?.tagName
        if (tag === 'INPUT' || tag === 'TEXTAREA') return
      }
      e.preventDefault()
      handler()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [opts.key, opts.ctrl, opts.meta, opts.shift, opts.alt, handler])
}
