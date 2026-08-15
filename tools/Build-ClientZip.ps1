# Build-ClientZip.ps1 — ZapeG instance zip üretici (Yol B / offline oyuncular için)
# Çalışan bir CurseForge App kurulumundan paylaşimlik zip çıkarır.
#
# Kullanım (PowerShell):
#   .\Build-ClientZip.ps1
#   .\Build-ClientZip.ps1 -ProfileDir "D:\CF\Instances\All the Mods 9"
#
# Çıktı: Desktop\zapeg-client-<tarih>.zip → Drive'a at, gruba linkle.

param(
    [string]$ProfileDir = "$env:USERPROFILE\curseforge\minecraft\Instances\All the Mods 9",
    [string]$OutDir = [Environment]::GetFolderPath('Desktop')
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $ProfileDir)) {
    Write-Error "Profil bulunamadı: $ProfileDir  (-ProfileDir ile doğru yolu ver)"
}

# Oyuna gereken klasörler — saves/logs/screenshots gibi kişisel şeyler BİLEREK yok.
$include = @('mods', 'config', 'kubejs', 'defaultconfigs', 'packmenu', 'scripts')

$stamp = Get-Date -Format 'yyyyMMdd'
$out = Join-Path $OutDir "zapeg-client-$stamp.zip"
$staging = Join-Path $env:TEMP "zapeg-client-staging"

if (Test-Path $staging) { Remove-Item $staging -Recurse -Force }
New-Item -ItemType Directory -Path $staging | Out-Null

$found = 0
foreach ($d in $include) {
    $src = Join-Path $ProfileDir $d
    if (Test-Path $src) {
        Copy-Item $src -Destination (Join-Path $staging $d) -Recurse
        $found++
        Write-Host "  + $d"
    }
}
if ($found -eq 0) { Write-Error "Hiçbir pack klasörü bulunamadı — ProfileDir doğru mu?" }

if (Test-Path $out) { Remove-Item $out -Force }
Compress-Archive -Path (Join-Path $staging '*') -DestinationPath $out -CompressionLevel Optimal
Remove-Item $staging -Recurse -Force

$size = [math]::Round((Get-Item $out).Length / 1MB, 1)
Write-Host ""
Write-Host "Hazır: $out (${size} MB)" -ForegroundColor Green
Write-Host "Offline arkadaşlar bunu launcher'ın oyun klasörüne açar (docs/PLAYER-SETUP-TR.md → Yol B)."
