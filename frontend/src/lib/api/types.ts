/**
 * TypeScript definitions mapping 1:1 with InterviewDNA FastAPI models.
 */

export interface HealthResponse {
  status: string
  service: string
  version: string
}

export interface CompanyInfo {
  company: string
  roles: string[]
  rounds: string[]
}

export interface CompaniesResponse {
  companies: string[]
  roles: Record<string, string[]>
  round_structures: Record<string, string[]>
  company_details: CompanyInfo[]
}

export interface CompanyDNAProfile {
  company: string
  role?: string | null
  total_records: number
  selection_rate: number
  avg_difficulty: number
  difficulty_trend_by_year: Record<string, number>
  topic_distribution: Record<string, number>
  round_distribution: Record<string, number>
  top_rejection_tags: Array<{ tag: string; count: number }>
  top_positive_tags: Array<{ tag: string; count: number }>
  interviewer_style_summary: string
  generated_at: string
}

export interface CreateSessionRequest {
  nickname: string
  company: string
  role: string
  round_mode: string
  difficulty_mode: number
  pressure_mode: boolean
}

export interface EvaluationResult {
  correctness: number
  depth: number
  communication: number
  overall: number
  matched_points: string[]
  missed_points: string[]
  red_flags: string[]
  needs_followup: boolean
  followup_reason?: string | null
}

export interface TurnRecord {
  turn_number: number
  question_id?: string | null
  question: string
  expected_points: string[]
  candidate_answer: string
  is_followup: boolean
  evaluation?: EvaluationResult | null
  topic?: string | null
  round_type?: string | null
}

export interface CreateSessionResponse {
  session_id: string
  company: string
  role: string
  round_type: string
  difficulty_level: number
  first_question?: TurnRecord | null
  message: string
}

export interface AgentTrace {
  retrieved_count: number
  fallback_level: string
  latency_ms: number
}

export interface CoachingTip {
  text: string
  evidence_ids: string[]
  evidence_year?: number | number[] | null
}

export interface CoachingAdvice {
  summary: string
  tips: CoachingTip[]
  no_evidence_notice?: string | null
}

export interface SendMessageResponse {
  routed_to: string
  confidence: number
  reply_type: 'PRACTICE' | 'EVALUATE' | 'COACH' | 'REPORT' | 'SMALLTALK_OR_UNCLEAR'
  response_text: string
  question?: TurnRecord | null
  evaluation?: EvaluationResult | null
  coaching?: CoachingAdvice | null
  followup?: TurnRecord | null
  agent_trace: AgentTrace
}

export interface TurnScore {
  turn_number: number
  question: string
  question_id?: string | null
  topic?: string | null
  round_type?: string | null
  correctness: number
  depth: number
  communication: number
  overall: number
  is_followup: boolean
}

export interface SessionReport {
  session_id: string
  company: string
  role: string
  scores_per_turn?: TurnScore[]
  turn_scores?: TurnScore[]
  averages: {
    correctness?: number
    depth?: number
    communication?: number
    overall?: number
  }
  trend: 'upward' | 'declining' | 'flat'
  strengths?: string[]
  top_strengths?: string[]
  gaps?: string[]
  top_gaps?: string[]
  improvement_plan: string[]
  benchmark_comparison: {
    company?: string
    role?: string
    avg_score_selected?: number
    sample_size?: number
  }
  final_verdict?: string
  verdict?: string
}

export interface UserProgressSession {
  session_id: string
  user_nickname: string
  company: string
  role: string
  round_type: string
  difficulty_level: number
  status: string
  created_at: string
  updated_at?: string
  overall_score: number
  final_verdict: string
  condensed_summary?: string
}

export interface UserProgressResponse {
  nickname: string
  total_sessions: number
  sessions: UserProgressSession[]
}

export interface ArchiveRecord {
  record_id: string
  year: number
  company: string
  role: string
  round_type: string
  topic: string
  difficulty: number
  question: string
  expected_points: string[]
  candidate_answer_summary: string
  feedback_text: string
  feedback_tags: string[]
  score_given: number
  outcome: 'Selected' | 'Rejected'
}

export interface ApiError {
  error: string
  detail: string
}
