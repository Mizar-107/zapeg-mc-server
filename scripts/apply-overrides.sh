#!/usr/bin/env bash
# Rsync hot/config overrides into the live data dir. Repo-owned mod jars are
# intentionally excluded: itzg's version-aware MODS source installs those only
# during Minecraft container creation/startup.
# Safe while the server runs; KubeJS server scripts hot-reload with
# /kubejs reload server_scripts
set -euo pipefail
cd "$(dirname "$0")/.."

rsync -av --exclude '/mods/' overrides/ data/

echo "Applied non-jar overrides. If KubeJS scripts changed: /kubejs reload server_scripts (in-game, OP)."
echo "Repo-owned mod jar changes require recreating/restarting mc; they are installed through MODS."
