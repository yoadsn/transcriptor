import type { SessionDTO, LineStatusDTO, SubmitKind } from './types'

const BASE = ''

export const CONSENT_VERSION = '1.0'

let authToken: string | null = null

export function setAuthToken(t: string): void {
  authToken = t
}

export function getAuthToken(): string | null {
  return authToken
}

async function request<T>(path: string, options?: RequestInit): Promise<T | null> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (authToken) headers['Authorization'] = `Bearer ${authToken}`
  const res = await fetch(BASE + path, {
    ...options,
    headers: { ...headers, ...(options?.headers as Record<string, string> | undefined) },
  })
  if (res.status === 204) return null
  if (!res.ok) throw new Error(`${res.status}`)
  return res.json() as Promise<T>
}

// ── Response types ────────────────────────────────────────────────────────────

export interface ProfileDTO {
  name: string
  today: number
  goal: number
  streak: number
  week: number
  total: number
  pages: number
}

export interface CommunityDTO {
  lines: number
  pages: number
  volunteers: number
  manuscripts: number
}

// ── API calls ─────────────────────────────────────────────────────────────────

export const api = {
  nextSession: (): Promise<SessionDTO | null> =>
    request<SessionDTO>('/api/next-session'),

  submitResponse: (
    lineId: string,
    body: { kind: SubmitKind; text?: string }
  ): Promise<LineStatusDTO | null> =>
    request<LineStatusDTO>(`/api/lines/${lineId}/response`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  postConsent: (body: { consent_type: string; version: string }): Promise<null> =>
    request<null>('/api/consent', {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  getProfile: (): Promise<ProfileDTO | null> =>
    request<ProfileDTO>('/api/me/profile'),

  getCommunityStats: (): Promise<CommunityDTO | null> =>
    request<CommunityDTO>('/api/community'),

  getLeaderboard: (): Promise<Array<{ display_name: string; text_count: number }> | null> =>
    request<Array<{ display_name: string; text_count: number }>>('/api/leaderboard'),
}
