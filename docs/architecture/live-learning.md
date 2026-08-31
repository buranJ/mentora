# Live learning — Phase 2 implementation

Mentora uses a small, course-scoped live classroom module. LearnHouse remains
the system of record for course access and user authorization; LiveKit is the
external self-hosted media transport only.

```text
LearnHouse
├── Course
├── Lesson / Chapter / Activity
├── User and organization RBAC
└── live-learning module
    └── LiveSession (belongs to one Course)

LiveKit Server
└── accessed only through a backend token/provider boundary
```

## Implemented boundary

`src/services/live_learning/livekit.py` is the sole LiveKit SDK boundary. It
reads `LIVEKIT_URL`, `LIVEKIT_API_KEY`, and `LIVEKIT_API_SECRET` server-side and
issues ten-minute participant tokens. Route handlers do not sign JWTs and the
frontend never receives the API secret.

`LiveSession` contains only the necessary application state: course,
organization, instructor, title, optional schedule, lifecycle timestamps and
status (`scheduled`, `live`, `ended`). It has a random `session_uuid` and an
opaque `mentora_live_<random>` room name. Neither room names nor participant
identities contain email, phone numbers or course names.

The join flow is:

```text
browser -> authenticated FastAPI /live-sessions/{id}/join
        -> load LiveSession + Course
        -> existing course RBAC READ check
        -> LiveKitService signs a short-lived, room-bound token
        -> browser connects directly to self-hosted LiveKit
```

Creating, starting and ending a session require existing course `UPDATE` RBAC.
Students receive room-join, subscribe, camera, microphone and data/chat grants;
instructors additionally receive screen-sharing. No client receives room admin,
room creation, recording or ingress permissions.

Attendance is intentionally deferred. Browser join/leave callbacks are not an
authoritative attendance source; a future phase should use verified LiveKit
webhooks before adding attendance records.

Recording, Egress, Ingress and persistent chat are not part of this module.
