#!/usr/bin/env bash
# Rsync hot/config overrides into the live data dir. Repo-owned mod jars are
# intentionally excluded: itzg's version-aware MODS source installs those only
# during Minecraft container creation/startup.
# Copying is safe while the server runs. Plain server_scripts can hot-reload,
# but KubeJS data-pack advancements and FTB quest type changes need a planned
# full Minecraft restart before they become authoritative.
set -euo pipefail
cd "$(dirname "$0")/.."

rsync -av --exclude '/mods/' overrides/ data/

echo "Applied non-jar overrides. KubeJS data/ or FTB quest changes require: docker compose restart mc"
echo "After restart, check /kubejs errors and test the quest book with two clients."
echo "Repo-owned mod jar changes require recreating/restarting mc; they are installed through MODS."
