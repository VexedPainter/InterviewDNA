import {
  CompaniesResponse,
  CompanyDNAProfile,
  CreateSessionRequest,
  CreateSessionResponse,
  HealthResponse,
  SendMessageResponse,
  SessionReport,
  UserProgressResponse,
  ArchiveRecord,
  ApiError,
} from './types'

// Use relative /api by default to leverage Vite proxy, or fallback to full URL
const BASE_URL = import.meta.env.VITE_API_URL || '/api'

function buildUrl(path: string, params?: Record<string, string>): string {
  // If BASE_URL starts with http:// or https://, use it directly
  let fullPath = `${BASE_URL.replace(/\/$/, '')}/${path.replace(/^\//, '')}`
  if (typeof window !== 'undefined' && !fullPath.startsWith('http://') && !fullPath.startsWith('https://')) {
    const url = new URL(fullPath, window.location.origin)
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null) url.searchParams.set(k, v)
      })
    }
    return url.toString()
  } else {
    if (params) {
      const searchParams = new URLSearchParams()
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null) searchParams.set(k, v)
      })
      const qs = searchParams.toString()
      if (qs) fullPath += (fullPath.includes('?') ? '&' : '?') + qs
    }
    return fullPath
  }
}

export class ApiRequestError extends Error {
  error: string
  detail: string
  status: number

  constructor(status: number, err: ApiError) {
    super(err.detail || err.error || `HTTP ${status}`)
    this.name = 'ApiRequestError'
    this.status = status
    this.error = err.error || 'Request Error'
    this.detail = err.detail || 'An unexpected error occurred.'
  }
}

async function fetchWithTimeout(
  input: string,
  init?: RequestInit,
  timeoutMs = 30000,
  retries = 1
): Promise<Response> {
  let attempt = 0
  while (attempt <= retries) {
    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), timeoutMs)

    try {
      const response = await fetch(input, {
        ...init,
        signal: controller.signal,
      })
      clearTimeout(timer)
      return response
    } catch (err: any) {
      clearTimeout(timer)
      const isAbort = err?.name === 'AbortError'
      const isNetwork = err instanceof TypeError || isAbort
      if (attempt < retries && isNetwork) {
        attempt++
        // Exponential backoff
        await new Promise((res) => setTimeout(res, 500 * Math.pow(2, attempt)))
        continue
      }
      if (isAbort) {
        throw new ApiRequestError(408, {
          error: 'Request Timeout',
          detail: `Request to ${input} timed out after ${timeoutMs / 1000}s.`,
        })
      }
      throw new ApiRequestError(0, {
        error: 'Network Error',
        detail: 'Cannot connect to InterviewDNA backend. Please ensure the backend is running.',
      })
    }
  }
  throw new Error('Unreachable retry state')
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errJson: ApiError = { error: 'HTTP Error', detail: res.statusText }
    try {
      errJson = await res.json()
    } catch {
      // no JSON body
    }
    throw new ApiRequestError(res.status, errJson)
  }
  return res.json()
}

export const api = {
  getHealth: async (): Promise<HealthResponse> => {
    const res = await fetchWithTimeout(buildUrl('health'), undefined, 8000, 1)
    return handleResponse<HealthResponse>(res)
  },

  getCompanies: async (): Promise<CompaniesResponse> => {
    const res = await fetchWithTimeout(buildUrl('companies'), undefined, 10000, 1)
    return handleResponse<CompaniesResponse>(res)
  },

  getCompanyDNA: async (company: string, role?: string): Promise<CompanyDNAProfile> => {
    const params: Record<string, string> = {}
    if (role) params.role = role
    const res = await fetchWithTimeout(buildUrl(`companies/${encodeURIComponent(company)}/dna`, params), undefined, 15000, 1)
    return handleResponse<CompanyDNAProfile>(res)
  },

  createSession: async (payload: CreateSessionRequest): Promise<CreateSessionResponse> => {
    const res = await fetchWithTimeout(buildUrl('sessions'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }, 30000, 1)
    return handleResponse<CreateSessionResponse>(res)
  },

  sendMessage: async (sessionId: string, message: string): Promise<SendMessageResponse> => {
    const res = await fetchWithTimeout(buildUrl(`sessions/${sessionId}/message`), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    }, 45000, 0)
    return handleResponse<SendMessageResponse>(res)
  },

  endSession: async (sessionId: string): Promise<SessionReport> => {
    const res = await fetchWithTimeout(buildUrl(`sessions/${sessionId}/end`), {
      method: 'POST',
    }, 30000, 1)
    return handleResponse<SessionReport>(res)
  },

  getUserProgress: async (nickname: string): Promise<UserProgressResponse> => {
    const res = await fetchWithTimeout(buildUrl(`users/${encodeURIComponent(nickname)}/progress`), undefined, 10000, 1)
    return handleResponse<UserProgressResponse>(res)
  },

  getArchiveRecord: async (recordId: string): Promise<ArchiveRecord> => {
    const res = await fetchWithTimeout(buildUrl(`records/${encodeURIComponent(recordId)}`), undefined, 10000, 1)
    return handleResponse<ArchiveRecord>(res)
  },

  getReportPdfUrl: (sessionId: string): string => {
    return buildUrl(`sessions/${sessionId}/report.pdf`)
  },

  getReportMdUrl: (sessionId: string): string => {
    return buildUrl(`sessions/${sessionId}/report.md`)
  },

  getStreamUrl: (sessionId: string, message: string): string => {
    return buildUrl(`sessions/${sessionId}/stream`, { message })
  },
}
