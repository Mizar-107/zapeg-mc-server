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
    [string]$OutDir = [Environment]::GetFolderPath('Desktop'),
    [switch]$ExtrasOnly   # sadece bizim eklediğimiz jar'ları zipler (Yol A oyuncuları için)
)

# Bizim eklediğimiz modların dosya adı önekleri — extras/cf-mods.txt ile senkron tut
$extraPrefixes = @('iceandfire', 'citadel', 'ImmersivePetroleum', 'alexscaves', 'mowziesmobs',
                   'easy_npc', 'aquamirae', 'born_in_chaos', 'DungeonsArise', 'simplyswords',
                   'bettercombat', 'player-animation-lib')

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $ProfileDir)) {
    Write-Error "Profil bulunamadı: $ProfileDir  (-ProfileDir ile doğru yolu ver)"
}

if ($ExtrasOnly) {
    # Yol A oyuncuları için: sadece ekstra mod jar'ları -> mods klasörüne açılır
    $stamp = Get-Date -Format 'yyyyMMdd'
    $out = Join-Path $OutDir "zapeg-extra-mods-$stamp.zip"
    $jars = Get-ChildItem (Join-Path $ProfileDir 'mods') -Filter '*.jar' |
        Where-Object { $n = $_.Name; ($extraPrefixes | Where-Object { $n -like "$_*" }).Count -gt 0 }
    if ($jars.Count -eq 0) { Write-Error "Ekstra mod jar'ı bulunamadı — önce hepsini kur." }
    if (Test-Path $out) { Remove-Item $out -Force }
    Compress-Archive -Path $jars.FullName -DestinationPath $out
    Write-Host "Hazır: $out ($($jars.Count) jar)" -ForegroundColor Green
    Write-Host "Oyuncular bunu profildeki mods klasörünün İÇİNE açar."
    exit 0
}

# Oyuna gereken klasörler — saves/logs/screenshots gibi kişisel şeyler BİLEREK yok.
$include = @('mods', 'config', 'kubejs', 'defaultconfigs', 'packmenu', 'scripts', 'shaderpacks')

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

# --- ZapeG görsel ön-ayarı: shaders açık başlasın (repo: client/defaults) ---
$repoRoot = Split-Path $PSScriptRoot -Parent
$defaults = Join-Path $repoRoot 'client\defaults'
if (Test-Path $defaults) {
    Copy-Item (Join-Path $defaults 'options.txt') -Destination $staging -Force
    $cfgDir = Join-Path $staging 'config'
    if (-not (Test-Path $cfgDir)) { New-Item -ItemType Directory -Path $cfgDir | Out-Null }
    Copy-Item (Join-Path $defaults 'config\oculus.properties') -Destination $cfgDir -Force
    Write-Host "  + görsel ön-ayar (options.txt + oculus.properties)"

    # Shaderpack dosya adını gerçek dosyadan tespit et
    $spDir = Join-Path $staging 'shaderpacks'
    if (Test-Path $spDir) {
        $pack = @(Get-ChildItem $spDir -Filter 'ComplementaryUnbound*.zip') +
                @(Get-ChildItem $spDir -Filter 'ComplementaryReimagined*.zip') +
                @(Get-ChildItem $spDir -Filter '*.zip') | Select-Object -First 1
        if ($pack) {
            $prop = Join-Path $cfgDir 'oculus.properties'
            (Get-Content $prop) -replace '^shaderPack=.*', "shaderPack=$($pack.Name)" | Set-Content $prop
            Write-Host "  + shader varsayılanı: $($pack.Name)"
        }
    }
}

if (Test-Path $out) { Remove-Item $out -Force }
Compress-Archive -Path (Join-Path $staging '*') -DestinationPath $out -CompressionLevel Optimal
Remove-Item $staging -Recurse -Force

$size = [math]::Round((Get-Item $out).Length / 1MB, 1)
Write-Host ""
Write-Host "Hazır: $out (${size} MB)" -ForegroundColor Green
Write-Host "Offline arkadaşlar bunu launcher'ın oyun klasörüne açar (docs/PLAYER-SETUP-TR.md → Yol B)."
