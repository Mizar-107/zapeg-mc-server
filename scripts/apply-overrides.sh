#!/usr/bin/env bash
# Rsync repo overrides/ (mirrors data/ layout) into the live data dir.
# Safe while the server runs; KubeJS server scripts hot-reload with
# /kubejs reload server_scripts
set -euo pipefail
cd "$(dirname "$0")/.."

rsync -av overrides/ data/

echo "Applied. If KubeJS scripts changed: /kubejs reload server_scripts (in-game, OP)."
