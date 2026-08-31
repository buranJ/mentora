# Local LiveKit classroom

## What starts

`./scripts/dev.sh` starts the normal Mentora PostgreSQL and Redis services plus
the pinned `livekit/livekit-server:v1.13.5` container. FastAPI, Next.js and the
Hocuspocus server continue to run through the official LearnHouse development
CLI. The local signaling URL is `ws://localhost:7880`.

LiveKit uses its official development credentials (`devkey` / `secret`) only in
this local container. They are stored as local-only values in `apps/api/.env`
and its example. Do not use them outside local development.

## Configuration

FastAPI is the only process that needs these variables:

```dotenv
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
```

The web app intentionally has no `LIVEKIT_API_SECRET` or API key. It receives a
short-lived room token and public WebSocket URL from FastAPI after application
authorization.

## Teacher flow

1. Sign in and open a course.
2. In **Онлайн-уроки**, create a lesson, optionally choosing a scheduled time.
3. Open it and select **Начать урок**.
4. Enable microphone, camera or screen sharing in the LiveKit controls.
5. Select **Завершить урок** when the class is over.

Course `UPDATE` permission controls creation, start and end. Course `READ`
permission controls listing and joining. The backend is authoritative: changing
frontend request data cannot promote a student.

## Student flow

1. Sign in as a learner who has course access.
2. Open the same course and select the active online lesson.
3. Join after the teacher starts it; use camera, microphone and the ephemeral
   LiveKit chat as needed.
4. Use **Покинуть урок** to disconnect safely.

## Troubleshooting

```bash
docker compose -f docker/docker-compose.mentora-dev.yml -p learnhouse-dev ps
docker logs mentora-livekit-dev
curl -I http://localhost:7880/
```

`LiveKitRoom` connection failures are normally separated by layer: verify the
container and port 7880 first, then the authenticated `/join` response, then
browser WebRTC permissions/networking. Local Docker exposes signaling, TCP
fallback and UDP port 7882. This is development-only; production requires a
TLS domain and an explicitly designed UDP/TURN deployment.

## Security boundary

- Tokens are signed with the official `livekit-api` SDK and expire after ten
  minutes.
- Rooms and LiveKit participant identities use opaque IDs.
- The display name excludes email and phone values.
- No room admin, recording, ingress or room-creation grants are issued.
- Chat is LiveKit room data only and is not persisted.

## Russian default localization follow-up

Russian is available through the existing selector. Making it the organization
default is deferred: server rendering initializes i18next with the English
fallback, while the client runs `LanguageDetector` from browser storage/cookies;
`OrgLanguageSync` then changes to the organization default after mount. A
correct fix is to resolve one locale from the request before SSR, preload that
resource on both server/client and pass it through a provider instead of doing
the post-hydration switch. This is deliberately not hidden with hydration
suppression or client-only rendering.
