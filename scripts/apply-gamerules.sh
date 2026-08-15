#!/usr/bin/env bash
# Apply the agreed gamerules (see TUNING.md) to the CURRENT world via rcon.
# Run once after real-world creation; safe to re-run any time.
set -euo pipefail
cd "$(dirname "$0")/.."

rcon() { docker compose exec mc rcon-cli "$@"; }

# rule value   — edit here, TUNING.md is the source of truth
rules=(
  "keepInventory false"
  "playersSleepingPercentage 10"
  "doInsomnia false"
  "mobGriefing true"
  "doFireTick true"
)

for r in "${rules[@]}"; do
  # shellcheck disable=SC2086
  rcon gamerule $r
done

echo "Applied ${#rules[@]} gamerules. Verify: docker compose exec mc rcon-cli gamerule keepInventory"
