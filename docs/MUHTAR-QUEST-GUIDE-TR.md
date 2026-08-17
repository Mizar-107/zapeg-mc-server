# Muhtar — görev yolu rehberi

Muhtar v1, ayrı bir görev sistemi değildir. Oyuncuya ne yapmak istediğini sorar
ve var olan FTB Quests kartını doğrudan açar. Görev tamamlamaz, ödül vermez,
eşya almaz, yol kilitlemez ve oyuncu başına yeni durum tutmaz. Bu yüzden Muhtar
silinse bile mevcut görev ilerlemesi aynen kalır.

## V1 kapsamı

| Muhtar seçimi | Açılan ZapeG görevi |
|---|---|
| Yeni başladım | İlk gece rehberi — `8129D7094B2D7000` |
| Makine ve otomasyon | Teknoloji Yolu — `5061F687C93750E0` |
| Büyü öğrenmek | Büyü Yolu — `E81A3ADBB5F701B7` |
| Kasaba kurmak | Şehir Kurucu — `69B229ED4B037D62` |
| Uzay programı | Uzay Programı — `D5E7D3BA9C25ECCD` |
| Ejderha peşindeyim | Ejderha Avcısı — `E6AD87C0417C62B7` |
| Boss avı | Boss Rush — `821E9FAD62271BBF` |
| Tüm yollar | ZapeG'e Hoş Geldin — `E3BD6E35F91448B4` |

Hedeflerin tamamı bu repo tarafından sahip olunan gerçek **quest** kimlikleridir.
FTB Quests 2001.4.14'ün `open_book` komutu chapter kimliğini açmaz; bu nedenle
chapter kimlikleri düğmelere konmadı. ATM9'in stok görev kimlikleri de preset'e
saçılmadı: ZapeG kartları sürüm yükseltmelerinde daha kararlı bir köprü görevi
görür ve ilgili ATM9 chapter'larını kendi metinlerinde tarif eder.
Bridge kartları ayrıca bu exact ATM9 sürümünde ayrı chapter'ı bulunmayan
MineColonies, Immersive Engineering, The Aether ve Ice and Fire yollarını açıkça
işaretleyip oyuncuyu ilgili modun öğretici/rehber kitabına veya JEI'ye yönlendirir.

## Kimlik ve dosya sözleşmesi

- Easy NPC kimliği: `zapeg:muhtar`
- Sabit entity UUID: `c9e6884a-57e1-44d4-8154-aedf54a12534`
- V1 preset UUID: `a9cf4e70-21bd-4e40-b67e-8fb490d99fad`
- V1 kaynak dosyası:
  `overrides/config/easy_npc/preset/humanoid/zapeg/muhtar_v1.npc.snbt`
- Canlı dosya:
  `data/config/easy_npc/preset/humanoid/zapeg/muhtar_v1.npc.snbt`

Entity UUID dosyanın içine gömülmez; import komutuna sabit olarak verilir. Aynı
UUID ile tekrar import, yüklü Muhtar'ı kopya üretmeden günceller. `import_new`
kullanmayın; bilerek yeni UUID üretir.

`scripts/apply-overrides.sh`, yalnız repo sahipli
`config/easy_npc/preset/humanoid/zapeg/` alt ağacını `--delete` ile birebir
eşler. Böylece Git'ten silinen bir ZapeG preset'i canlı config altında hayalet
dosya bırakmaz; yönetici tarafından dışa aktarılan başka preset klasörlerine
dokunulmaz.

## İlk kurulum

Muhtar'ın duracağı overworld blok koordinatlarını seçin. Sonra:

```bash
./scripts/snapshot.sh pre-muhtar-v1
./scripts/apply-overrides.sh
docker compose restart mc
bash scripts/muhtar-npc.sh apply v1 <X> <Y> <Z>
```

İlk restart, takip edilen Easy NPC güvenlik ayarını yükler. Ayar yalnız
`ftbquests` komut kökünü `GAMEMASTERS` execute-as-user fallback listesine ekler.
Her quest düğmesi gerçek etkileşen oyuncu adına ve seviye 2 ile yalnız
`open_book` çalıştırır; normal oyuncuya genel komut yetkisi verilmez. Easy NPC
allowlist'i komut kökü bazında çalıştığı için `ftbquests` satırı yalnız güvenilir
yönetici/creative kullanıcıların düzenleyebildiği bu `RESTRICTED` preset ile
birlikte tutulmalıdır.

Kabul testi mutlaka **OP olmayan** bir oyuncuyla yapılır:

1. Muhtar'a sağ tıklayın; ana ekran açılmalı.
2. Ana ekrandaki dört doğrudan yol kartını ve “tüm yollar” düğmesini deneyin.
3. “Uzaklara gitmek” alt ekranındaki üç kartı ve “geri” düğmesini deneyin.
4. Her düğmenin tablodaki kartı açtığını, hiçbir görevi tamamlamadığını ve ödül
   vermediğini doğrulayın.
5. Hostta `bash scripts/muhtar-npc.sh list` çalıştırın; tek bir
   `zapeg:muhtar` görünmeli.

## Değişiklik ve geri alma

V1 dosyasını ezmek yerine kabul edilen sürümü saklayın ve
`muhtar_v2.npc.snbt` ekleyin. Muhtar'ın chunk'ı yüklüyken:

```bash
./scripts/snapshot.sh pre-muhtar-v2
./scripts/apply-overrides.sh
bash scripts/muhtar-npc.sh apply v2 <X> <Y> <Z>
```

Yalnız preset değiştiyse restart gerekmez. Beğenilmezse aynı sabit UUID'ye eski
sürümü geri import edin:

```bash
bash scripts/muhtar-npc.sh apply v1 <X> <Y> <Z>
```

## Tamamen kaldırma

`despawn` geçici saklar; kalıcı silme değildir. Muhtar'ın chunk'ını bir oyuncu
ile yükleyin (veya hostun mevcut forceload durumunu bozmadan kontrollü yükleyin),
sonra:

```bash
./scripts/snapshot.sh pre-remove-muhtar
bash scripts/muhtar-npc.sh remove
docker compose exec -T mc rcon-cli save-all flush
```

`easy_npc delete`, entity'yi, Easy NPC genel indeks kaydını ve
`world/easy_npc/npcs/<UUID>.npc.nbt` kaydını birlikte siler. Chunk yüklü değilse
“bulunamadı” sonucu temiz kaldırma sayılmaz; chunk'ı yükleyip tekrar çalıştırın.

Preset'i de paketten çıkarmak isterseniz izlenen `muhtar_v*.npc.snbt`
dosyalarını kaldırıp `scripts/apply-overrides.sh` çalıştırın. Artık hiçbir Easy
NPC görev rehberi kalmayacaksa
`overrides/config/easy_npc/security.cfg` içindeki
`executeAsUserCommandAllowList.GAMEMASTERS` değerini tekrar boşaltın, override'ı
uygulayın ve Minecraft'ı yeniden başlatın. Oyuncu verisi için ayrıca temizlenecek
score, stage veya quest kaydı yoktur.

Kişisel Nemesis fikri bu sürümün parçası değildir; ayrı bir deney olarak parkta
kalır.
