# Seri ATM9+ — Oyuncu Kurulumu (~10 dk)

Kendi paketimiz: **All the Mods 9 v1.1.1** + 3 ek mod. Herkesin mod seti birebir aynı olmak zorunda, yoksa sunucu içeri almaz — o yüzden sürümlere dikkat.

## 1. CurseForge App

[curseforge.overwolf.com](https://www.curseforge.com/download/app) → indir, kur (Minecraft seçili olsun). Zaten Prism/MultiMC kullanan bilir, aynı mantık.

## 2. All the Mods 9 — sürüm 1.1.1

1. App içinde **Minecraft → Browse Modpacks → "All the Mods 9"** → Install.
2. Sürüm kontrolü: profil → **⋮ → Profile Options / Version** → **"All the Mods 9-1.1.1"** seçili olmalı (şu an zaten en günceli, yine de bak).

## 3. Ek modlar (3 jar)

Profil → **⋮ → Open Folder** → `mods` klasörüne şu üç dosyayı at (linkten **Download**, indirilen jar'ı sürükle):

| Mod | Dosya | Link |
|---|---|---|
| Ice and Fire | `iceandfire-2.1.13-1.20.1-beta-5.jar` | [indir](https://www.curseforge.com/minecraft/mc-mods/ice-and-fire-dragons/files/5633453) |
| Citadel | `citadel-2.6.3-1.20.1.jar` | [indir](https://www.curseforge.com/minecraft/mc-mods/citadel/files/7476570) |
| Immersive Petroleum | `ImmersivePetroleum-1.20.1-4.3.1-36b.jar` | [indir](https://www.curseforge.com/minecraft/mc-mods/immersive-petroleum/files/8499079) |

Dosya adı birebir bu olmalı — farklı sürüm indirme.

## 4. RAM

CurseForge App → **Settings → Game Specific → Minecraft → Allocated Memory** → **10–12 GB** (makinen 16 GB ise 8–10 GB yap, altına inme). Java ile uğraşma, app hallediyor.

## 5. Bağlan

Profilden **Play** → ilk açılış uzun sürer (5+ dk, normal) → **Multiplayer → Add Server** → IP'yi Ertu'dan al. Whitelist var; Minecraft kullanıcı adını Ertu'ya bildir.

## Sorun giderme

- **Bağlanırken atıyor / "mod set mismatch"** → pack sürümü 1.1.1 mi + 3 jar doğru sürüm mü kontrol et.
- **Açılışta crash** → RAM ayarına bak (adım 4); olmadı Ertu'ya crash log at.
- **Çok kasıyor** → video ayarlarından render distance 8'e çek; shader açtıysan kapat.

## Güncellemeler

Pack güncellenince Ertu duyurur. Çoğu güncellemede **hiçbir şey yapman gerekmez** (sunucu tarafı). "Jar değişti" derse: eskisini `mods`'tan sil, yenisini at — hepsi bu.
