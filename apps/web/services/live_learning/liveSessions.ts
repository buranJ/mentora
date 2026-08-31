import { getAPIUrl } from '@services/config/config'
import { RequestBodyWithAuthHeader } from '@services/utils/ts/requests'

export type LiveSessionStatus = 'scheduled' | 'live' | 'ended'

export type LiveSession = {
  id: number
  session_uuid: string
  course_uuid: string
  instructor_id: number
  instructor_name: string
  title: string
  description?: string | null
  scheduled_start_at?: string | null
  scheduled_end_at?: string | null
  status: LiveSessionStatus
  started_at?: string | null
  ended_at?: string | null
  created_at: string
  updated_at: string
}

export type LiveJoinConfig = {
  server_url: string
  token: string
  session: LiveSession
  is_instructor: boolean
}

async function liveFetch<T>(path: string, method: string, token: string, body: unknown = null): Promise<T> {
  const response = await fetch(
    `${getAPIUrl()}live-sessions${path}`,
    RequestBodyWithAuthHeader(method, body, null, token),
  )
  if (!response.ok) {
    const payload = await response.json().catch(() => null)
    throw Object.assign(new Error(payload?.detail || 'Не удалось выполнить действие с онлайн-уроком.'), {
      status: response.status,
    })
  }
  return response.json() as Promise<T>
}

export function listLiveSessions(courseUuid: string, token: string) {
  return liveFetch<LiveSession[]>(`/course/${courseUuid}`, 'GET', token)
}

export function createLiveSession(courseUuid: string, payload: { title: string; scheduled_start_at?: string | null }, token: string) {
  return liveFetch<LiveSession>(`/course/${courseUuid}`, 'POST', token, payload)
}

export function getLiveSession(sessionUuid: string, token: string) {
  return liveFetch<LiveSession>(`/${sessionUuid}`, 'GET', token)
}

export function startLiveSession(sessionUuid: string, token: string) {
  return liveFetch<LiveSession>(`/${sessionUuid}/start`, 'POST', token)
}

export function endLiveSession(sessionUuid: string, token: string) {
  return liveFetch<LiveSession>(`/${sessionUuid}/end`, 'POST', token)
}

export function joinLiveSession(sessionUuid: string, token: string) {
  return liveFetch<LiveJoinConfig>(`/${sessionUuid}/join`, 'POST', token)
}
