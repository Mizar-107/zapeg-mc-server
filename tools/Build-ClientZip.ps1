# Build-ClientZip.ps1 — ZapeG oyuncu paketi üretici
#
# Lisanslı oyuncular için önerilen çıktı:
#   .\Build-ClientZip.ps1 -PatchOnly -WriteInventoryLock  # bir kez; incele
#   .\Build-ClientZip.ps1 -PatchOnly                      # sonra paketi üret
#   -> ZapeG-Kurulum-Yamasi-ATM9-1.1.1-YYYYMMDD.zip
#   Oyuncu bu TEK zip'i ATM9 profil köküne açar. mods/, shader ayarı ve
#   PackMenu logosu doğru klasör yapısıyla birlikte gelir. Kişisel
#   options.txt dosyasına dokunulmaz.
#
# Offline oyuncular için oyun-dizini payload'ı:
#   .\Build-ClientZip.ps1 -WriteInventoryLock   # bir kez; dosyayı incele
#   .\Build-ClientZip.ps1                       # sonra paketi üret
#   -> ZapeG-Offline-ATM9-1.1.1-YYYYMMDD.zip
#   Bu bir launcher profili veya Forge kurucusu değildir; izole Forge 47.4.10
#   profilinin oyun dizinine açılır (zip içindeki INSTALL-TR.txt'ye bakın).

[CmdletBinding()]
param(
    [string]$ProfileDir = "$env:USERPROFILE\curseforge\minecraft\Instances\All the Mods 9",
    [string]$OutDir = [Environment]::GetFolderPath('Desktop'),
    [Alias('ExtrasOnly')]
    [switch]$PatchOnly,
    [switch]$SkipProfileCheck,
    [string]$InventoryLockFile,
    [switch]$WriteInventoryLock
)

$ErrorActionPreference = 'Stop'

$packVersion = '1.1.1'
$packFileId = '7097953'
$forgeVersion = '47.4.10'

# Her ek moddan TAM BİR, TAM SÜRÜM jar bulunmalı. Dosya adları
# extras/cf-mods.txt, docker-compose.yml ve oyuncu rehberindeki pinlerle
# senkron kalır. Yalnız önek kontrolü eski bir jar'ı yanlışlıkla kabul eder.
$extraMods = @(
    [pscustomobject]@{ Name = 'Ice and Fire';        Prefix = 'iceandfire';           FileName = 'iceandfire-2.1.13-1.20.1-beta-5.jar';               FileId = '5633453'; Pin = 'CurseForge file 5633453' },
    [pscustomobject]@{ Name = 'Citadel';             Prefix = 'citadel';              FileName = 'citadel-2.6.3-1.20.1.jar';                          FileId = '7476570'; Pin = 'CurseForge file 7476570' },
    [pscustomobject]@{ Name = 'Immersive Petroleum'; Prefix = 'ImmersivePetroleum';    FileName = 'ImmersivePetroleum-1.20.1-4.3.1-36b.jar';           FileId = '8499079'; Pin = 'CurseForge file 8499079' },
    [pscustomobject]@{ Name = "Alex's Caves";       Prefix = 'alexscaves';            FileName = 'alexscaves-2.0.2.jar';                              FileId = '5848216'; Pin = 'CurseForge file 5848216' },
    [pscustomobject]@{ Name = "Mowzie's Mobs";      Prefix = 'mowziesmobs';           FileName = 'mowziesmobs-1.8.2.jar';                             FileId = '7815705'; Pin = 'CurseForge file 7815705' },
    [pscustomobject]@{ Name = 'Easy NPC Bundle';     Prefix = 'easy_npc_bundle';       FileName = 'easy_npc_bundle-forge-1.20.1-7.7.7.jar';            FileId = '8644040'; Pin = 'CurseForge file 8644040' },
    [pscustomobject]@{ Name = 'Easy NPC Core';       Prefix = 'easy_npc-forge';        FileName = 'easy_npc-forge-1.20.1-7.7.7.jar';                   FileId = '8644032'; Pin = 'CurseForge file 8644032' },
    [pscustomobject]@{ Name = 'Easy NPC Config UI';  Prefix = 'easy_npc_config_ui';    FileName = 'easy_npc_config_ui-forge-1.20.1-7.7.7.jar';         FileId = '8644036'; Pin = 'CurseForge file 8644036' },
    [pscustomobject]@{ Name = 'Aquamirae';           Prefix = 'aquamirae';             FileName = 'aquamirae-forge-1.20.1-7.1.10.jar';                 FileId = '8558369'; Pin = 'CurseForge file 8558369' },
    [pscustomobject]@{ Name = 'Fragmentum';           Prefix = 'fragmentum';            FileName = 'fragmentum-forge-1.20.1-1.5.2.jar';                 FileId = '8506891'; Pin = 'CurseForge file 8506891' },
    [pscustomobject]@{ Name = 'Born in Chaos';       Prefix = 'born_in_chaos';         FileName = 'born_in_chaos_[Forge]1.20.1_1.7.5.jar';             FileId = '7917933'; Pin = 'CurseForge file 7917933' },
    [pscustomobject]@{ Name = 'When Dungeons Arise'; Prefix = 'DungeonsArise';         FileName = 'DungeonsArise-1.20.1-2.1.57-release.jar';           FileId = '4798432'; Pin = 'CurseForge file 4798432' },
    [pscustomobject]@{ Name = 'Simply Swords';       Prefix = 'simplyswords';          FileName = 'simplyswords-forge-1.56.0-1.20.1.jar';              FileId = '5639538'; Pin = 'CurseForge file 5639538' },
    [pscustomobject]@{ Name = 'Valkyrien Skies';     Prefix = 'valkyrienskies';        FileName = 'valkyrienskies-120-2.4.11.jar';                     FileId = '7906689'; Pin = 'CurseForge file 7906689' },
    [pscustomobject]@{ Name = 'Eureka';              Prefix = 'eureka';                FileName = 'eureka-1201-1.6.3.jar';                             FileId = '7979379'; Pin = 'CurseForge file 7979379' },
    [pscustomobject]@{ Name = 'Better Combat';       Prefix = 'bettercombat';          FileName = 'bettercombat-forge-1.9.0+1.20.1.jar';               FileId = $null;     Pin = 'Modrinth 1.9.0+1.20.1-forge' },
    [pscustomobject]@{ Name = 'playerAnimator';      Prefix = 'player-animation-lib'; FileName = 'player-animation-lib-forge-1.0.2-rc1+1.20.jar';     FileId = $null;     Pin = 'Modrinth 1.0.2-rc1+1.20-forge' }
)

