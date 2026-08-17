#!/usr/bin/env bash
# Rsync hot/config overrides into the live data dir. Repo-owned mod jars are
# intentionally excluded: itzg's version-aware MODS source installs those only
# during Minecraft container creation/startup.
# Copying is safe while the server runs. Plain server_scripts can hot-reload,
# but KubeJS data-pack advancements and FTB quest type changes need a planned
# full Minecraft restart before they become authoritative.
set -euo pipefail
cd "$(dirname "$0")/.."

npc_presets_source="overrides/config/easy_npc/preset/humanoid/zapeg"
npc_presets_live="data/config/easy_npc/preset/humanoid/zapeg"

# This subtree is repository-owned and deliberately mirrored with deletion so a
# retired ZapeG preset cannot survive as an untracked live file. Other Easy NPC
# preset directories may contain admin exports and are never delete-synced.
rsync -av --exclude '/mods/' \
  --exclude '/config/easy_npc/preset/humanoid/zapeg/' overrides/ data/
mkdir -p "$npc_presets_live"
rsync -av --delete "$npc_presets_source/" "$npc_presets_live/"

echo "Applied non-jar overrides and mirrored the repo-owned ZapeG Easy NPC presets."
echo "KubeJS data/, FTB quest or Easy NPC security changes require: docker compose restart mc"
echo "After restart, check /kubejs errors and test the quest book with two clients."
echo "Repo-owned mod jar changes require recreating/restarting mc; they are installed through MODS."
