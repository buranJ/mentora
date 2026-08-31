import { describe, expect, test } from 'bun:test'
import { readFile } from 'node:fs/promises'

const root = new URL('..', import.meta.url)

describe('live classroom wiring', () => {
  test('uses the backend-owned join endpoint and never a client secret', async () => {
    const source = await readFile(new URL('./services/live_learning/liveSessions.ts', root), 'utf8')
    expect(source).toContain('live-sessions${path}')
    expect(source).toContain('/join')
    expect(source).not.toContain('LIVEKIT_API_SECRET')
  })

  test('classroom contains real LiveKit room states and Russian failure UI', async () => {
    const source = await readFile(new URL('./components/LiveLearning/LiveClassroom.tsx', root), 'utf8')
    expect(source).toContain('LiveKitRoom')
    expect(source).toContain('VideoConference')
    expect(source).toContain('RoomAudioRenderer')
    expect(source).toContain('Не удалось открыть онлайн-урок')
    expect(source).toContain('Покинуть урок')
  })
})
