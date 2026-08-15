#!/usr/bin/env bash
# Post-first-boot helper (brief §4): locate Ice and Fire configs and surface the
# griefing / spawn knobs to tune (dragon griefing -> low/none so wild dragons
# don't level player builds). Read-only — edit values by hand, then restart.
set -euo pipefail
cd "$(dirname "$0")/.."

found=0
for f in data/config/iceandfire*.toml data/config/iceandfire*.cfg \
         data/config/iceandfire/* data/world/serverconfig/iceandfire*; do
  [ -e "$f" ] || continue
  found=1
  echo "== $f"
  grep -inE 'grief|roar|spawn(chance|rate|_chance|_rate| chance)|generat|density' "$f" | head -40 || true
  echo
done

if [ "$found" -eq 0 ]; then
  echo "No Ice and Fire config found yet — boot the server once with the mod installed."
else
  echo "Edit the flagged values in place, snapshot, then: docker compose restart mc"
fi
