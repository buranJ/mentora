#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

copy_if_missing() {
  local target=$1
  local example=$2
  if [[ ! -f "$target" ]]; then
    cp "$example" "$target"
  fi
}

copy_if_missing apps/api/.env apps/api/.env.example
copy_if_missing apps/web/.env.local apps/web/.env.local.example
copy_if_missing apps/collab/.env apps/collab/.env.example

# Keep LearnHouse separate from a host PostgreSQL that already occupies 5432.
docker compose -f docker/docker-compose.mentora-dev.yml -p learnhouse-dev up -d

for _attempt in {1..30}; do
  if nc -z 127.0.0.1 7880 2>/dev/null; then
    break
  fi
  sleep 1
done

if ! nc -z 127.0.0.1 7880 2>/dev/null; then
  echo "LiveKit did not open localhost:7880. Inspect: docker logs mentora-livekit-dev" >&2
  exit 1
fi

npx --yes learnhouse@1.5.1 dev \
  --admin-email "${MENTORA_ADMIN_EMAIL:-admin@school.dev}" \
  --admin-password "${MENTORA_ADMIN_PASSWORD:-MentoraDevOnly!2026}"
