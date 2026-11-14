import React, { Suspense, lazy } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Navbar } from './components/layout/Navbar'
import { Sidebar } from './components/layout/Sidebar'
import { AuroraBackground } from './components/layout/AuroraBackground'
import { CommandPalette } from './components/layout/CommandPalette'
import { OnboardingTour } from './components/layout/OnboardingTour'
import { KeyboardCheatSheet } from './components/layout/KeyboardCheatSheet'
import { Footer } from './components/layout/Footer'
import { ErrorBoundary } from './components/layout/ErrorBoundary'
import { AppRoutes } from './routes/AppRoutes'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 mins
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="relative min-h-screen flex flex-col font-sans">
        <AuroraBackground />
        <Navbar />
        <Sidebar />
        <CommandPalette />
        <OnboardingTour />
        <KeyboardCheatSheet />

        {/* Main Content Area */}
        <main className="flex-1 md:pl-20 transition-all duration-300 pt-16">
          <ErrorBoundary>
            <AppRoutes />
          </ErrorBoundary>
        </main>

        <Footer />
      </div>
    </QueryClientProvider>
  )
}

export default App
