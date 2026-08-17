# Muhtar v2 — mod ve görev danışmanı

Muhtar v2 bir görev otoritesi değil, konuşmalı bir danışmandır. Oyuncuya yalnız
bir sayfa açmak yerine önce hedefini sorar; uygun modları karşılaştırır,
önkoşulları, ilk üç adımı ve en sık yapılan hatayı anlatır. Oyuncu isterse en
son düğme ilgili FTB Quests zincirini açar.

Muhtar görev tamamlamaz, ödül vermez, eşya almaz, yol kilitlemez ve oyuncu
başına durum tutmaz. Sabit meydan rehberidir; etrafta dolaşmaz. Silinmesi veya
v1'e döndürülmesi hiçbir FTB Quest ilerlemesini değiştirmez.

## V2 kapsamı

| Danışma alanı | Muhtar'ın açıkladığı seçimler | Ayrıntılı ZapeG sayfası |
|---|---|---|
| İlk gün ve temel altyapı | JEI, claim, yatak/mezar, güç, AE2 veya Refined Storage | Yol Haritası / İlk Gece |
| Teknoloji | Create, Mekanism, Immersive Engineering ve Petroleum'un farklı rolleri | Immersive Petroleum |
| Büyü ve uzay | Ars Nouveau, Botania, Occultism, Blood Magic; Ad Astra hazırlığı | Mevcut büyü/uzay yol kartları |
| Kara araçları | Immersive Vehicles + iki resmi MTS içerik paketi | Araçlar ve Gemiler |
| Fizik gemileri | Eureka + Valkyrien Skies | Araçlar ve Gemiler |
| Yelkenli gemiler | Aleki's Nifty Ships | Araçlar ve Gemiler |
| Ejderhalar | Ice and Fire avcı/yetiştirici/Dragonsteel hatları | Ice and Fire |
| Mağaralar ve donmuş deniz | Alex's Caves ve Aquamirae | İki ayrı chapter |
| Bosslar ve gece | Mowzie's Mobs ve Born in Chaos | İki ayrı chapter |
| Silahlar | Simply Swords aileleri ve Better Combat ritmi | Simply Swords |
| Vatandaşlar | oyuncuya ait işçi ile sunucuya ait lore vatandaşının farkı | Citizens |
| Nether keşfi | Incendium'un yalnız yeni chunk üretme kuralı | Incendium |

Yeni mod sayfaları FTB Quests'te ayrı chapter olarak görünür. Muhtar'ın metni
karar vermeyi sağlar; chapter ise gerçek ilerleme zincirini, ayrıntılı güvenlik
notlarını ve otomatik kanıtları tutar. Doğrulama modeli
[`QUEST-VALIDATION-TR.md`](QUEST-VALIDATION-TR.md) içindedir.

## Güvenli görev açma köprüsü

V1'de Easy NPC menüsü açık kalırken FTB ekranı açılıyordu. Sunucu tarafındaki
eski menü oturumu kapanmadığı için art arda seçimler bozuk veya etkisiz
görünebiliyordu. V2'nin her son düğmesi şu sırayı kullanır:

1. Easy NPC diyaloğunu kapat.
2. Bir tick bekle; ertelenmiş kapatma işlemi gerçekten tamamlansın.
3. Etkileşen oyuncu adına `zapeg-guide open <sabit-yol>` çalıştır.

`zapeg-guide` normal oyuncuya açık, sunucu taraflı bir KubeJS komutudur. Yalnız
kodda sabitlenmiş görünür landing quest'lerini açabilir; oyuncudan quest ID veya
başka komut kabul etmez. Görev tamamlayamaz, ödül veremez ve progress
değiştiremez. Bu nedenle Easy NPC'nin bütün execute-as-user allowlist'leri boş
kalır; geniş `ftbquests` yetki yükseltmesi yoktur.

NPC bulunmasa da oyuncu aynı güvenli köprüyü doğrudan kullanabilir. Örnekler:

```mcfunction
/zapeg-guide open all_paths
/zapeg-guide open petroleum
/zapeg-guide open immersive_vehicles
/zapeg-guide open alexs_caves
```

Tab tamamlama izin verilen yolları gösterir. Komut yalnız gerçek bir oyun
oyuncusunun ekranını açar; konsol/RCON kaynak olarak kullanılamaz.

## Kimlik ve dosya sözleşmesi

- Easy NPC kimliği: `zapeg:muhtar`
- Sabit entity UUID: `c9e6884a-57e1-44d4-8154-aedf54a12534`
- V2 kaynak preset'i:
  `overrides/config/easy_npc/preset/humanoid/zapeg/muhtar_v2.npc.snbt`
