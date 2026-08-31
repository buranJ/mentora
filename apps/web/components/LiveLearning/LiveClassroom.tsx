'use client'

import { useCallback, useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { LiveKitRoom, RoomAudioRenderer, VideoConference, useParticipants } from '@livekit/components-react'
import { AlertTriangle, LoaderCircle, Users } from 'lucide-react'
import { useLHSession } from '@components/Contexts/LHSessionContext'
import { getUriWithOrg } from '@services/config/config'
import { endLiveSession, getLiveSession, joinLiveSession, startLiveSession, type LiveJoinConfig, type LiveSession } from '@services/live_learning/liveSessions'

function ParticipantsCount() {
  const participants = useParticipants()
  return <span className="inline-flex items-center gap-1"><Users size={16} /> Участники: {participants.length}</span>
}

function ErrorState({ message }: { message: string }) {
  return <div className="mx-auto mt-16 max-w-lg rounded-xl border border-red-200 bg-red-50 p-6 text-center text-red-900"><AlertTriangle className="mx-auto mb-3" /><h1 className="font-semibold">Не удалось открыть онлайн-урок</h1><p className="mt-2 text-sm">{message}</p></div>
}

export default function LiveClassroom({ orgslug, sessionUuid }: { orgslug: string; sessionUuid: string }) {
  const router = useRouter()
  const appSession = useLHSession() as any
  const accessToken = appSession?.data?.tokens?.access_token as string | undefined
  const currentUserId = appSession?.data?.user?.id as number | undefined
  const [liveSession, setLiveSession] = useState<LiveSession | null>(null)
  const [joinConfig, setJoinConfig] = useState<LiveJoinConfig | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [ending, setEnding] = useState(false)

  const load = useCallback(async () => {
    if (!accessToken) return
    setLoading(true)
    setError(null)
    try {
      const result = await getLiveSession(sessionUuid, accessToken)
      setLiveSession(result)
      if (result.status === 'live' || result.instructor_id === currentUserId) setJoinConfig(await joinLiveSession(sessionUuid, accessToken))
    } catch (cause: any) {
      setError(cause?.message || 'Проверьте подключение и доступ к уроку.')
    } finally {
      setLoading(false)
    }
  }, [accessToken, currentUserId, sessionUuid])

  useEffect(() => { void load() }, [load])

  const start = async () => {
    if (!accessToken) return
    setLoading(true)
    try { await startLiveSession(sessionUuid, accessToken); await load() }
    catch (cause: any) { setError(cause?.message || 'Не удалось начать урок.'); setLoading(false) }
  }
  const end = async () => {
    if (!accessToken) return
    setEnding(true)
    try { setLiveSession(await endLiveSession(sessionUuid, accessToken)); setJoinConfig(null) }
    catch (cause: any) { setError(cause?.message || 'Не удалось завершить урок.') }
    finally { setEnding(false) }
  }
  const leave = () => {
    setJoinConfig(null)
    if (liveSession?.course_uuid) router.push(getUriWithOrg(orgslug, `/course/${liveSession.course_uuid.replace(/^course_/, '')}`))
    else router.back()
  }

  if (appSession?.status === 'loading' || loading) return <div className="flex min-h-[50vh] items-center justify-center gap-2"><LoaderCircle className="animate-spin" /> Загружаем защищённое подключение…</div>
  if (!accessToken) return <ErrorState message="Для входа в онлайн-урок необходимо авторизоваться." />
  if (error) return <ErrorState message={error} />
  if (!liveSession) return <ErrorState message="Онлайн-урок не найден." />
  if (liveSession.status === 'ended') return <ErrorState message="Этот онлайн-урок уже завершён." />
  if (liveSession.status === 'scheduled' && liveSession.instructor_id !== currentUserId) return <ErrorState message="Преподаватель ещё не начал этот урок." />
  if (liveSession.status === 'scheduled') return <div className="mx-auto mt-16 max-w-lg rounded-xl border bg-white p-6 text-center"><h1 className="text-xl font-semibold">{liveSession.title}</h1><p className="mt-2 text-neutral-600">Урок запланирован. Начните его, когда будете готовы.</p><button onClick={start} className="mt-5 rounded-lg bg-blue-600 px-4 py-2 font-medium text-white">Начать урок</button></div>
  if (!joinConfig) return <ErrorState message="Не удалось получить разрешение на вход в комнату." />

  return <div className="mx-auto max-w-7xl p-3 md:p-6" data-lk-theme="default">
    <LiveKitRoom serverUrl={joinConfig.server_url} token={joinConfig.token} connect audio={false} video={false} onError={() => setError('Не удалось подключиться к серверу онлайн-урока.')} onDisconnected={() => setJoinConfig(null)} className="min-h-[78vh] overflow-hidden rounded-xl border bg-neutral-950">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-white/15 bg-neutral-900 px-4 py-3 text-white"><div><p className="text-xs text-white/65">Онлайн-урок</p><h1 className="font-semibold">{liveSession.title}</h1><p className="text-sm text-white/70">Преподаватель: {liveSession.instructor_name}</p></div><ParticipantsCount /></header>
      <div className="p-2"><VideoConference /></div>
      <RoomAudioRenderer />
      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-white/15 bg-neutral-900 px-4 py-3 text-sm text-white"><span>Микрофон · Камера · Демонстрация экрана · Чат · Участники</span><div className="flex gap-2"><button onClick={leave} className="rounded bg-white/15 px-3 py-1.5 hover:bg-white/25">Покинуть урок</button>{joinConfig.is_instructor && <button disabled={ending} onClick={end} className="rounded bg-red-600 px-3 py-1.5 disabled:opacity-60">{ending ? 'Завершение…' : 'Завершить урок'}</button>}</div></div>
    </LiveKitRoom>
  </div>
}
