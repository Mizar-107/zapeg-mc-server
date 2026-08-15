#!/usr/bin/env bash
# Chunky pregen around world spawn (brief §6: ~5–8k radius before opening).
# Usage: scripts/pregen.sh [radius_blocks]   (default 6000)
set -euo pipefail
cd "$(dirname "$0")/.."

r="${1:-6000}"
rcon() { docker compose exec mc rcon-cli "$@"; }

rcon chunky spawn
rcon chunky radius "$r"
rcon chunky start

cat <<EOF
Pregen started (radius ${r}).
  progress : docker compose exec mc rcon-cli chunky progress
  pause    : docker compose exec mc rcon-cli chunky pause
  resume   : docker compose exec mc rcon-cli chunky continue
Expect hours of elevated CPU; fine to leave running overnight.
EOF
