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

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

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
    const res = await fetch(`${BASE_URL}/health`)
    return handleResponse<HealthResponse>(res)
  },

  getCompanies: async (): Promise<CompaniesResponse> => {
    const res = await fetch(`${BASE_URL}/companies`)
    return handleResponse<CompaniesResponse>(res)
  },

  getCompanyDNA: async (company: string, role?: string): Promise<CompanyDNAProfile> => {
    const url = new URL(`${BASE_URL}/companies/${encodeURIComponent(company)}/dna`)
    if (role) url.searchParams.set('role', role)
    const res = await fetch(url.toString())
    return handleResponse<CompanyDNAProfile>(res)
  },

  createSession: async (payload: CreateSessionRequest): Promise<CreateSessionResponse> => {
    const res = await fetch(`${BASE_URL}/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    return handleResponse<CreateSessionResponse>(res)
  },

  sendMessage: async (sessionId: string, message: string): Promise<SendMessageResponse> => {
    const res = await fetch(`${BASE_URL}/sessions/${sessionId}/message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    })
    return handleResponse<SendMessageResponse>(res)
  },

  endSession: async (sessionId: string): Promise<SessionReport> => {
    const res = await fetch(`${BASE_URL}/sessions/${sessionId}/end`, {
      method: 'POST',
    })
    return handleResponse<SessionReport>(res)
  },

  getUserProgress: async (nickname: string): Promise<UserProgressResponse> => {
    const res = await fetch(`${BASE_URL}/users/${encodeURIComponent(nickname)}/progress`)
    return handleResponse<UserProgressResponse>(res)
  },

  getArchiveRecord: async (recordId: string): Promise<ArchiveRecord> => {
    const res = await fetch(`${BASE_URL}/records/${encodeURIComponent(recordId)}`)
    return handleResponse<ArchiveRecord>(res)
  },

  getReportPdfUrl: (sessionId: string): string => {
    return `${BASE_URL}/sessions/${sessionId}/report.pdf`
  },

  getReportMdUrl: (sessionId: string): string => {
    return `${BASE_URL}/sessions/${sessionId}/report.md`
  },

  getStreamUrl: (sessionId: string, message: string): string => {
    const url = new URL(`${BASE_URL}/sessions/${sessionId}/stream`)
    url.searchParams.set('message', message)
    return url.toString()
  },
}
