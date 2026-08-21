# Build-ClientZip.ps1 — ZapeG oyuncu paketi üretici
#
# Lisanslı oyuncular için önerilen çıktı:
#   .\Build-ClientZip.ps1 -PatchOnly  # repodaki incelenmiş lock ile üret
#   -> ZapeG-Kurulum-Yamasi-ATM9-1.1.1-YYYYMMDD.zip
#   Oyuncu bu TEK zip'i ATM9 profil köküne açar. mods/, shader/Entity Culling
#   uyumluluk ayarları ve PackMenu logosu doğru klasör yapısıyla gelir. Kişisel
#   options.txt dosyasına dokunulmaz.
#
# Offline oyuncular için oyun-dizini payload'ı:
#   .\Build-ClientZip.ps1  # repodaki incelenmiş tam-envanter lock'u ile üret
#   -> ZapeG-Offline-ATM9-1.1.1-YYYYMMDD.zip
#   Bu bir launcher profili veya Forge kurucusu değildir; izole Forge 47.4.10
#   profilinin oyun dizinine açılır (zip içindeki INSTALL-TR.txt'ye bakın).
# -WriteInventoryLock yalnız pinler bilinçli değiştiğinde, mevcut lock kontrollü
# olarak yenilenirken kullanılır; normal build komutu değildir.

