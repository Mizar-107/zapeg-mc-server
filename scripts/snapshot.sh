#!/usr/bin/env bash
# Manual snapshot — MANDATORY before any mod/pack/config change (brief §6).
# Usage: scripts/snapshot.sh [label]
set -euo pipefail
cd "$(dirname "$0")/.."

label="${1:-manual}"
ts="$(date +%Y%m%d-%H%M%S)"
out="snapshots/${ts}-${label}.tar.gz"
mkdir -p snapshots

running="$(docker compose ps -q --status running mc 2>/dev/null || true)"

if [ -n "$running" ]; then
  docker compose exec mc rcon-cli save-off >/dev/null
  docker compose exec mc rcon-cli save-all flush >/dev/null
  sleep 3
fi

tar --exclude='data/cache' --exclude='data/logs' --exclude='data/libraries' \
    --exclude='data/versions' -czf "$out" data

if [ -n "$running" ]; then
  docker compose exec mc rcon-cli save-on >/dev/null
fi

echo "Snapshot: $out ($(du -h "$out" | cut -f1))"
