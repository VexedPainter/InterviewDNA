import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import {
  AgentTrace,
  CoachingAdvice,
  EvaluationResult,
  SessionReport,
  TurnRecord,
} from '../lib/api/types'

export interface ChatMessage {
  id: string
  sender: 'agent' | 'user'
  text: string
  timestamp: number
  turnNumber?: number
  isFollowup?: boolean
  questionId?: string | null
  topic?: string | null
  roundType?: string | null
  evaluation?: EvaluationResult | null
  followup?: TurnRecord | null
  coaching?: CoachingAdvice | null
}

export type AgentName =
  | 'Interviewer Agent'
  | 'Evaluator Agent'
  | 'Coach Agent'
  | 'Report Agent'
  | 'General Chat'

interface SessionState {
  nickname: string
  company: string
  role: string
  roundMode: string
  difficultyMode: number
  pressureMode: boolean
  pressureSeconds: number

  sessionId: string | null
  activeQuestion: TurnRecord | null
  messages: ChatMessage[]
  agentTrace: AgentTrace | null
  activeAgent: AgentName
  isProcessing: boolean
  isStreaming: boolean

  latestReport: SessionReport | null
  activeCitationId: string | null

  // Actions
  setNickname: (name: string) => void
  setConfig: (config: Partial<Pick<SessionState, 'company' | 'role' | 'roundMode' | 'difficultyMode' | 'pressureMode' | 'pressureSeconds'>>) => void
  startSession: (sessionId: string, firstQuestion?: TurnRecord | null) => void
  addUserMessage: (text: string) => void
  addAgentMessage: (msg: Omit<ChatMessage, 'id' | 'sender' | 'timestamp'>) => void
  updateStreamingMessage: (chunk: string) => void
  setTrace: (trace: AgentTrace | null, agent?: AgentName) => void
  setProcessing: (val: boolean) => void
  setStreaming: (val: boolean) => void
  setReport: (report: SessionReport | null) => void
  setActiveCitationId: (id: string | null) => void
  resetSession: () => void
}

export const useSessionStore = create<SessionState>()(
  persist(
    (set, get) => ({
      nickname: 'Alex',
      company: 'Zoho',
      role: 'Software Developer',
      roundMode: 'Technical',
      difficultyMode: 3,
      pressureMode: false,
      pressureSeconds: 120,

      sessionId: null,
      activeQuestion: null,
      messages: [],
      agentTrace: null,
      activeAgent: 'Interviewer Agent',
      isProcessing: false,
      isStreaming: false,

      latestReport: null,
      activeCitationId: null,

      setNickname: (nickname) => set({ nickname }),

      setConfig: (config) => set((state) => ({ ...state, ...config })),

      startSession: (sessionId, firstQuestion) => {
        const welcomeMsgs: ChatMessage[] = []
        if (firstQuestion) {
          welcomeMsgs.push({
            id: `q-1`,
            sender: 'agent',
            text: `### 🎯 Question #1 (${firstQuestion.round_type || 'Technical'} Round | ${firstQuestion.topic || 'General'})\n\n**${firstQuestion.question}**\n\n*Type your answer below or use voice input.*`,
            timestamp: Date.now(),
            turnNumber: 1,
            questionId: firstQuestion.question_id,
            topic: firstQuestion.topic,
            roundType: firstQuestion.round_type,
          })
        }
        set({
          sessionId,
          activeQuestion: firstQuestion || null,
          messages: welcomeMsgs,
          latestReport: null,
          activeAgent: 'Interviewer Agent',
          agentTrace: {
            retrieved_count: 5,
            fallback_level: 'company_role',
            latency_ms: 220,
          },
        })
      },

      addUserMessage: (text) => {
        const newMsg: ChatMessage = {
          id: `usr-${Date.now()}`,
          sender: 'user',
          text,
          timestamp: Date.now(),
        }
        set((state) => ({ messages: [...state.messages, newMsg] }))
      },

      addAgentMessage: (msg) => {
        const newMsg: ChatMessage = {
          ...msg,
          id: `agt-${Date.now()}`,
          sender: 'agent',
          timestamp: Date.now(),
        }
        set((state) => ({
          messages: [...state.messages, newMsg],
          activeQuestion: msg.followup || (msg.text.includes('### 🎯 Question') ? state.activeQuestion : state.activeQuestion),
        }))
      },

      updateStreamingMessage: (chunk) => {
        set((state) => {
          const msgs = [...state.messages]
          const lastMsg = msgs[msgs.length - 1]
          if (lastMsg && lastMsg.sender === 'agent') {
            lastMsg.text += chunk
            return { messages: msgs }
          }
          return state
        })
      },

      setTrace: (trace, agent) =>
        set((state) => ({
          agentTrace: trace ?? state.agentTrace,
          activeAgent: agent ?? state.activeAgent,
        })),

      setProcessing: (isProcessing) => set({ isProcessing }),
      setStreaming: (isStreaming) => set({ isStreaming }),
      setReport: (latestReport) => set({ latestReport }),
      setActiveCitationId: (activeCitationId) => set({ activeCitationId }),

      resetSession: () =>
        set({
          sessionId: null,
          activeQuestion: null,
          messages: [],
          agentTrace: null,
          activeAgent: 'Interviewer Agent',
          isProcessing: false,
          isStreaming: false,
          latestReport: null,
          activeCitationId: null,
        }),
    }),
    {
      name: 'interviewdna-session-storage',
      partialize: (state) => ({
        nickname: state.nickname,
        company: state.company,
        role: state.role,
        roundMode: state.roundMode,
        difficultyMode: state.difficultyMode,
        pressureMode: state.pressureMode,
        pressureSeconds: state.pressureSeconds,
        sessionId: state.sessionId,
      }),
    }
  )
)
