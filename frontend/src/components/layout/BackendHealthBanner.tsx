import React from 'react'
import { useQuery } from '@tanstack/react-query'
import { AlertCircle, RefreshCw, Terminal } from 'lucide-react'
import { api } from '../../lib/api/client'

export const BackendHealthBanner: React.FC = () => {
  const { data, isError, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['backend-health'],
    queryFn: () => api.getHealth(),
    retry: 1,
    staleTime: 30000,
    refetchOnWindowFocus: false,
  })

  if (isLoading || (!isError && data?.status === 'healthy')) {
    return null
  }

  return (
    <div className="bg-rose-500/90 text-white px-4 py-2 text-xs flex items-center justify-between sticky top-0 z-50 shadow-md backdrop-blur-sm border-b border-rose-600">
      <div className="flex items-center space-x-2 max-w-4xl mx-auto flex-1">
        <AlertCircle className="w-4 h-4 flex-shrink-0" />
        <span className="font-semibold">Backend Offline:</span>
        <span className="text-rose-100">
          Cannot connect to InterviewDNA API server at <code className="bg-black/20 px-1 py-0.5 rounded font-mono">:8000</code>.
        </span>
        <span className="hidden sm:inline-flex items-center text-rose-200 pl-2">
          <Terminal className="w-3.5 h-3.5 mr-1" />
          Run <code className="bg-black/30 px-1.5 py-0.5 rounded ml-1 font-mono text-white">make api</code> in root
        </span>
      </div>

      <button
        onClick={() => refetch()}
        disabled={isFetching}
        className="inline-flex items-center space-x-1 px-2.5 py-1 rounded bg-black/20 hover:bg-black/30 text-white font-medium transition-colors"
      >
        <RefreshCw className={`w-3 h-3 ${isFetching ? 'animate-spin' : ''}`} />
        <span>Retry</span>
      </button>
    </div>
  )
}
