/**
 * usePageTitle.ts — sets document.title per route
 */
import { useEffect } from 'react'

const BASE = 'InterviewDNA'

export function usePageTitle(title?: string) {
  useEffect(() => {
    document.title = title ? `${title} — ${BASE}` : BASE
  }, [title])
}
