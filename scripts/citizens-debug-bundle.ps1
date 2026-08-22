# ZapeG debug bundle - WINDOWS HOST version (the live server host is Windows,
# docker runs via WSL/Docker Desktop; the .sh twin is for real-Linux hosts).
# Usage (PowerShell, repo root or anywhere):
#   powershell -ExecutionPolicy Bypass -File scripts\citizens-debug-bundle.ps1
# Output: citizens-debug-<timestamp>.txt in the repo root. Send that file as-is.
# Every section is best-effort: a dead container just leaves a note.

$ErrorActionPreference = 'Continue'
$repo = Split-Path $PSScriptRoot -Parent
Set-Location $repo
$OutputEncoding = [Text.UTF8Encoding]::new($false)
$out = Join-Path $repo ("citizens-debug-" + (Get-Date -Format 'yyyyMMdd-HHmmss') + ".txt")
"ZapeG debug bundle (Windows) - $(Get-Date -Format o)" | Set-Content -Encoding UTF8 $out

function Sec([string]$title) {
    Add-Content $out ""
    Add-Content $out ("============ " + $title + " ============")
}
function Put($x) { $x 2>&1 | Out-String | Add-Content $out }

# --- pick a docker runner: native CLI first, then WSL ------------------------
$script:DockerPrefix = $null
try {
    $null = & docker version --format '{{.Server.Version}}' 2>$null
    if ($LASTEXITCODE -eq 0) { $script:DockerPrefix = @('docker') }
} catch {}
if (-not $script:DockerPrefix) {
    try {
        $null = & wsl -e docker version --format '{{.Server.Version}}' 2>$null
        if ($LASTEXITCODE -eq 0) { $script:DockerPrefix = @('wsl', '-e', 'docker') }
    } catch {}
}
function D {
    # invoke docker with the chosen prefix; args passed straight through
    if (-not $script:DockerPrefix) { return "docker erisimi yok (ne native ne WSL cevap verdi)" }
    $exe = $script:DockerPrefix[0]
    $lead = @()
    if ($script:DockerPrefix.Count -gt 1) { $lead = $script:DockerPrefix[1..($script:DockerPrefix.Count - 1)] }
    & $exe @($lead + $args) 2>&1
}

Sec "ortam"
Put ("docker runner: " + ($(if ($script:DockerPrefix) { $script:DockerPrefix -join ' ' } else { 'YOK' })))
Put (git rev-parse --short HEAD)
Put (git log --oneline -3)
git fetch origin --quiet 2>$null
Put (git status -sb)   # 'behind N' gorunuyorsa canli sunucu ESKI commit calistiriyor

Sec "docker compose ps (tum profiller)"
Put (D compose --profile citizens --profile heraldor --profile metrics ps)

Sec "data/mods - zapeg/numen/cc-tweaked jarlari"
if (Test-Path 'data\mods') {
    Put (Get-ChildItem 'data\mods' | Where-Object { $_.Name -match 'zapeg|numen|cc-tweaked' } | Format-Table Name, Length, LastWriteTime)
} else { Add-Content $out "(data\mods yok - data dizini WSL tarafinda olabilir; docker bolumlerine bak)" }

Sec "citizen-brain imaj + durum + env (secret degerleri maskeli)"
Put (D inspect atm9-citizen-brain --format 'image={{.Config.Image}} created={{.Created}} status={{.State.Status}} started={{.State.StartedAt}}')
$envDump = D inspect atm9-citizen-brain --format '{{range .Config.Env}}{{println .}}{{end}}'
Put ($envDump | Out-String -Stream | ForEach-Object { $_ -replace '^([A-Z0-9_]*(TOKEN|KEY|SECRET)[A-Z0-9_]*)=.+$', '$1=<gizli:var>' })

Sec "rcon: citizen list / brain-status / jobs"
Put (D compose exec -T mc rcon-cli "citizen list")
Put (D compose exec -T mc rcon-cli "citizen brain-status")
Put (D compose exec -T mc rcon-cli "citizen jobs")

Sec "mc log - citizens/numen/brain suzgeci (son 400 eslesme)"
Put (D compose logs --no-color --tail 4000 mc | Select-String -Pattern 'zapeg-citizens|numen|citizen|brain' | Select-Object -Last 400)

Sec "mc log - suzgecsiz son 120 satir"
Put (D compose logs --no-color --tail 120 mc)

Sec "citizen-brain log - son 300 satir"
Put (D compose logs --no-color --tail 300 citizen-brain)

Sec "brain SQLite ozeti (salt-okunur; tablolar + son isler)"
$py = @'
import json, sqlite3
con = sqlite3.connect("file:/data/citizens-brain.sqlite3?mode=ro", uri=True)
con.row_factory = sqlite3.Row
tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
print("tables:", tables)
for table in tables:
    try:
        n = con.execute("SELECT COUNT(*) FROM '%s'" % table).fetchone()[0]
        print("\n-- %s: %d rows" % (table, n))
        if n and any(k in table.lower() for k in ("job", "turn", "event", "action")):
            for row in con.execute("SELECT * FROM '%s' ORDER BY rowid DESC LIMIT 5" % table):
                compact = {}
                for key in row.keys():
                    text = str(row[key])
                    compact[key] = text[:220] + "..." if len(text) > 220 else row[key]
                print(json.dumps(compact, ensure_ascii=False, default=str)[:2000])
    except Exception as exc:
        print("-- %s: ERROR %s" % (table, exc))
'@
$tmp = Join-Path $env:TEMP 'zapeg-brain-dump.py'
Set-Content -Encoding Ascii $tmp $py
try {
    if ($script:DockerPrefix) {
        $exe = $script:DockerPrefix[0]
        $lead = @()
        if ($script:DockerPrefix.Count -gt 1) { $lead = $script:DockerPrefix[1..($script:DockerPrefix.Count - 1)] }
        Put (Get-Content $tmp -Raw | & $exe @($lead + @('compose', 'exec', '-T', 'citizen-brain', 'python3', '-')))
    }
} catch { Add-Content $out "(sqlite ozeti alinamadi: $_)" }
Remove-Item $tmp -ErrorAction SilentlyContinue

Sec "heraldor konteyneri + son 120 log"
Put (D compose --profile heraldor ps heraldor)
Put (D compose --profile heraldor logs --no-color --tail 120 heraldor)

Sec "kubejs log - [zapeg] canary + [zapeg-lore] kayitlari (KRITIK BOLUM)"
$kubejsLog = 'data\logs\kubejs\server.log'
if (Test-Path $kubejsLog) {
    Add-Content $out "-- '[zapeg' eslesmeleri (hangi script yuklendi, hangi kapi calisiyor):"
    Put (Select-String -Path $kubejsLog -SimpleMatch '[zapeg' | Select-Object -Last 80 | ForEach-Object Line)
    Add-Content $out "-- son 60 satir:"
    Put (Get-Content $kubejsLog -Tail 60)
} else {
    Add-Content $out "(data\logs\kubejs\server.log Windows tarafinda yok - docker icinden dene:)"
    Put (D compose exec -T mc sh -c "grep -a '\[zapeg' /data/logs/kubejs/server.log | tail -80; echo ---; tail -60 /data/logs/kubejs/server.log")
}

Sec "BITTI"
Add-Content $out ("Bu dosyayi oldugu gibi gonder: " + $out)
Write-Host "Debug paketi hazir: $out"
