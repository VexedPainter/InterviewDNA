/**
 * ErrorBoundary.tsx — catches render errors and shows a friendly offline state.
 */
import React, { Component, type ErrorInfo, type ReactNode } from 'react'

interface Props {
  children: ReactNode
}
interface State {
  hasError: boolean
  error?: Error
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('[ErrorBoundary]', error, info)
  }

  render() {
    if (!this.state.hasError) return this.props.children

    return (
      <div className="min-h-screen flex items-center justify-center px-6 text-center">
        <div className="space-y-6 max-w-md">
          <div className="text-5xl">⚠️</div>
          <h2 className="text-2xl font-display font-bold text-text">Something went wrong</h2>
          <p className="text-muted text-sm leading-relaxed">
            {this.state.error?.message || 'An unexpected error occurred.'}
          </p>
          <p className="text-xs text-muted">
            If the backend is not running, start it with{' '}
            <code className="px-2 py-0.5 bg-white/10 rounded font-mono">make api</code>.
          </p>
          <button
            onClick={() => this.setState({ hasError: false })}
            className="px-6 py-2.5 rounded-full bg-accent text-white text-sm font-semibold hover:opacity-90 transition-all"
          >
            Try again
          </button>
        </div>
      </div>
    )
  }
}
