# ZapeG — Oyuncu Kurulumu

Kendi paketimiz: **All the Mods 9 v1.1.1** + 12 ek mod. Sunucu **offline-mode** — Microsoft hesabı şart değil, her launcher girer. İki kural: herkesin mod seti birebir aynı olacak, ve **kullanıcı adını BİR KEZ seçeceksin** (whitelist + envanterin o ada bağlı; sonradan değiştirirsen sıfırdan başlarsın). Adını Ertu'ya bildir.

> Şık HTML sürümü: `zapeg-kurulum.html` — telefonda da rahat okunur.

## Yol A — Minecraft lisansın varsa (CurseForge App, ~10 dk)

1. [CurseForge App](https://www.curseforge.com/download/app) indir, kur.
2. **Minecraft → Browse Modpacks → "All the Mods 9"** → Install → sürüm **1.1.1** olduğunu doğrula (profil → ⋮ → Version).
3. Ek modlar — profil → **⋮ → Open Folder** → `mods` klasörüne tablodakileri at. (Kolay yol: Ertu'nun paylaştığı `zapeg-extra-mods.zip`'i `mods` klasörüne aç — tablo yedek/referans.)

   | Mod | Dosya | Link |
   |---|---|---|
   | Ice and Fire | `iceandfire-2.1.13-1.20.1-beta-5.jar` | [indir](https://www.curseforge.com/minecraft/mc-mods/ice-and-fire-dragons/files/5633453) |
   | Citadel | `citadel-2.6.3-1.20.1.jar` | [indir](https://www.curseforge.com/minecraft/mc-mods/citadel/files/7476570) |
   | Immersive Petroleum | `ImmersivePetroleum-1.20.1-4.3.1-36b.jar` | [indir](https://www.curseforge.com/minecraft/mc-mods/immersive-petroleum/files/8499079) |
   | Alex's Caves | `alexscaves-2.0.2.jar` | [indir](https://www.curseforge.com/minecraft/mc-mods/alexs-caves/files/5848216) |
   | Mowzie's Mobs | `mowziesmobs-1.8.2.jar` | [indir](https://www.curseforge.com/minecraft/mc-mods/mowzies-mobs/files/7815705) |
   | Easy NPC | `easy_npc_bundle-forge-1.20.1-7.7.7.jar` | [indir](https://www.curseforge.com/minecraft/mc-mods/easy-npc/files/8644040) |
   | Aquamirae | `aquamirae-forge-1.20.1-7.1.10.jar` | [indir](https://www.curseforge.com/minecraft/mc-mods/aquamirae/files/8558369) |
   | Born in Chaos | `born_in_chaos_[Forge]1.20.1_1.7.5.jar` | [indir](https://www.curseforge.com/minecraft/mc-mods/born-in-chaos/files/7917933) |
   | When Dungeons Arise | `DungeonsArise-1.20.1-2.1.57-release.jar` | [indir](https://www.curseforge.com/minecraft/mc-mods/when-dungeons-arise/files/4798432) |
   | Simply Swords | `simplyswords-forge-1.56.0-1.20.1.jar` | [indir](https://www.curseforge.com/minecraft/mc-mods/simply-swords/files/5639538) |
   | Better Combat | `bettercombat-forge-1.9.0+1.20.1.jar` | [indir](https://modrinth.com/mod/better-combat/version/1.9.0%2B1.20.1-forge) |
   | playerAnimator | `player-animation-lib-forge-1.0.2-rc1+1.20.jar` | [indir](https://modrinth.com/mod/playeranimator/version/1.0.2-rc1%2B1.20-forge) |

4. **Görsel ön-ayar (shaders açık başlasın):** `zapeg-client-defaults.zip`'i profil klasörüne aç, üzerine yaz. (Shader aç/kapa: **K**; kasarsa Shader Packs → MakeUp-UltraFast.)
5. RAM: Settings → Game Specific → Minecraft → **10–12 GB** (16 GB makinede 8–10).
6. Play → Multiplayer → Add Server → IP: `81.213.77.41` (değişirse duyurulur).

## Yol B — Lisans yoksa (offline launcher)

1. Offline hesap destekleyen bir launcher kur (ör. **SKlauncher**). Kullanıcı adını gir — Ertu'ya bildirdiğinle birebir aynı.
2. **ZapeG instance zip'ini** Ertu'dan al (ilk premium kurulumdan üretilecek, Drive linki grupta) → launcher'ın oyun klasörüne aç (`mods`, `config`, `kubejs`, `defaultconfigs`... hepsi gelecek).
3. Launcher'da sürüm: **Forge 1.20.1** (47.4.0). RAM: **8–10 GB**.
4. Başlat → Multiplayer → IP: `81.213.77.41` (değişirse duyurulur).

Not: Zip, premium kurulumdaki profil klasörünün kopyası — mod seti otomatik birebir aynı olur.

## Sorun giderme

- **Girişte atıyor / mod uyuşmazlığı** → pack 1.1.1 mi + 3 jar doğru sürüm mü? (Yol B'de: zip güncel mi?)
- **"Not whitelisted"** → adını Ertu'ya bildirdin mi, birebir aynı mı yazdın?
- **Açılışta crash** → RAM ayarı; olmadı crash log'u gruba at.
- **Kasma** → render distance 8; shader kapat.

## Güncellemeler

Pack güncellenince duyurulur. Çoğunlukla bir şey yapman gerekmez (sunucu tarafı). "Jar değişti" denirse: eski jar'ı sil, yenisini at. Yol B'dekilere güncel zip verilir.
