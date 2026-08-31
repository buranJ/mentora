# Mentora — Project Architecture

## Current baseline

Mentora is based on LearnHouse Community Edition `1.3.5`. Its upstream modular
monolith is preserved: changes stay in existing applications and use their
existing domain models and service boundaries.

| Layer | Current implementation |
| --- | --- |
| Frontend | Next.js, React, TypeScript, Tailwind CSS, shared UI components |
| Backend | FastAPI, Python, SQLModel, Alembic |
| Database | PostgreSQL with pgvector |
| Cache | Redis |
| Collaboration | LearnHouse Hocuspocus/Yjs collab server |
| Live classroom | LiveKit `v1.13.5`, behind a backend-owned token boundary |

## Principles

1. Modular monolith first.
2. Clear domain boundaries.
3. No unnecessary microservices.
4. Backend owns authorization.
5. Frontend never receives infrastructure secrets.
6. Keep changes upgrade-friendly relative to upstream LearnHouse.
7. Keep business logic separate from UI.
8. Put external realtime providers behind an abstraction.
9. Russian-first UX.
10. Keep MVP code production-ready.

## Local development

The project-local wrapper starts the same infrastructure used by the official
upstream CLI, then invokes `npx learnhouse dev`:

```bash
./scripts/dev.sh
```

It runs PostgreSQL, Redis, and the pinned LiveKit development server in Docker
and runs API, web, and collab locally.
Install Bun `1.4.0` and `uv` first. Copy the per-app example environment files
before the first run; the wrapper also copies them when they do not exist.
LearnHouse already ships a lazy-loaded Russian locale; use the existing
language selector while the Russian-first server/client locale policy is
introduced in a later phase.

After the initial admin bootstrap, load the small local test dataset with:

```bash
cd apps/api
uv run python scripts/seed_mentora_dev.py --confirm-development
```

The command is idempotent and creates three published courses, two instructors,
three students, three modules per course, and two lessons per module. Its
development-only password is `MentoraDevOnly!2026`.

Mentora uses host port `5433` for its Docker database, so an existing local
PostgreSQL on `5432` is never stopped or repurposed.

LiveKit is available locally at `ws://localhost:7880`. Its API secret is read
only by FastAPI from `apps/api/.env`; it is never added to the web environment
or frontend bundle. See [LiveKit development](development/livekit.md).

## Design readiness

The web app already centralizes Tailwind styling, shared components, dashboard
layouts, menu definitions, and responsive UI primitives. A future redesign
should evolve those layers instead of creating a second component system.
