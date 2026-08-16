#!/usr/bin/env bash
# Manual snapshot — MANDATORY before any mod/pack/config change (brief §6).
# Usage: scripts/snapshot.sh [label]
set -euo pipefail
cd "$(dirname "$0")/.."

label="${1:-manual}"
ts="$(date +%Y%m%d-%H%M%S)"
out="snapshots/${ts}-${label}.tar.gz"
partial="${out}.partial"
mkdir -p snapshots

running="$(docker compose ps -q --status running mc 2>/dev/null || true)"
backup_running="$(docker compose ps -q --status running backup 2>/dev/null || true)"
saves_paused=false
backup_stopped=false

resume_saves() {
  if [ "$saves_paused" = true ]; then
    if ! docker compose exec -T mc rcon-cli save-on >/dev/null; then
      echo "UYARI: save-on başarısız; sunucu logunu hemen kontrol edin." >&2
      return 1
    fi
    saves_paused=false
  fi
}

restart_backup() {
  if [ "$backup_stopped" = true ]; then
    # Restore the exact stopped container; `up` could recreate dependencies or
    # unexpectedly start mc when this was a cold snapshot.
    if ! docker compose start backup >/dev/null; then
      return 1
    fi
    backup_stopped=false
  fi
}

cleanup() {
  status=$?
  cleanup_status=0
  trap - EXIT
  if ! resume_saves; then
    cleanup_status=1
  fi
  if ! restart_backup; then
    echo "UYARI: backup servisi yeniden başlatılamadı." >&2
    cleanup_status=1
  fi
  if [ -f "$partial" ]; then
    rm -f -- "$partial"
  fi
  if [ "$status" -ne 0 ]; then
    exit "$status"
  fi
  exit "$cleanup_status"
}

# Otomatik backup da save-on/off kullanır; iki arşivin birbirinin tutarlılığını
# bozmasını önlemek için manuel snapshot boyunca onu durdur, çıkışta geri aç.
trap cleanup EXIT
if [ -n "$backup_running" ]; then
  backup_stopped=true
  docker compose stop backup >/dev/null
fi

if [ -n "$running" ]; then
  # Komut sunucuya ulaşıp istemci hata verebilir; önce flag koymak save-on
  # cleanup'ını o küçük hata penceresinde de güvenli kılar.
  saves_paused=true
  docker compose exec -T mc rcon-cli save-off >/dev/null
  docker compose exec -T mc rcon-cli save-all flush >/dev/null
  sleep 3
fi

tar --exclude='data/cache' --exclude='data/logs' --exclude='data/libraries' \
    --exclude='data/versions' --exclude='data/bluemap' -czf "$partial" data
mv -- "$partial" "$out"

resume_saves
restart_backup
trap - EXIT

echo "Snapshot: $out ($(du -h "$out" | cut -f1))"
