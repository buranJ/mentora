'use client'

import Link from 'next/link'
import { FormEvent, useState } from 'react'
import { Radio, Video } from 'lucide-react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useLHSession } from '@components/Contexts/LHSessionContext'
import { getUriWithOrg } from '@services/config/config'
import { getCourseRights } from '@services/courses/courses'
import { createLiveSession, listLiveSessions, type LiveSession } from '@services/live_learning/liveSessions'

function sessionLabel(session: LiveSession) {
  if (session.status === 'live') return 'В эфире'
  if (session.status === 'ended') return 'Завершён'
  return 'Запланирован'
}

export default function LiveSessionsPanel({ courseUuid, courseName, orgslug }: { courseUuid: string; courseName: string; orgslug: string }) {
  const session = useLHSession() as any
  const accessToken = session?.data?.tokens?.access_token as string | undefined
  const queryClient = useQueryClient()
  const [open, setOpen] = useState(false)
  const [title, setTitle] = useState(`Онлайн-урок: ${courseName}`)
  const [scheduledAt, setScheduledAt] = useState('')
  const sessionsQuery = useQuery({ queryKey: ['live-sessions', courseUuid], queryFn: () => listLiveSessions(courseUuid, accessToken!), enabled: !!accessToken && !!courseUuid })
  const rightsQuery = useQuery({ queryKey: ['course-rights', courseUuid], queryFn: () => getCourseRights(courseUuid, accessToken!), enabled: !!accessToken && !!courseUuid })
  const canManage = rightsQuery.data?.permissions?.update === true
  const createMutation = useMutation({
    mutationFn: () => createLiveSession(courseUuid, { title: title.trim(), scheduled_start_at: scheduledAt ? new Date(scheduledAt).toISOString() : null }, accessToken!),
    onSuccess: () => { setOpen(false); queryClient.invalidateQueries({ queryKey: ['live-sessions', courseUuid] }) },
  })
  const submit = (event: FormEvent) => { event.preventDefault(); if (title.trim()) createMutation.mutate() }

  return <section className="rounded-xl border border-neutral-200 bg-white p-4 shadow-sm space-y-3" aria-label="Онлайн-уроки">
    <div className="flex items-center justify-between gap-3"><div className="flex items-center gap-2 font-semibold text-neutral-900"><Radio size={18} /> Онлайн-уроки</div>{canManage && <button type="button" onClick={() => setOpen((value) => !value)} className="rounded-md bg-neutral-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-neutral-700">Создать</button>}</div>
    {open && canManage && <form onSubmit={submit} className="space-y-2 rounded-lg bg-neutral-50 p-3"><label className="block text-sm font-medium">Название урока<input value={title} onChange={(event) => setTitle(event.target.value)} maxLength={180} required className="mt-1 w-full rounded border border-neutral-300 bg-white px-2 py-1.5" /></label><label className="block text-sm font-medium">Начало (необязательно)<input type="datetime-local" value={scheduledAt} onChange={(event) => setScheduledAt(event.target.value)} className="mt-1 w-full rounded border border-neutral-300 bg-white px-2 py-1.5" /></label>{createMutation.error && <p className="text-sm text-red-700">Не удалось создать урок. Проверьте права доступа.</p>}<button disabled={createMutation.isPending} className="rounded bg-blue-600 px-3 py-1.5 text-sm font-medium text-white disabled:opacity-60">{createMutation.isPending ? 'Создание…' : 'Сохранить урок'}</button></form>}
    {sessionsQuery.isLoading && <p className="text-sm text-neutral-500">Загружаем онлайн-уроки…</p>}
    {sessionsQuery.isError && <p className="text-sm text-red-700">Не удалось загрузить онлайн-уроки.</p>}
    {!sessionsQuery.isLoading && !sessionsQuery.data?.length && <p className="text-sm text-neutral-500">Онлайн-уроков пока нет.</p>}
    <div className="space-y-2">{sessionsQuery.data?.map((liveSession) => <Link key={liveSession.session_uuid} href={getUriWithOrg(orgslug, `/live/${liveSession.session_uuid}`)} className="block rounded-lg border border-neutral-200 p-3 hover:border-blue-400 hover:bg-blue-50/40"><div className="flex items-start gap-2"><Video size={16} className="mt-0.5" /><div className="min-w-0"><p className="font-medium text-neutral-900 truncate">{liveSession.title}</p><p className="text-xs text-neutral-600">{sessionLabel(liveSession)} · Преподаватель: {liveSession.instructor_name}</p></div></div></Link>)}</div>
  </section>
}