- V1 güvenli eski düzeni:
  `overrides/config/easy_npc/preset/humanoid/zapeg/muhtar_v1.npc.snbt`
- Canlı preset dizini: `data/config/easy_npc/preset/humanoid/zapeg/`

Entity UUID preset'in içine gömülmez; import komutuna sabit olarak verilir. Aynı
UUID ile tekrar import, chunk yüklüyken mevcut Muhtar'ı kopya üretmeden
günceller. `import_new` kullanmayın; bilerek yeni UUID üretir.

`scripts/apply-overrides.sh`, yalnız repo sahipli `.../humanoid/zapeg/` preset
alt ağacını `--delete` ile aynalar. Git'ten kaldırılan ZapeG preset'i canlı
config altında hayalet dosya bırakmaz; başka yönetici preset'lerine dokunulmaz.

## İlk kurulum veya v1'den yükseltme

Muhtar'ın duracağı overworld blok koordinatlarını seçin ve chunk'ı bir oyuncuyla
yüklü tutun:

```bash
./scripts/snapshot.sh pre-muhtar-v2
./scripts/apply-overrides.sh
docker compose restart mc
bash scripts/muhtar-npc.sh apply v2 <X> <Y> <Z>
```

Restart; yeni FTB chapter'larını, KubeJS `zapeg-guide` komutunu ve Easy NPC
config'ini birlikte yükler. Sadece daha sonraki bir diyalog/preset metni
değişirse restart gerekmez: override'ı uygulayıp aynı UUID'ye v2'yi tekrar import
etmek yeterlidir. Quest veya KubeJS değişirse yeniden restart gerekir.

Kabul testi mutlaka **OP olmayan** bir oyuncuyla yapılır:

1. Muhtar'a sağ tıklayın; ana ekran ve bütün alt menüler açılmalı.
2. Her ayrıntı ekranında karşılaştırma, önkoşul, üç başlangıç adımı ve tehlike
   notunun gerçekten bulunduğunu okuyun.
3. Her chapter düğmesinin NPC ekranını kapatıp doğru quest'i açtığını doğrulayın.
4. Aynı quest'i aç/kapat işlemini arka arkaya üç kez yapın; hayalet diyalog veya
   kapanan FTB ekranı olmamalı.
5. `/zapeg-guide open petroleum` komutunu doğrudan deneyin.
6. Hiçbir seçimden quest completion, ödül, item veya score gelmediğini kontrol
   edin.
7. Hostta `bash scripts/muhtar-npc.sh list` çalıştırın; yalnız bir
   `zapeg:muhtar` görünmeli.

`/easy_npc reload`, KubeJS komutlarını veya Easy NPC güvenlik config'ini yeniden
başlatmaz. Özellikle ilk kurulum testini tam Minecraft restart'ından sonra yapın.

## Geri alma ve kaldırma

V2 beğenilmezse eski kısa düzen aynı sabit entity UUID'sine geri yüklenebilir.
V1 de düzeltilmiş kapat/bekle/köprü sırasını kullanır:

```bash
./scripts/apply-overrides.sh
bash scripts/muhtar-npc.sh apply v1 <X> <Y> <Z>
```

Muhtar'ı tamamen kaldırmak için `despawn` kullanmayın; o yalnız geçici saklar.
Chunk'ı yükleyin, yedek alın ve gerçek delete çalıştırın:

```bash
./scripts/snapshot.sh pre-remove-muhtar
bash scripts/muhtar-npc.sh remove
docker compose exec -T mc rcon-cli save-all flush
```

`easy_npc delete`, entity'yi, Easy NPC genel indeks kaydını ve
`world/easy_npc/npcs/<UUID>.npc.nbt` dosyasını birlikte siler. Komut “bulunamadı”
diyorsa temiz kaldırma sayılmaz; chunk'ı yükleyip yeniden çalıştırın.

Yalnız NPC'yi silmek on yeni mod chapter'ını ve doğrudan `zapeg-guide` komutunu
korur. Bu chapter'ları da istemiyorsanız ilgili dağıtım commit'ini Git ile geri
alın, `scripts/apply-overrides.sh` çalıştırın ve Minecraft'ı yeniden başlatın.
Dünya blokları ve oyuncu envanterleri değişmez; yalnız bu sayfalardaki FTB
ilerleme görünümü artık yüklenmez.

Kişisel Nemesis fikri v2'nin parçası değildir; ayrı ve varsayılan kapalı bir
deney olarak parkta kalır.
