import { create } from 'zustand'

export type ThemeMode = 'dark' | 'light'

interface ThemeState {
  theme: ThemeMode
  setTheme: (theme: ThemeMode) => void
  toggleTheme: (event?: React.MouseEvent) => void
}

function getInitialTheme(): ThemeMode {
  if (typeof window === 'undefined') return 'dark'
  const saved = localStorage.getItem('interviewdna-theme') as ThemeMode | null
  if (saved === 'dark' || saved === 'light') return saved
  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
    return 'light'
  }
  return 'dark'
}

function applyThemeClass(theme: ThemeMode) {
  if (typeof document === 'undefined') return
  const root = document.documentElement
  if (theme === 'dark') {
    root.classList.add('dark')
    root.classList.remove('light')
  } else {
    root.classList.add('light')
    root.classList.remove('dark')
  }
  localStorage.setItem('interviewdna-theme', theme)
}

export const useThemeStore = create<ThemeState>((set, get) => {
  const initial = getInitialTheme()
  applyThemeClass(initial)

  return {
    theme: initial,
    setTheme: (theme: ThemeMode) => {
      applyThemeClass(theme)
      set({ theme })
    },
    toggleTheme: (event?: React.MouseEvent) => {
      const nextTheme = get().theme === 'dark' ? 'light' : 'dark'

      // Check if View Transitions API is supported
      if (!('startViewTransition' in document)) {
        applyThemeClass(nextTheme)
        set({ theme: nextTheme })
        return
      }

      const x = event ? event.clientX : window.innerWidth / 2
      const y = event ? event.clientY : 40
      const endRadius = Math.hypot(
        Math.max(x, window.innerWidth - x),
        Math.max(y, window.innerHeight - y)
      )

      const doc = document as any
      const transition = doc.startViewTransition(() => {
        applyThemeClass(nextTheme)
        set({ theme: nextTheme })
      })

      transition.ready.then(() => {
        document.documentElement.animate(
          {
            clipPath: [
              `circle(0px at ${x}px ${y}px)`,
              `circle(${endRadius}px at ${x}px ${y}px)`,
            ],
          },
          {
            duration: 450,
            easing: 'cubic-bezier(0.2, 0, 0, 1)',
            pseudoElement: '::view-transition-new(root)',
          }
        )
      })
    },
  }
})