function Assert-SourceProfile {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
        throw "Profil bulunamadı: $Path  (-ProfileDir ile doğru yolu verin.)"
    }

    $modsDir = Join-Path $Path 'mods'
    if (-not (Test-Path -LiteralPath $modsDir -PathType Container)) {
        throw "Bu bir Minecraft profil kökü gibi görünmüyor; mods klasörü yok: $Path"
    }

    if ($SkipProfileCheck) {
        Write-Warning 'ATM9 sürüm doğrulaması -SkipProfileCheck nedeniyle atlandı.'
        return [pscustomobject]@{ Verified = $false; Metadata = $null }
    }

    $instanceFile = Join-Path $Path 'minecraftinstance.json'
    if (-not (Test-Path -LiteralPath $instanceFile -PathType Leaf)) {
        throw "CurseForge profil bilgisi bulunamadı: $instanceFile`nDoğru ATM9 profilini seçin veya yalnızca bilinçli olarak -SkipProfileCheck kullanın."
    }

    try {
        $instance = Get-Content -Raw -LiteralPath $instanceFile | ConvertFrom-Json
    }
    catch {
        throw "CurseForge profil bilgisi geçerli JSON değil: $instanceFile"
    }

    $actualFileId = [string]$instance.installedModpack.fileID
    $actualMinecraft = [string]$instance.baseModLoader.minecraftVersion
    $loaderValues = @(
        [string]$instance.baseModLoader.forgeVersion,
        [string]$instance.baseModLoader.name,
        [string]$instance.baseModLoader.mavenVersionString
    ) | Where-Object { $_ }
    $acceptedForgeValues = @(
        $forgeVersion,
        "forge-$forgeVersion",
        "1.20.1-$forgeVersion",
        "net.minecraftforge:forge:1.20.1-$forgeVersion"
    )
    $forgeMatches = @($loaderValues | Where-Object { $_ -in $acceptedForgeValues })
    if ($actualFileId -ne $packFileId) {
        throw "Seçilen profil ATM9 $packVersion (CurseForge file $packFileId) olarak doğrulanamadı. Profil sürümünü CurseForge'dan kontrol edin."
    }
    if ($actualMinecraft -ne '1.20.1' -or $forgeMatches.Count -eq 0) {
        $foundLoaders = if ($loaderValues.Count) { $loaderValues -join ', ' } else { '(boş)' }
        throw "Profilin loader bilgisi uyuşmuyor. Beklenen Minecraft 1.20.1 / Forge $forgeVersion; bulunan Minecraft '$actualMinecraft' / loader '$foundLoaders'."
    }

    return [pscustomobject]@{ Verified = $true; Metadata = $instance }
}

function Get-ValidatedExtraJars {
    param(
        [string]$ModsDir,
        [object]$InstanceMetadata
    )

    $allJars = @(Get-ChildItem -LiteralPath $ModsDir -Filter '*.jar' -File)
    $selected = @()
    $problems = @()

    foreach ($mod in $extraMods) {
        $matches = @($allJars | Where-Object { $_.Name -like "$($mod.Prefix)*" })
        if ($matches.Count -eq 0) {
            $problems += "EKSİK: $($mod.Name) (beklenen dosya öneki: $($mod.Prefix))"
            continue
        }
        if ($matches.Count -gt 1) {
            $names = ($matches.Name | Sort-Object) -join ', '
            $problems += "ÇİFT SÜRÜM: $($mod.Name) -> $names"
            continue
        }
        if ($matches[0].Name -ine $mod.FileName) {
            $problems += "YANLIŞ SÜRÜM: $($mod.Name) -> $($matches[0].Name); beklenen $($mod.FileName) ($($mod.Pin))"
            continue
        }
        if ($mod.FileId -and $InstanceMetadata) {
            $metadataMatches = @(
                $InstanceMetadata.installedAddons |
                    Where-Object { [string]$_.installedFile.id -eq $mod.FileId }
            )
            if ($metadataMatches.Count -ne 1) {
                $problems += "KAYNAK PIN DOĞRULANAMADI: $($mod.Name) -> CurseForge file $($mod.FileId) profil metadatasında tam bir kez bulunmalı"
                continue
            }
        }
        $selected += $matches[0]
    }

    if ($problems.Count -gt 0) {
        throw "ZapeG ek mod seti doğrulanamadı:`n - $($problems -join "`n - ")`nEksik modu kurun veya eski/çift jar'ı silip tekrar deneyin."
    }

    if ($selected.Count -ne $extraMods.Count) {
        throw "İç hata: $($extraMods.Count) yerine $($selected.Count) ek mod seçildi."
    }

    return $selected
}

function Get-ModInventoryLines {
    param([System.IO.FileInfo[]]$Jars)

    return @(
        $Jars |
            Sort-Object Name |
            ForEach-Object {
                $hash = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
                "$hash  $($_.Name)"
            }
    )
}

function New-ModInventoryLock {
    param(
        [System.IO.FileInfo[]]$Jars,
        [string]$Path,
        [string]$Mode
    )

    if (Test-Path -LiteralPath $Path) {
        throw "Envanter kilidi zaten var; gözden geçirilmiş dosyayı otomatik ezmeyeceğim: $Path"
    }
    $parent = Split-Path $Path -Parent
    if ($parent -and -not (Test-Path -LiteralPath $parent -PathType Container)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    $lines = @(
        "# ZapeG $Mode client mod inventory — verified source; review before distributing.",
        "# ATM9 $packVersion / CurseForge file $packFileId / Forge $forgeVersion",
        '# Format: SHA256<two spaces>exact jar filename',
        '# Any added, removed, renamed or changed jar makes the build fail.',
        ''
    ) + @(Get-ModInventoryLines -Jars $Jars)
    $lines | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Assert-ModInventoryLock {
    param(
        [System.IO.FileInfo[]]$Jars,
        [string]$Path
    )

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Bu paket modu için incelenmiş jar envanter kilidi yok: $Path`nÖnce -WriteInventoryLock ile aday dosyayı üretin, listeyi inceleyip repoya ekleyin, sonra tekrar çalıştırın."
    }

    $expected = @(
        Get-Content -LiteralPath $Path |
            Where-Object { $_.Trim() -and -not $_.TrimStart().StartsWith('#') }
    )
    $actual = @(Get-ModInventoryLines -Jars $Jars)
    $delta = @(Compare-Object -ReferenceObject $expected -DifferenceObject $actual -CaseSensitive)
    if ($delta.Count -gt 0) {
        $detail = @($delta | Select-Object -First 12 | ForEach-Object { "$($_.SideIndicator) $($_.InputObject)" }) -join "`n"
        throw "Kaynak jar listesi incelenmiş envanter kilidiyle uyuşmuyor. Paket üretilmedi.`n$detail"
    }
}

function New-StagingRoot {
    $path = Join-Path ([IO.Path]::GetTempPath()) ("zapeg-client-" + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $path | Out-Null
    return $path
}

function Remove-StagingRoot {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) { return }
    $resolved = [IO.Path]::GetFullPath($Path)
    $tempRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath())
    $leaf = Split-Path $resolved -Leaf
    if (-not $resolved.StartsWith($tempRoot, [StringComparison]::OrdinalIgnoreCase) -or
        $leaf -notlike 'zapeg-client-*') {
        throw "Güvenlik nedeniyle geçici klasör silinmedi: $resolved"
    }
    Remove-Item -LiteralPath $resolved -Recurse -Force
}

function Add-ZapeGClientLayer {
    param(
        [string]$Staging,
        [string]$Mode
    )

    $repoRoot = Split-Path $PSScriptRoot -Parent
    $defaults = Join-Path $repoRoot 'client\defaults'
    $options = Join-Path $defaults 'options.txt'
    $oculus = Join-Path $defaults 'config\oculus.properties'
    if (-not (Test-Path -LiteralPath $oculus) -or
        ($Mode -eq 'offline' -and -not (Test-Path -LiteralPath $options))) {
        throw 'Repo içindeki ZapeG görsel varsayılanları eksik.'
    }

    # options.txt oyuncunun tüm tuş, dil, ses, video ve erişilebilirlik
    # ayarlarıdır. Mevcut CurseForge profiline uygulanan yamada asla ezme.
    # Yalnız sıfırdan kurulan offline profil payload'ında varsayılan olarak ekle.
    if ($Mode -eq 'offline') {
        Copy-Item -LiteralPath $options -Destination (Join-Path $Staging 'options.txt') -Force
    }
    $configDir = Join-Path $Staging 'config'
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null
    Copy-Item -LiteralPath $oculus -Destination (Join-Path $configDir 'oculus.properties') -Force

    $packMenu = Join-Path $repoRoot 'client\packmenu'
    if (Test-Path -LiteralPath $packMenu -PathType Container) {
        $packMenuOut = Join-Path $Staging 'packmenu'
        New-Item -ItemType Directory -Path $packMenuOut -Force | Out-Null
        Get-ChildItem -LiteralPath $packMenu -Force |
            Copy-Item -Destination $packMenuOut -Recurse -Force
    }

    # Gerçek shaderpack dosya adını o profile göre ayarla.
    $shaderDir = Join-Path $Staging 'shaderpacks'
    if (Test-Path -LiteralPath $shaderDir -PathType Container) {
        $shader = @(
            @(Get-ChildItem -LiteralPath $shaderDir -Filter 'ComplementaryUnbound*.zip' -File),
            @(Get-ChildItem -LiteralPath $shaderDir -Filter 'ComplementaryReimagined*.zip' -File),
            @(Get-ChildItem -LiteralPath $shaderDir -Filter '*.zip' -File)
        ) | ForEach-Object { $_ } | Select-Object -First 1

        if ($shader) {
            $oculusOut = Join-Path $configDir 'oculus.properties'
            (Get-Content -LiteralPath $oculusOut) -replace '^shaderPack=.*', "shaderPack=$($shader.Name)" |
                Set-Content -LiteralPath $oculusOut -Encoding UTF8
        }
    }

    $installLines = if ($Mode -eq 'patch') {
        @(
            'ZapeG KURULUM YAMASI — ATM9 1.1.1',
            '',
            '1. CurseForge App içinde All the Mods 9 sürüm 1.1.1 kurulu olsun.',
            '2. Profile Options / Profil Seçenekleri içinde modloader sürümünü Forge 47.4.10 yap.',
            '3. Profil menüsünde ... > Open Folder / Klasörü Aç seçeneğine bas.',
            '4. Minecraft ve CurseForge kapalıyken bu zip içeriğini O KLASÖRÜN KÖKÜNE çıkar.',
            '5. ZapeG dosyaları için üzerine yazma sorulursa onayla. Kişisel options.txt ayarların bu yamada yoktur ve korunur.',
            '6. Sonuçta mods\iceandfire-...jar doğrudan görünmeli.',
            '7. Oyunu başlat. Kullanıcı adını değiştirme; whitelist ve envanter o ada bağlıdır.',
            '',
            'Zip içinde yeniden bir ZapeG klasörü oluşturma. mods klasörü profil kökünde olmalı.'
        )
    } else {
        @(
            'ZapeG OFFLINE OYUN-DİZİNİ PAKETİ — ATM9 1.1.1 / Forge 47.4.10',
            '',
            'BU ZIP BİR LAUNCHER VEYA FORGE KURUCUSU DEĞİLDİR.',
            '1. Launcher içinde Minecraft 1.20.1 + Forge 47.4.10 kullanan İZOLE bir profil oluştur.',
            '2. Launcher sorarsa Java 17 seç. Profili bir kez açıp kapat.',
            '3. Minecraft ve launcher kapalıyken bu zip içeriğini o profilin OYUN KLASÖRÜNE çıkar.',
            '4. Sonuçta mods\iceandfire-...jar doğrudan görünmeli; iç içe ZapeG klasörü olmamalı.',
            '5. Sabit bir kullanıcı adı seç ve Ertu''ya whitelist için bildir. Sonradan değiştirme.'
        )
    }
    $installLines | Set-Content -LiteralPath (Join-Path $Staging 'INSTALL-TR.txt') -Encoding UTF8
}

function Write-BuildManifest {
    param(
        [string]$Staging,
        [string]$Mode,
        [bool]$ProfileVerified
    )

    $verification = if ($ProfileVerified) { 'PASSED' } else { 'SKIPPED — UNVERIFIED BUILD' }
    $lines = @(
        'ZapeG client build manifest',
        "Mode: $Mode",
        "Expected target: ATM9 $packVersion (CurseForge file $packFileId), Forge $forgeVersion",
        "Source profile verification: $verification",
        "Built: $((Get-Date).ToString('yyyy-MM-dd HH:mm:ss zzz'))",
        ''
    )
    $lines += 'Pinned ZapeG additions:'
    foreach ($mod in $extraMods) {
        $lines += "- $($mod.FileName) [$($mod.Pin)]"
    }
    $lines += ''
    $lines += 'Packaged jar SHA-256:'
    $modsDir = Join-Path $Staging 'mods'
    if (Test-Path -LiteralPath $modsDir) {
        foreach ($jar in Get-ChildItem -LiteralPath $modsDir -Filter '*.jar' -File | Sort-Object Name) {
            $hash = (Get-FileHash -LiteralPath $jar.FullName -Algorithm SHA256).Hash
            $lines += "$hash  $($jar.Name)"
        }
    }
    $lines | Set-Content -LiteralPath (Join-Path $Staging 'ZAPEG-BUILD.txt') -Encoding UTF8
}

$profileState = Assert-SourceProfile -Path $ProfileDir
$profileVerified = [bool]$profileState.Verified
$modsDir = Join-Path $ProfileDir 'mods'
$validatedExtras = @(Get-ValidatedExtraJars -ModsDir $modsDir -InstanceMetadata $profileState.Metadata)
$mode = if ($PatchOnly) { 'patch' } else { 'offline' }

if (-not $InventoryLockFile) {
    $lockName = if ($PatchOnly) { 'client-extra-mods.lock' } else { 'client-mods.lock' }
    $InventoryLockFile = Join-Path $PSScriptRoot $lockName
}
$inventoryJars = if ($PatchOnly) {
    @($validatedExtras)
} else {
    @(Get-ChildItem -LiteralPath $modsDir -Filter '*.jar' -File)
}

if ($WriteInventoryLock) {
    if (-not $profileVerified) {
        throw '-SkipProfileCheck ile doğrulanmış envanter kilidi üretilemez. Doğru CurseForge ATM9 profilini seçip komutu kontrol atlamadan çalıştırın.'
    }
    New-ModInventoryLock -Jars $inventoryJars -Path $InventoryLockFile -Mode $mode
    Write-Host "Aday envanter kilidi yazıldı: $InventoryLockFile" -ForegroundColor Yellow
    if ($PatchOnly) {
        Write-Host "$($extraMods.Count) satırın beklenen kaynaklardan geldiğini inceleyip lock dosyasını repoya ekleyin; sonra normal -PatchOnly komutunu çalıştırın."
    } else {
        Write-Host 'Dağıtmadan önce listeyi inceleyin: kişisel ve server-only jar bulunmamalı. Lock dosyasını repoya ekleyip normal komutla offline payload üretin.'
    }
    return
}

Assert-ModInventoryLock -Jars $inventoryJars -Path $InventoryLockFile

if (-not (Test-Path -LiteralPath $OutDir -PathType Container)) {
    New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
}

$stamp = Get-Date -Format 'yyyyMMdd'
$verificationSuffix = if ($profileVerified) { '' } else { '-UNVERIFIED' }
$fileName = if ($PatchOnly) {
    "ZapeG-Kurulum-Yamasi-ATM9-$packVersion$verificationSuffix-$stamp.zip"
} else {
    "ZapeG-Offline-ATM9-$packVersion$verificationSuffix-$stamp.zip"
}
$out = Join-Path $OutDir $fileName
$pendingOut = Join-Path $OutDir (".$fileName." + [guid]::NewGuid().ToString('N') + '.tmp.zip')
$backupOut = $null
$staging = New-StagingRoot

try {
    if ($PatchOnly) {
        $modsOut = Join-Path $staging 'mods'
        New-Item -ItemType Directory -Path $modsOut | Out-Null
        foreach ($jar in $validatedExtras) {
            Copy-Item -LiteralPath $jar.FullName -Destination $modsOut
        }
        Write-Host "  + $($extraMods.Count)/$($extraMods.Count) ek mod tam sürüm pinleriyle doğrulandı"
    } else {
        $include = @('mods', 'config', 'kubejs', 'defaultconfigs', 'packmenu', 'scripts', 'shaderpacks')
        $required = @('mods', 'config', 'kubejs', 'defaultconfigs')

        foreach ($d in $required) {
            if (-not (Test-Path -LiteralPath (Join-Path $ProfileDir $d) -PathType Container)) {
                throw "Kaynak profilde gerekli klasör eksik: $d"
            }
        }

        foreach ($d in $include) {
            $src = Join-Path $ProfileDir $d
            if (Test-Path -LiteralPath $src -PathType Container) {
                Copy-Item -LiteralPath $src -Destination (Join-Path $staging $d) -Recurse
                Write-Host "  + $d"
            }
        }
    }

    Add-ZapeGClientLayer -Staging $staging -Mode $mode
    Write-BuildManifest -Staging $staging -Mode $mode -ProfileVerified $profileVerified

    Compress-Archive -Path (Join-Path $staging '*') -DestinationPath $pendingOut -CompressionLevel Optimal

    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archive = [IO.Compression.ZipFile]::OpenRead($pendingOut)
    try {
        if ($archive.Entries.Count -eq 0) {
            throw 'Oluşturulan zip boş; mevcut paket korunuyor.'
        }
    }
    finally {
        $archive.Dispose()
    }

    # Aynı gün yeniden build alınırsa eski iyi dosyayı ancak yeni zip
    # açılıp doğrulandıktan sonra, aynı volume üzerinde atomik olarak değiştir.
    if (Test-Path -LiteralPath $out -PathType Leaf) {
        $backupOut = Join-Path $OutDir (".$fileName." + [guid]::NewGuid().ToString('N') + '.bak')
        [IO.File]::Replace($pendingOut, $out, $backupOut, $true)
        try {
            [IO.File]::Delete($backupOut)
            $backupOut = $null
        }
        catch {
            Write-Warning "Yeni zip hazır; eski dosyanın geçici yedeği silinemedi: $backupOut"
        }
    }
    else {
        [IO.File]::Move($pendingOut, $out)
    }

    $size = [math]::Round((Get-Item -LiteralPath $out).Length / 1MB, 1)
    Write-Host ''
    Write-Host "Hazır: $out (${size} MB)" -ForegroundColor Green
    if ($PatchOnly) {
        Write-Host 'Lisanslı oyuncu bu tek zip dosyasını ATM9 profil köküne çıkarır.'
    } else {
        Write-Host 'Offline oyuncu önce izole Forge 47.4.10 profili oluşturur; INSTALL-TR.txt paket içindedir.'
    }
}
finally {
    Remove-StagingRoot -Path $staging
    if (Test-Path -LiteralPath $pendingOut) {
        [IO.File]::Delete($pendingOut)
    }
}
