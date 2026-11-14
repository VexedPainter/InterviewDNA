import React, { Suspense, lazy } from 'react'
import { Routes, Route, useLocation } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { pageVariants } from '../lib/motion'
import { Skeleton } from '../components/ui/Skeleton'

// Code-split each feature route
const LandingPage   = lazy(() => import('../features/landing/LandingPage').then((m) => ({ default: m.LandingPage })))
const SetupWizard   = lazy(() => import('../features/setup/SetupWizard').then((m) => ({ default: m.SetupWizard })))
const DashboardPage = lazy(() => import('../features/dashboard/DashboardPage').then((m) => ({ default: m.DashboardPage })))
const InterviewRoom = lazy(() => import('../features/interview/InterviewRoom').then((m) => ({ default: m.InterviewRoom })))
const CompanyDNAPage = lazy(() => import('../features/dna/CompanyDNAPage').then((m) => ({ default: m.CompanyDNAPage })))
const CoachingPage  = lazy(() => import('../features/coaching/CoachingPage').then((m) => ({ default: m.CoachingPage })))
const ReportPage    = lazy(() => import('../features/report/ReportPage').then((m) => ({ default: m.ReportPage })))
const NotFoundPage  = lazy(() => import('../features/errors/NotFoundPage').then((m) => ({ default: m.NotFoundPage })))

/** Full-page skeleton shown while a lazy chunk loads */
const PageFallback: React.FC = () => (
  <div className="p-6 space-y-4 max-w-5xl mx-auto pt-8">
    <Skeleton className="h-10 w-64" />
    <Skeleton className="h-6 w-full max-w-lg" />
    <div className="grid grid-cols-3 gap-4 mt-6">
      {[1, 2, 3].map((i) => <Skeleton key={i} className="h-40 rounded-2xl" />)}
    </div>
    <Skeleton className="h-64 rounded-2xl mt-4" />
  </div>
)

export const AppRoutes: React.FC = () => {
  const location = useLocation()

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={location.pathname}
        variants={pageVariants}
        initial="initial"
        animate="animate"
        exit="exit"
        className="w-full min-h-[calc(100vh-4rem)]"
      >
        <Suspense fallback={<PageFallback />}>
          <Routes location={location}>
            <Route path="/"          element={<LandingPage />} />
            <Route path="/setup"     element={<SetupWizard />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/interview" element={<InterviewRoom />} />
            <Route path="/dna"       element={<CompanyDNAPage />} />
            <Route path="/coaching"  element={<CoachingPage />} />
            <Route path="/report"    element={<ReportPage />} />
            <Route path="*"          element={<NotFoundPage />} />
          </Routes>
        </Suspense>
      </motion.div>
    </AnimatePresence>
  )
}