[CmdletBinding()]
param(
    [string]$ProfileDir = "$env:USERPROFILE\curseforge\minecraft\Instances\All the Mods 9 - ATM9",
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
$ccTweakedReplacement = [pscustomobject]@{
    Name = 'CC: Tweaked'
    Pattern = 'cc-tweaked-1.20.1-forge-*.jar'
    FileName = 'cc-tweaked-1.20.1-forge-1.116.1.jar'
}

# Her ek moddan TAM BİR, TAM SÜRÜM jar bulunmalı. Dosya adları
# extras/cf-mods.txt, docker-compose.yml ve oyuncu rehberindeki pinlerle
# senkron kalır. Yalnız önek kontrolü eski bir jar'ı yanlışlıkla kabul eder.
# ZapeG Citizens ve Runtime bize ait build'lerdir; CurseForge profili gibi
# gösterilmez. Repo içindeki overrides/mods kopyaları ayrı doğrulanır ve aynı
# SHA kilitlerine dahil edilir.
$extraMods = @(
    [pscustomobject]@{ Name = 'Ice and Fire';        Prefix = 'iceandfire';           FileName = 'iceandfire-2.1.13-1.20.1-beta-5.jar';               FileId = '5633453'; Pin = 'CurseForge file 5633453' },
    [pscustomobject]@{ Name = 'Citadel';             Prefix = 'citadel';              FileName = 'citadel-2.6.3-1.20.1.jar';                          FileId = '7476570'; Pin = 'CurseForge file 7476570' },
    [pscustomobject]@{ Name = 'Immersive Petroleum'; Prefix = 'ImmersivePetroleum';    FileName = 'ImmersivePetroleum-1.20.1-4.3.1-36b.jar';           FileId = '8499079'; Pin = 'CurseForge file 8499079' },
    [pscustomobject]@{ Name = 'Immersive Vehicles';  Prefix = 'Immersive Vehicles-1.20.1-'; FileName = 'Immersive Vehicles-1.20.1-24.0.0.jar';           FileId = '7926604'; Pin = 'CurseForge file 7926604' },
    [pscustomobject]@{ Name = 'IV Official Content Pack'; Prefix = 'MTS Official Pack-1.20.1-'; FileName = 'MTS Official Pack-1.20.1-V29.jar';              FileId = '7933733'; Pin = 'CurseForge file 7933733' },
    [pscustomobject]@{ Name = 'IV Official Automobile Pack'; Prefix = 'OAmP-1.20.1-'; FileName = 'OAmP-1.20.1-V3.jar';                                 FileId = '7933540'; Pin = 'CurseForge file 7933540' },
    [pscustomobject]@{ Name = 'UNU Parts Pack';      Prefix = 'UNU Parts Pack ';       FileName = 'UNU Parts Pack [MTS] 1.20.1-22.18.0-6.7.3.jar';     FileId = '7064153'; Pin = 'CurseForge file 7064153' },
    [pscustomobject]@{ Name = 'UNU Civilian Pack';   Prefix = 'UNU Civilian Pack ';    FileName = 'UNU Civilian Pack [MTS] 1.20.1-22.18.0-6.7.1.jar';  FileId = '7064154'; Pin = 'CurseForge file 7064154' },
    [pscustomobject]@{ Name = 'Trin Parts Pack';     Prefix = 'Trin Parts Pack-';      FileName = 'Trin Parts Pack-1.20.1-2.28.0.jar';                 FileId = '7890589'; Pin = 'CurseForge file 7890589' },
    [pscustomobject]@{ Name = 'Trin Civil Pack';     Prefix = 'Trin Civil Pack-';      FileName = 'Trin Civil Pack-1.20.1-4.5.0.jar';                  FileId = '7890609'; Pin = 'CurseForge file 7890609' },
    [pscustomobject]@{ Name = 'Prefab';              Prefix = 'prefab-';               FileName = 'prefab-1.10.0.1.jar';                               FileId = '6065398'; Pin = 'CurseForge file 6065398' },
    [pscustomobject]@{ Name = 'CasinoCraft';         Prefix = 'CasinoCraft_';          FileName = 'CasinoCraft_1.20.1_v25.jar';                        FileId = '5942243'; Pin = 'CurseForge file 5942243' },
    [pscustomobject]@{ Name = 'Slots Machine';       Prefix = 'slotmachinemod-';       FileName = 'slotmachinemod-1.2.1-1.20.1.jar';                   FileId = '8187162'; Pin = 'CurseForge file 8187162' },
    [pscustomobject]@{ Name = "Aleki's Nifty Ships"; Prefix = 'alekiNiftyShips-FORGE-1.20.1-'; FileName = 'alekiNiftyShips-FORGE-1.20.1-1.0.14.jar';      FileId = '5963449'; Pin = 'CurseForge file 5963449' },
    [pscustomobject]@{ Name = "Alex's Caves";       Prefix = 'alexscaves';            FileName = 'alexscaves-2.0.2.jar';                              FileId = '5848216'; Pin = 'CurseForge file 5848216' },
    [pscustomobject]@{ Name = "Mowzie's Mobs";      Prefix = 'mowziesmobs';           FileName = 'mowziesmobs-1.8.2.jar';                             FileId = '7815705'; Pin = 'CurseForge file 7815705' },
    [pscustomobject]@{ Name = 'Easy NPC Bundle';     Prefix = 'easy_npc_bundle';       FileName = 'easy_npc_bundle-forge-1.20.1-7.7.7.jar';            FileId = '8644040'; Pin = 'CurseForge file 8644040' },
    [pscustomobject]@{ Name = 'Easy NPC Core';       Prefix = 'easy_npc-forge';        FileName = 'easy_npc-forge-1.20.1-7.7.7.jar';                   FileId = '8644032'; Pin = 'CurseForge file 8644032' },
    [pscustomobject]@{ Name = 'Easy NPC Config UI';  Prefix = 'easy_npc_config_ui';    FileName = 'easy_npc_config_ui-forge-1.20.1-7.7.7.jar';         FileId = '8644036'; Pin = 'CurseForge file 8644036' },
    [pscustomobject]@{ Name = 'Aquamirae';           Prefix = 'aquamirae';             FileName = 'aquamirae-forge-1.20.1-7.1.10.jar';                 FileId = '8558369'; Pin = 'CurseForge file 8558369' },
    [pscustomobject]@{ Name = 'Fragmentum';           Prefix = 'fragmentum';            FileName = 'fragmentum-forge-1.20.1-1.5.2.jar';                 FileId = '8506891'; Pin = 'CurseForge file 8506891' },
    [pscustomobject]@{ Name = 'Born in Chaos';       Prefix = 'born_in_chaos';         FileName = 'born_in_chaos_[Forge]1.20.1_1.7.5.jar';             FileId = '7917933'; Pin = 'CurseForge file 7917933' },
    [pscustomobject]@{ Name = 'Simply Swords';       Prefix = 'simplyswords';          FileName = 'simplyswords-forge-1.56.0-1.20.1.jar';              FileId = '5639538'; Pin = 'CurseForge file 5639538' },
    [pscustomobject]@{ Name = 'Valkyrien Skies';     Prefix = 'valkyrienskies';        FileName = 'valkyrienskies-120-2.4.11.jar';                     FileId = '7906689'; Pin = 'CurseForge file 7906689' },
    [pscustomobject]@{ Name = 'Eureka';              Prefix = 'eureka';                FileName = 'eureka-1201-1.6.3.jar';                             FileId = '7979379'; Pin = 'CurseForge file 7979379' },
    [pscustomobject]@{ Name = 'Numen AI';            Prefix = 'numen-forge';           FileName = 'numen-forge-1.20.1-0.1.1-all.jar';                 FileId = '8551640'; Pin = 'CurseForge file 8551640' },
    [pscustomobject]@{ Name = 'Better Combat';       Prefix = 'bettercombat';          FileName = 'bettercombat-forge-1.9.0+1.20.1.jar';               FileId = $null;     Pin = 'Modrinth 1.9.0+1.20.1-forge' },
    [pscustomobject]@{ Name = 'CC: Tweaked (1.116.1 re-pin)'; Prefix = 'cc-tweaked-1.20.1-forge-1.116'; FileName = $ccTweakedReplacement.FileName; FileId = $null; Pin = 'Modrinth 1.116.1 — ATM9 base pack CurseForge resolution does not reliably give every player this version (mod stopped publishing new files to CurseForge); re-pinned so Numen/AdvancedPeripherals integration does not throw a missing-dependency error' }
)

# ZipFileName is deliberately unversioned: it is what ships inside the
# player-facing zip, so every future release overwrites the same path on
# extraction and players never have to manually delete a stale jar again.
# FileName/RelativePath stay versioned — that is the repo's own source pin,
# verified against overrides/mods and the SHA-256 inventory lock as before.
$ownedMods = @(
    [pscustomobject]@{
        Name = 'ZapeG Citizens'
        Prefix = 'zapeg-citizens-forge-1.20.1-'
        FileName = 'zapeg-citizens-forge-1.20.1-0.4.0.jar'
        RelativePath = 'overrides\mods\zapeg-citizens-forge-1.20.1-0.4.0.jar'
        ZipFileName = 'zapeg-citizens-forge-1.20.1.jar'
        Pin = 'ZapeG owned release 0.4.0 (not CurseForge)'
    },
    [pscustomobject]@{
        Name = 'ZapeG Runtime'
        Prefix = 'zapeg-runtime-forge-1.20.1-'
        FileName = 'zapeg-runtime-forge-1.20.1-0.4.0.jar'
        RelativePath = 'overrides\mods\zapeg-runtime-forge-1.20.1-0.4.0.jar'
        ZipFileName = 'zapeg-runtime-forge-1.20.1.jar'
        Pin = 'ZapeG owned release 0.4.0 (not CurseForge)'
    }
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

    # CurseForge has used more than one schema for this value. Current profiles
    # store it under installedFile.id; older exports used fileID directly.
    $fileIdValues = @(
        [string]$instance.installedModpack.installedFile.id,
        [string]$instance.installedModpack.fileID,
        [string]$instance.fileID
    ) | Where-Object { $_ } | Select-Object -Unique
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
    if ($packFileId -notin $fileIdValues) {
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
            if ($metadataMatches.Count -gt 1) {
                $problems += "ÇİFT CURSEFORGE METADATA KAYDI: $($mod.Name) -> file $($mod.FileId)"
                continue
            }
            if ($metadataMatches.Count -eq 0) {
                # Manually copied additions are not always registered in
                # minecraftinstance.json. Exact filename selection happens here;
                # the reviewed SHA-256 inventory lock is authoritative below.
                Write-Warning "$($mod.Name) için CurseForge metadata kaydı yok; incelenmiş SHA-256 kilidiyle doğrulanacak."
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

function Get-ValidatedOwnedJars {
    $repoRoot = Split-Path $PSScriptRoot -Parent
    $selected = @()
    $problems = @()

    foreach ($mod in $ownedMods) {
        $expectedPath = Join-Path $repoRoot $mod.RelativePath
        $ownedDir = Split-Path $expectedPath -Parent
        $matches = if (Test-Path -LiteralPath $ownedDir -PathType Container) {
            @(Get-ChildItem -LiteralPath $ownedDir -Filter "$($mod.Prefix)*.jar" -File)
        } else {
            @()
        }

        if ($matches.Count -eq 0) {
            $problems += "EKSİK SAHİPLİ MOD: $($mod.Name) -> $expectedPath"
            continue
        }
        if ($matches.Count -gt 1) {
            $names = ($matches.Name | Sort-Object) -join ', '
            $problems += "ÇİFT SAHİPLİ MOD: $($mod.Name) -> $names"
            continue
        }
        if ($matches[0].Name -cne $mod.FileName -or
            [IO.Path]::GetFullPath($matches[0].FullName) -cne [IO.Path]::GetFullPath($expectedPath)) {
            $problems += "YANLIŞ SAHİPLİ MOD SÜRÜMÜ: $($matches[0].Name); beklenen $($mod.FileName)"
            continue
        }
        $selected += $matches[0]
    }

    if ($problems.Count -gt 0) {
        throw "Repo içindeki sahipli ZapeG mod seti doğrulanamadı:`n - $($problems -join "`n - ")"
    }
    if ($selected.Count -ne $ownedMods.Count) {
        throw "İç hata: $($ownedMods.Count) yerine $($selected.Count) sahipli mod seçildi."
    }

    return $selected
}

function Assert-SingleCcTweakedJar {
    param(
        [object[]]$Jars,
        [string]$Context
    )

    $matches = @($Jars | Where-Object { $_.Name -like $ccTweakedReplacement.Pattern })
    if ($matches.Count -ne 1 -or $matches[0].Name -cne $ccTweakedReplacement.FileName) {
        $found = if ($matches.Count -eq 0) {
            '(yok)'
        } else {
            ($matches.Name | Sort-Object) -join ', '
        }
        throw "CC:Tweaked değiştirme doğrulaması başarısız ($Context): yalnız $($ccTweakedReplacement.FileName) bulunmalı; bulunan: $found"
    }
}

function Set-ExactCcTweakedJar {
    param(
        [string]$ModsDir,
        [System.IO.FileInfo]$SourceJar
    )

    if (-not $SourceJar -or $SourceJar.Name -cne $ccTweakedReplacement.FileName) {
        throw "CC:Tweaked değiştirme kaynağı yanlış; beklenen $($ccTweakedReplacement.FileName)."
    }

    @(Get-ChildItem -LiteralPath $ModsDir -Filter $ccTweakedReplacement.Pattern -File) |
        ForEach-Object { [IO.File]::Delete($_.FullName) }
    Copy-Item -LiteralPath $SourceJar.FullName -Destination (Join-Path $ModsDir $ccTweakedReplacement.FileName)

    $result = @(Get-ChildItem -LiteralPath $ModsDir -Filter $ccTweakedReplacement.Pattern -File)
    Assert-SingleCcTweakedJar -Jars $result -Context 'offline staging mods klasörü'
}

function Assert-SingleOwnedModJars {
    param(
        [object[]]$Jars,
        [string]$Context,
        # 'FileName' checks source/repo pins (versioned); 'ZipFileName' checks
        # what actually ships inside the player-facing zip (unversioned).
        [ValidateSet('FileName', 'ZipFileName')]
        [string]$FileNameProperty = 'FileName'
    )

    foreach ($mod in $ownedMods) {
        $expectedName = $mod.$FileNameProperty
        # Prefix carries a trailing '-' for the versioned source form; the
        # unversioned ZipFileName has no dash before '.jar', so trim it here
        # or the wildcard would never match the staged/zip file.
        $matchPrefix = if ($FileNameProperty -eq 'ZipFileName') { $mod.Prefix.TrimEnd('-') } else { $mod.Prefix }
        $matchPattern = "$matchPrefix*.jar"
        $matches = @($Jars | Where-Object { $_.Name -like $matchPattern })
        if ($matches.Count -ne 1 -or $matches[0].Name -cne $expectedName) {
            $found = if ($matches.Count -eq 0) {
                '(yok)'
            } else {
                ($matches.Name | Sort-Object) -join ', '
            }
            throw "Sahipli mod doğrulaması başarısız ($Context): yalnız $expectedName bulunmalı; bulunan: $found"
        }
    }
}

function Set-ExactOwnedModJars {
    param(
        [string]$ModsDir,
        [System.IO.FileInfo[]]$SourceJars
    )

    foreach ($mod in $ownedMods) {
        @(Get-ChildItem -LiteralPath $ModsDir -Filter "$($mod.Prefix.TrimEnd('-'))*" -File) |
            ForEach-Object { [IO.File]::Delete($_.FullName) }
        $source = @($SourceJars | Where-Object { $_.Name -ceq $mod.FileName })
        if ($source.Count -ne 1) {
            throw "Sahipli mod değiştirme kaynağı yanlış; beklenen $($mod.FileName)."
        }
        Copy-Item -LiteralPath $source[0].FullName -Destination (Join-Path $ModsDir $mod.ZipFileName)
    }

    $result = @(Get-ChildItem -LiteralPath $ModsDir -Filter '*.jar' -File)
    Assert-SingleOwnedModJars -Jars $result -Context 'offline staging mods klasörü' -FileNameProperty 'ZipFileName'
}

function Get-OfflineInventoryJars {
    param(
        [string]$ModsDir,
        [System.IO.FileInfo[]]$OwnedJars,
        [System.IO.FileInfo]$CcTweakedJar
    )

    $profileJars = @(Get-ChildItem -LiteralPath $ModsDir -Filter '*.jar' -File)
    foreach ($mod in $ownedMods) {
        # Repo-owned releases replace the entire filename family. A maintainer
        # profile may still contain the previous release (versioned) or the
        # maintainer's own unversioned test copy after testing it; never copy
        # either stale jar into an offline payload beside the reviewed build.
        $profileJars = @($profileJars | Where-Object { $_.Name -notlike "$($mod.Prefix.TrimEnd('-'))*.jar" })
    }

    # ATM9 1.1.1 contributes CC:Tweaked 1.113.1 while ZapeG re-pins 1.116.1.
    # Treat the whole filename family as a replacement set: discard every base
    # copy, then add exactly the already validated pin. This same invariant is
    # checked again in staging and in the completed archive below.
    $profileJars = @(
        $profileJars |
            Where-Object { $_.Name -notlike $ccTweakedReplacement.Pattern }
    )
    $inventory = @($profileJars) + @($CcTweakedJar) + @($OwnedJars)
    Assert-SingleCcTweakedJar -Jars $inventory -Context 'offline envanteri'
    Assert-SingleOwnedModJars -Jars $inventory -Context 'offline envanteri'
    return $inventory
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
    $entityCulling = Join-Path $defaults 'config\entityculling.json'
    $iafClient = Join-Path $defaults 'config\iceandfire-client.toml'
    $niftyLicense = Join-Path $repoRoot 'client\licenses\alekiships-LICENSE.txt'
    if (-not (Test-Path -LiteralPath $oculus) -or
        -not (Test-Path -LiteralPath $entityCulling) -or
        -not (Test-Path -LiteralPath $iafClient) -or
        -not (Test-Path -LiteralPath $niftyLicense) -or
        ($Mode -eq 'offline' -and -not (Test-Path -LiteralPath $options))) {
        throw 'Repo içindeki ZapeG istemci varsayılanları eksik.'
    }

    try {
        $entityCullingConfig = Get-Content -Raw -LiteralPath $entityCulling | ConvertFrom-Json
    }
    catch {
        throw "Entity Culling uyumluluk ayarı geçerli JSON değil: $entityCulling"
    }
    $requiredMtsEntities = @(
        'mts:builder_existing',
        'mts:builder_rendering',
        'mts:builder_seat'
    )
    $missingMtsEntities = @(
        $requiredMtsEntities |
            Where-Object { $_ -notin @($entityCullingConfig.entityWhitelist) }
    )
    if ($missingMtsEntities.Count -gt 0) {
        throw "Entity Culling ayarı Immersive Vehicles render whitelist'ini içermiyor: $($missingMtsEntities -join ', ')"
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
    # ATM9's Entity Culling otherwise hides IV's linked render/seat entities.
    # Both patch and offline outputs carry the reviewed whitelist.
    Copy-Item -LiteralPath $entityCulling -Destination (Join-Path $configDir 'entityculling.json') -Force

    # Ice and Fire'in ejderhali ozel ana menusu TitleScreen'i degistirip
    # PackMenu'yu (ZapeG logosu) tamamen eziyor. Yama bu istemci ayarini
    # kapali olarak dagitir; icerik dogrulanir ki yanlislikla acilmasin.
    if ((Get-Content -Raw -LiteralPath $iafClient) -notmatch '"Custom main menu"\s*=\s*false') {
        throw "Ice and Fire istemci ayari 'Custom main menu = false' icermiyor: $iafClient"
    }
    Copy-Item -LiteralPath $iafClient -Destination (Join-Path $configDir 'iceandfire-client.toml') -Force

    # Nifty Ships is MIT, but its published 1.0.14 jar omits the notice file.
    # Preserve the upstream copyright/permission text in every distributed build.
    $licensesDir = Join-Path $Staging 'licenses'
    New-Item -ItemType Directory -Path $licensesDir -Force | Out-Null
    Copy-Item -LiteralPath $niftyLicense -Destination (Join-Path $licensesDir 'alekiships-LICENSE.txt') -Force

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
             "4. Minecraft ve CurseForge tamamen kapalıyken mods içindeki TÜM cc-tweaked-1.20.1-forge-*.jar, zapeg-citizens-forge-1.20.1*.jar ve zapeg-runtime-forge-1.20.1*.jar dosyalarını sil. Özellikle cc-tweaked-1.20.1-forge-1.113.1.jar ile eski, sürüm numaralı Citizens/Runtime jarları (varsa) silinmiş olmalı — bu adım artık yalnız eski bir kurulumdan kalan dosyalar için gerekli; $($ownedMods[0].ZipFileName) ve $($ownedMods[1].ZipFileName) bundan sonraki her güncellemede otomatik üzerine yazılır, tekrar silmen gerekmez.",
             '5. Bu zip içeriğini O KLASÖRÜN KÖKÜNE çıkar.',
             '6. ZapeG dosyaları için üzerine yazma sorulursa onayla. Kişisel options.txt ayarların bu yamada yoktur ve korunur.',
             "7. Bu üç mod ailesi için yalnız cc-tweaked-1.20.1-forge-1.116.1.jar, $($ownedMods[0].ZipFileName) ve $($ownedMods[1].ZipFileName) bulunmalı; diğer ATM9/ZapeG modlarını silme. mods\iceandfire-...jar, üç resmi IV jarı ve alekiNiftyShips-FORGE-1.20.1-1.0.14.jar doğrudan görünmeli.",
             '8. Oyunu başlat. Kullanıcı adını değiştirme; envanter, claim ve kişisel lore o ada bağlıdır.',
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
             "3. Minecraft ve launcher tamamen kapalıyken mods içindeki TÜM cc-tweaked-1.20.1-forge-*.jar, zapeg-citizens-forge-1.20.1*.jar ve zapeg-runtime-forge-1.20.1*.jar dosyalarını sil. Özellikle cc-tweaked-1.20.1-forge-1.113.1.jar ile eski, sürüm numaralı Citizens/Runtime jarları (varsa) silinmiş olmalı — bu adım artık yalnız eski bir kurulumdan kalan dosyalar için gerekli; $($ownedMods[0].ZipFileName) ve $($ownedMods[1].ZipFileName) bundan sonraki her güncellemede otomatik üzerine yazılır, tekrar silmen gerekmez.",
             '4. Bu zip içeriğini o profilin OYUN KLASÖRÜNE çıkar.',
             "5. Bu üç mod ailesi için yalnız cc-tweaked-1.20.1-forge-1.116.1.jar, $($ownedMods[0].ZipFileName) ve $($ownedMods[1].ZipFileName) bulunmalı; diğer ATM9/ZapeG modlarını silme. mods\iceandfire-...jar, üç resmi IV jarı ve alekiNiftyShips-FORGE-1.20.1-1.0.14.jar doğrudan görünmeli; iç içe ZapeG klasörü olmamalı.",
             '6. Sabit bir kullanıcı adı seç. Sonradan değiştirme; envanter ve claim kimliğin bu addır.'
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
    foreach ($mod in $ownedMods) {
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
$validatedOwned = @(Get-ValidatedOwnedJars)
$validatedCcTweaked = @(
    $validatedExtras |
        Where-Object { $_.Name -ceq $ccTweakedReplacement.FileName }
)
if ($validatedCcTweaked.Count -ne 1) {
    throw "Doğrulanmış ek modlarda tam bir CC:Tweaked pini bulunmalı: $($ccTweakedReplacement.FileName)"
}
$validatedCcTweaked = $validatedCcTweaked[0]
$mode = if ($PatchOnly) { 'patch' } else { 'offline' }

if (-not $InventoryLockFile) {
    $lockName = if ($PatchOnly) { 'client-extra-mods.lock' } else { 'client-mods.lock' }
    $InventoryLockFile = Join-Path $PSScriptRoot $lockName
}
$inventoryJars = if ($PatchOnly) {
    @($validatedExtras) + @($validatedOwned)
} else {
    @(Get-OfflineInventoryJars -ModsDir $modsDir -OwnedJars $validatedOwned -CcTweakedJar $validatedCcTweaked)
}
Assert-SingleCcTweakedJar -Jars $inventoryJars -Context "$mode kilit envanteri"
Assert-SingleOwnedModJars -Jars $inventoryJars -Context "$mode kilit envanteri"

if ($WriteInventoryLock) {
    if (-not $profileVerified) {
        throw '-SkipProfileCheck ile doğrulanmış envanter kilidi üretilemez. Doğru CurseForge ATM9 profilini seçip komutu kontrol atlamadan çalıştırın.'
    }
    New-ModInventoryLock -Jars $inventoryJars -Path $InventoryLockFile -Mode $mode
    Write-Host "Aday envanter kilidi yazıldı: $InventoryLockFile" -ForegroundColor Yellow
    if ($PatchOnly) {
        Write-Host "$($inventoryJars.Count) satırın beklenen kaynaklardan geldiğini inceleyip lock dosyasını repoya ekleyin; sonra normal -PatchOnly komutunu çalıştırın."
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
        for ($i = 0; $i -lt $ownedMods.Count; $i++) {
            Copy-Item -LiteralPath $validatedOwned[$i].FullName -Destination (Join-Path $modsOut $ownedMods[$i].ZipFileName)
        }
        Write-Host "  + $($extraMods.Count) dış kaynak + $($ownedMods.Count) sahipli ek mod tam sürüm/SHA pinleriyle doğrulandı"
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

        # The repo-owned build is authoritative even if the maintainer's source
        # profile already contains the same exact filename.
        $modsOut = Join-Path $staging 'mods'
        Set-ExactOwnedModJars -ModsDir $modsOut -SourceJars $validatedOwned
        Set-ExactCcTweakedJar -ModsDir $modsOut -SourceJar $validatedCcTweaked
        Write-Host "  + $($ownedMods.Count) sahipli ZapeG mod"
        Write-Host "  + CC:Tweaked taban sürümü $($ccTweakedReplacement.FileName) ile değiştirildi"
    }

    $stagedCcTweaked = @(Get-ChildItem -LiteralPath (Join-Path $staging 'mods') -Filter $ccTweakedReplacement.Pattern -File)
    Assert-SingleCcTweakedJar -Jars $stagedCcTweaked -Context "$mode staging mods klasörü"
    $stagedJars = @(Get-ChildItem -LiteralPath (Join-Path $staging 'mods') -Filter '*.jar' -File)
    Assert-SingleOwnedModJars -Jars $stagedJars -Context "$mode staging mods klasörü" -FileNameProperty 'ZipFileName'
    Add-ZapeGClientLayer -Staging $staging -Mode $mode
    Write-BuildManifest -Staging $staging -Mode $mode -ProfileVerified $profileVerified

    Compress-Archive -Path (Join-Path $staging '*') -DestinationPath $pendingOut -CompressionLevel Optimal

    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archive = [IO.Compression.ZipFile]::OpenRead($pendingOut)
    try {
        if ($archive.Entries.Count -eq 0) {
            throw 'Oluşturulan zip boş; mevcut paket korunuyor.'
        }
        $requiredClientEntries = @(
            'config/oculus.properties',
            'config/entityculling.json',
            'config/iceandfire-client.toml',
            'licenses/alekiships-LICENSE.txt'
        )
        $archivedEntryNames = @($archive.Entries | ForEach-Object { $_.FullName.Replace('\', '/') })
        $missingClientEntries = @(
            $requiredClientEntries |
                Where-Object { $_ -notin $archivedEntryNames }
        )
        if ($missingClientEntries.Count -gt 0) {
            throw "Oluşturulan zip gerekli istemci ayarlarını içermiyor: $($missingClientEntries -join ', ')"
        }
        $archivedCcTweaked = @(
            $archive.Entries |
                Where-Object { $_.Name -like $ccTweakedReplacement.Pattern }
        )
        Assert-SingleCcTweakedJar -Jars $archivedCcTweaked -Context "$mode zip arşivi"
        Assert-SingleOwnedModJars -Jars $archive.Entries -Context "$mode zip arşivi" -FileNameProperty 'ZipFileName'
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
