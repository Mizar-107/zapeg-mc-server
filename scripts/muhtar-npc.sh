#!/usr/bin/env bash
# Place/update, inspect or permanently remove the deterministic Easy NPC Muhtar.
set -euo pipefail
cd "$(dirname "$0")/.."

readonly MUHTAR_UUID="c9e6884a-57e1-44d4-8154-aedf54a12534"
readonly MUHTAR_IDENTIFIER="zapeg:muhtar"
readonly MUHTAR_DIMENSION="minecraft:overworld"
readonly PRESET_DIR="overrides/config/easy_npc/preset/humanoid/zapeg"
readonly LIVE_PRESET_DIR="data/config/easy_npc/preset/humanoid/zapeg"

usage() {
  cat <<'EOF'
Usage:
  scripts/muhtar-npc.sh apply v2 <x> <y> <z>
  scripts/muhtar-npc.sh apply v1 <x> <y> <z>  # legacy layout rollback
  scripts/muhtar-npc.sh list
  scripts/muhtar-npc.sh remove

Run snapshot.sh first. For apply/update/remove, keep Muhtar's chunk loaded.
The initial install also needs a Minecraft restart after apply-overrides.sh so
KubeJS registers the narrow quest bridge and FTB Quests loads the new chapters.
EOF
}

run_rcon() {
  docker compose exec -T mc rcon-cli "$@"
}

is_coordinate() {
  [[ "$1" =~ ^-?[0-9]+([.][0-9]+)?$ ]]
}

case "${1:-}" in
  apply)
    if [ "$#" -ne 5 ]; then
      usage >&2
      exit 2
    fi
    version="$2"
    x="$3"
    y="$4"
    z="$5"
    if [[ ! "$version" =~ ^v[0-9]+$ ]] ||
       ! is_coordinate "$x" || ! is_coordinate "$y" || ! is_coordinate "$z"; then
      echo "Version must look like v1 and coordinates must be absolute numbers." >&2
      exit 2
    fi
    preset_file="muhtar_${version}.npc.snbt"
    preset_id="easy_npc:preset/humanoid/zapeg/${preset_file}"
    if [ ! -f "${PRESET_DIR}/${preset_file}" ]; then
      echo "Tracked preset not found: ${PRESET_DIR}/${preset_file}" >&2
      exit 1
    fi
    if [ ! -f "${LIVE_PRESET_DIR}/${preset_file}" ]; then
      echo "Live preset not found. Run scripts/apply-overrides.sh first." >&2
      exit 1
    fi
    run_rcon execute in "$MUHTAR_DIMENSION" run easy_npc preset import custom \
      "$preset_id" "$x" "$y" "$z" "$MUHTAR_UUID"
    run_rcon easy_npc list identifier "$MUHTAR_IDENTIFIER"
    ;;
  list)
    if [ "$#" -ne 1 ]; then
      usage >&2
      exit 2
    fi
    run_rcon easy_npc list identifier "$MUHTAR_IDENTIFIER"
    ;;
  remove)
    if [ "$#" -ne 1 ]; then
      usage >&2
      exit 2
    fi
    run_rcon execute in "$MUHTAR_DIMENSION" run easy_npc delete "$MUHTAR_UUID"
    run_rcon easy_npc list identifier "$MUHTAR_IDENTIFIER"
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac
