#!/usr/bin/env bash
# ZapeG citizens/heraldor debug paketi — TEK KOMUT, TEK DOSYA.
# Host'ta repo kökünden çalıştır:   bash scripts/citizens-debug-bundle.sh
# Çıktı:  citizens-debug-YYYYmmdd-HHMMSS.txt  (Ertu'ya bu dosyayı gönder)
#
# Her bölüm best-effort: kapalı bir konteyner veya eksik komut paketi
# durdurmaz, sadece o bölüm "yok" düşer. Hiçbir secret dosyaya yazılmaz
# (token/anahtar değerleri değil, yalnız var/yok durumu raporlanır).

# WINDOWS HOST NOTU: canlı sunucu Windows + WSL docker ise BUNU DEĞİL,
# scripts/citizens-debug-bundle.ps1 kullan (PowerShell'den, WSL gerekmez).
set -u
OUT="citizens-debug-$(date +%Y%m%d-%H%M%S).txt"
echo "yazılıyor: $OUT" >&2
exec >"$OUT" 2>&1

section() { printf '\n============ %s ============\n' "$1"; }

echo "ZapeG debug bundle — $(date -Is)"
echo "repo: $(git rev-parse --short HEAD 2>/dev/null || echo 'git yok') ($(git log -1 --format=%s 2>/dev/null | cut -c1-70))"

section "docker compose ps (tüm profiller)"
docker compose --profile citizens --profile heraldor --profile metrics ps || true

section "data/mods — zapeg/numen/cc-tweaked jarları"
ls -la data/mods 2>/dev/null | grep -iE "zapeg|numen|cc-tweaked" || echo "(bulunamadı / data/mods yok)"

section "citizen-brain imajı + yaşı + env (değerler gizli)"
docker inspect atm9-citizen-brain --format 'image={{.Config.Image}} created={{.Created}} started={{.State.StartedAt}} status={{.State.Status}}' 2>/dev/null || echo "(konteyner yok)"
docker inspect atm9-citizen-brain --format '{{range .Config.Env}}{{println .}}{{end}}' 2>/dev/null \
  | sed -E 's/^([A-Z0-9_]*(TOKEN|KEY|SECRET)[A-Z0-9_]*)=.+$/\1=<gizli:var>/' || true

section "rcon: citizen list"
docker compose exec -T mc rcon-cli "citizen list" || echo "(rcon/mc erişilemedi)"
section "rcon: citizen brain-status"
docker compose exec -T mc rcon-cli "citizen brain-status" || true
section "rcon: citizen jobs"
docker compose exec -T mc rcon-cli "citizen jobs" || true

section "mc log — citizens/numen/brain süzgeci (son 400 eşleşme)"
docker compose logs --no-color --tail 4000 mc 2>/dev/null | grep -iE "zapeg-citizens|numen|citizen|brain" | tail -400 || true

section "mc log — süzgeçsiz son 120 satır"
docker compose logs --no-color --tail 120 mc || true

section "citizen-brain log — son 300 satır"
docker compose logs --no-color --tail 300 citizen-brain 2>/dev/null || echo "(brain konteyneri yok/kapalı)"

section "brain SQLite özeti (tablolar + son işler; salt-okunur)"
docker compose exec -T citizen-brain python3 - <<'PYEOF' 2>/dev/null || echo "(sqlite özeti alınamadı)"
import json, sqlite3
con = sqlite3.connect("file:/data/citizens-brain.sqlite3?mode=ro", uri=True)
con.row_factory = sqlite3.Row
tables = [r[0] for r in con.execute(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
print("tablolar:", tables)
for table in tables:
    try:
        n = con.execute(f"SELECT COUNT(*) FROM '{table}'").fetchone()[0]
        print(f"\n-- {table}: {n} satır")
        if n and any(k in table.lower() for k in ("job", "turn", "event", "action")):
            for row in con.execute(f"SELECT * FROM '{table}' ORDER BY rowid DESC LIMIT 5"):
                compact = {}
                for key in row.keys():
                    value = row[key]
                    text = str(value)
                    compact[key] = text[:220] + "…" if len(text) > 220 else value
                print(json.dumps(compact, ensure_ascii=False, default=str)[:2000])
    except Exception as exc:  # tek tablo patlarsa geri kalanı sürsün
        print(f"-- {table}: HATA {exc}")
PYEOF

section "heraldor konteyneri + son 120 log"
docker compose --profile heraldor ps heraldor 2>/dev/null || true
docker compose --profile heraldor logs --no-color --tail 120 heraldor 2>/dev/null || echo "(heraldor konteyneri yok/kapalı)"

section "kubejs log — [zapeg] canary + kayıtları (hangi script yüklendi)"
grep -a "\[zapeg" data/logs/kubejs/server.log 2>/dev/null | tail -80 || echo "(zapeg kaydı yok)"
tail -60 data/logs/kubejs/server.log 2>/dev/null || echo "(kubejs logu yok)"

section "BİTTİ"
echo "Bu dosyayı olduğu gibi gönder: $OUT"

# not: /dev/tty bazı WSL/CI kabuklarında yok — stdout'u geri almayı DENEME.
# Dosya adı en başta stderr'e basılıyor; ayrıca dosyanın son satırında yazıyor.
