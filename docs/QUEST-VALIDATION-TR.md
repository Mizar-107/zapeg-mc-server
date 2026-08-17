# ZapeG görev doğrulama sistemi

## Model

FTB Quests artık başarı gerçeğinin sahibi değil; yalnız kitap ve ödül yüzeyidir.
`zapeg:verified` içindeki görünmez advancement kriterleri sunucu otoritesidir.
Otomatik ölçülebilen başarı görevlerinde oyuncunun basabileceği `checkmark`
bırakılmaz; fiziksel sürüş/kalıcılık gibi ölçülemeyen yeni rehber adımları aşağıda
ayrı ve açıkça manuel olarak listelenir.

Yol Haritası da düzeltilmiştir: hoş geldin kriteri girişte; ilk gece yatakta
uyuyunca; teknoloji/büyü/ejderha yolları gerçek item görülünce; şehir/uzay/boss
yolları ilgili mod veya vanilla advancement'ı gelince açılır. Rehberde de boş
tikle kaynak alma kalmaz.

- Ölçülebilir hedef: KubeJS/vanilla/mod advancement olayı kriteri verir.
- Yapı, güvenlik veya kalite hedefi: OP dünyada gördükten sonra kriteri verir.
- FTB Teams ortak partisinde kriteri alan bir üye grup görevini tamamlar.
- Kupa item ödülleri `team_reward: true` olduğu için takım başına bir kez alınır.

## Eklenen modların rehber chapter'ları

ZapeG'in oyuncuya dönük eklemeleri artık yalnız Yol Haritası metninde anılmaz;
on ayrı chapter gerçek başlangıç ve ilerleme zincirleri sağlar:

| Chapter | Kapsam | Ana doğrulama |
|---|---|---|
| ZapeG — Ice and Fire | Bestiary, av, yumurta/bakım, Dragonsteel | mod advancement'ları |
| ZapeG — Immersive Petroleum | rezerv, pumpjack, damıtma, ileri rafineri | mod advancement'ları |
| ZapeG — Alex's Caves | rehber/harita, altı mağara, altı boss | mod advancement'ları |
| ZapeG — Aquamirae | buz labirenti, Shipbreaker, ekipman, Shellback | mod advancement'ları |
| ZapeG — Mowzie's Mobs | erken avlar, Wroughtnaut/Frostmaw, Umvuthi, Sculptor | mod advancement'ları |
| ZapeG — Born in Chaos | gece avları, dark metal, bosslar, necromancy | mod advancement'ları |
| ZapeG — Simply Swords | silah ailesi, runik silah, relic, Better Combat pratiği | item + mod advancement'ı |
| ZapeG — Araçlar ve Gemiler | IV/MTS, Eureka/VS, Nifty Ships | item + advancement + kullanım testi |
| ZapeG — Citizens | sahiplik, sohbet, güvenli iş emri | tek açık manuel canlı test |
| ZapeG — Incendium | yeni Nether chunk kuralı ve güvenli sefer | açık manuel keşif testi |

Citadel, Fragmentum, Valkyrien Skies çekirdeği, Easy NPC iç bileşenleri,
Chunky, BlueMap, Discord Integration ve ZapeG Runtime bağımlılık/operatör
altyapısıdır; sırf listeyi doldurmak için sahte ilerleme sayfası almaz.
Valkyrien Skies oyuncuya Eureka dalında; Numen ise Citizens dalında açıklanır.

Yeni chapter/quest/task/reward kimlikleri
`SHA256("zapeg-ftbq-v1|" + kalıcı_slug)` sonucunun ilk 16 hex hanesidir. Bir ID
yayınlandıktan sonra slug veya ID yeniden üretilmez; aksi halde canlı ilerleme
yeni bir nesne sanılır. Muhtar landing ID'leri yalnız
`overrides/kubejs/server_scripts/zapeg_quest_guide.js` içindeki sabit haritada
tutulur; NPC preset'lerine 16 haneli ID saçılmaz.

Ölçülebilen yeni hedeflerde oyuncu tiki kullanılmaz. Bilinçli manuel alanlar
yalnız şunlardır: bir rehber/güvenlik metnini okuma, gerçek araç veya geminin
unload/reload sonrası kalması, güvenli Better Combat pratiği, gerçek Citizens
yanıtı ve bounded iş, Incendium'un yeni chunk bölgesine gidip dönme. Bu düğmeler
metinde açıkça “manuel” diye işaretlidir; nadir item veya ilerleme atlatan ödül
vermez. Immersive Vehicles 24.0.0'ın 22 advancement dosyasından 20'si hatalı JSON
olduğu için IV dalında bozuk advancement'a güvenmek yerine exact core item'ları
ve gerçek yol testi kullanılır.

## Otomatik doğrulanan kişisel hedefler

| Kişi | Login | Hedef | Kanıt |
|---|---|---|---|
| Emir | `kralxlarge` | Ender Dragon son darbesi | `minecraft:end/kill_dragon` yalnız exact login için |
| Emir | `kralxlarge` | Aynı anda 64 elmas | Sunucu envanter toplamı; eşya tüketilmez |
| Emir | `kralxlarge` | Kendi evcil ejderhası | Kendi Ice and Fire ejderhasına binme + tame/owner UUID kontrolü |
| Emin Taha | `eminomi12` | Vanilla köy keşfi | Beş vanilla köy structure detektörü |
| Emin Taha | `eminomi12` | 10 evcilleştirme | Tekrarlanan `tame_animal` olayı + kalıcı sayaç |
| Salih | `SalihKarahan` | Kontrollü yak/söndür | Netherrack/soul-soil, 2 blok güvenlik hacmi, aynı ateş ve aynı oyuncu |
| Salih | `SalihKarahan` | Kendi evcil ejderhası | Kendi Ice and Fire ejderhasına binme + tame/owner UUID kontrolü |
| Recep | `Mizar__107` | Sandık nöbeti | Sandık üstünde kesintisiz 120 saniye; ayrılınca sıfır |
| Mert | `MertOnal` | Minecart ile 5 km | Vanilla `minecart_one_cm` istatistiği |
| Enes | `Thekingim` | Arbalet | Exact login için `ol_betsy`; önceden kazanılmışsa girişte uzlaştırılır |

`zapeg_tames` ve `zapeg_chest_s` scoreboard'ları canlı test/sayaç görünümü
sağlar. Modlu canlıların hepsi vanilla tame tetikleyicisini kullanmayabilir;
ilk test kurt/kedi/at ile yapılmalıdır.

## İncelemeli kişisel hedefler ve doğrudan ödüller

Yapının niteliği salt blok sayısıyla güvenilir biçimde ölçülemez. Bu iki görevde
oyuncu tiki yoktur; OP aşağıdaki ölçütleri dünyada görür ve yalnız doğru login
çevrimiçiyken kriteri verir:

| Login | Hedef | İnceleme tabanı | Yalnız sahibine bir kez verilen eşya |
|---|---|---|---|
| `MertOnal` | Ev | Kapalı dış duvar/çatı, kapı, yatak, ışık, sandık; oyuncu yapı yanında | `MertOnal'ın Tapusu` (brick) |
| `eminomi12` | Kasaba fıskiyesi | Ortak alan, görünür su/havuz, ışık; yol veya yapıları su basmıyor | `Kasaba Fıskiyesinin Kalbi` (heart of the sea) |

İki owner-UUID ejderha görevi de aynı teslimat kanalını kullanır: `Emir'in
Ejderha Boynuzu` ve `Salih'in Ejderha Düdüğü` yalnız ilgili exact login'e
(`SalihKarahan` dahil) bir kez verilir.

Onay komutları:

```mcfunction
advancement grant MertOnal only zapeg:verified merton_house
advancement grant eminomi12 only zapeg:verified emin_fountain
```

Ödül, kriter görüldükten sonra en geç bir saniye içinde doğrudan exact login'e
verilir. Eşya NBT'sinde `zapeg.personal`, `zapeg.owner`, `zapeg.quest` ve sürüm
işaretleri vardır; FTB Teams ödül talebi kullanılmaz. Envanter doluysa eşya yere
düşürülmez; yer açılana kadar teslimat yeniden denenir. Yanlış onayda kriteri `revoke`
edin, ardından teslim edilmiş hatıra eşyasını operatör olarak geri alın. Bu
etiket hedef sahibini gösterir ama eşyayı başkasına vermeyi veya başkasının
kullanmasını teknik olarak engellemez. Eşyalar kişisel hatıra/işlevsel araçtır;
OP, claim bypass veya başka yönetim gücü vermez.

## Otomatik ve incelemeli grup hedefleri

- Otomatik: Wither ölümü, Ender Dragon, MineColonies 10 nüfus, aynı oyuncunun
  Ay'a gidip Overworld'e dönmesi, bir oyuncunun kendi tamed Ice and Fire
  ejderhasına binmesi, whitelist'teki Cataclysm boss ölümleri ve Chaos Guardian
  ölümü.
- Yetkili incelemesi: spawn kasabası, üç çalışan waystone ve güvenli Mekanism
  fisyon reaktörü.

İnceleme tamamlanınca çevrimiçi ortak takım üyelerinden birine konsoldan:

```mcfunction
advancement grant <oyuncu> only zapeg:verified town
advancement grant <oyuncu> only zapeg:verified waystones
advancement grant <oyuncu> only zapeg:verified reactor
```

Yanlış onay aynı komutta `grant` yerine `revoke` ile geri alınır; ardından
ilgili FTB task ilerlemesi de `ftbquests change_progress` ile resetlenir.

## Canlıya geçiş

Advancement veri paketi eklendiği için yalnız hot reload yeterli değildir:

```bash
./scripts/snapshot.sh pre-quest-authority
./scripts/apply-overrides.sh
docker compose restart mc
docker compose logs --tail=200 mc
```

Sunucu açıldıktan sonra OP olarak `/kubejs errors` kontrol edilir. Quest book'ta
ZapeG ve Kilometre Taşları sayfalarındaki başarı kutularının artık tıklanamaz
advancement task olarak göründüğü iki farklı istemcide doğrulanır.

Yeni zincirlerin kısa kabul testi:

1. Emir veya Salih kendi evcil Ice and Fire ejderhasına biner; ilgili kişisel
   kriter ve grup `dragon_rider` kriteri açılır. Başkasına ait ejderha kişisel
   kriteri açmamalıdır.
2. Bir kişisel ödül teslim olurken NBT sahibi doğru, FTB ödül talebi yok ve aynı
   kriter sonraki girişte ikinci eşya üretmiyor olmalıdır.

Eklenen mod chapter'larının temsilî kabul testi:

1. OP olmayan iki takım üyesiyle Ice and Fire Bestiary ve Immersive Petroleum
   projector advancement'larını ayrı ayrı tetikleyin; FTB Teams ilerlemesinin
   beklenen üyeye/takıma yansıdığını doğrulayın. Advancement daha önce alınmışsa
   chapter kurulumundan sonraki yeniden uzlaştırmayı da test edin.
2. `/zapeg-guide open petroleum` ve `/zapeg-guide open immersive_vehicles`
   komutlarını normal oyuncuyla çalıştırın. Yalnız doğru landing quest açılmalı;
   progress ve ödül değişmemeli.
3. IV dalında Car Handbook ve üç workbench item task'ını deneyin; belirli araç
   NBT'si istenmemeli. Küçük resmi-pack aracını sürüp chunk'ı unload/reload edin,
   geri dönün ve yalnız gerçek kalıcılık testinden sonra manuel düğmeye basın.
4. Eureka prototipini ve Nifty sloop'u ayrı alanlarda test edin. Nifty gemisini
   anchor + iki uçlu mooring ile bırakıp 16+ chunk uzaklaşın, geri dönün ve
   restart/reconnect sonrası kargo ile gövdenin kaldığını doğrulayın. Hiçbir IV,
   Eureka/VS, Nifty veya hareketli Create sistemini diğerinin üstüne koymayın.
5. Citizens brain gerçekten açıkken OP bir test çalışanı provision etsin.
   Oyuncu `@Ad status`, bounded hareket işi ve `@Ad stop` akışını görmeden final
   manuel task'ı tamamlamasın. Sunucuya ait lore vatandaşı fiziksel oyuncu işi
   almamalı; onun `/citizen task` yolu yalnız oyun içi OP içindir.
6. Incendium için eski Nether chunk'ının değişmediğini ve uzak portalın yeni
   üretilen bölgede farklı içerik verdiğini doğrulayın; dönüş portalı/waystone
   güvenli olmadan keşif tikini işaretlemeyin.
7. Muhtar'ın her quest handoff'unu üç kez aç/kapatın. NPC diyaloğu FTB ekranının
   altında açık kalmamalı; test matrisi `MUHTAR-QUEST-GUIDE-TR.md` içindedir.

Yeni dört task daha önce var olmadığı için eski onur-tiki temizleme listesine
eklenmez; aşağıdaki resetler yalnız eski task ID'leri içindir.

Mevcut task ID'leri korunduğu için daha önce elle atılmış tikler kendiliğinden
silinmez. Dünya yedeğinden sonra yalnız sahte/deneme ilerlemelerini resetleyin:

```mcfunction
ftbquests change_progress @a reset 42FCD9CE56EAB362
ftbquests change_progress @a reset 622EE803CEEB2DD6
ftbquests change_progress @a reset 9ADC70D84AC65478
ftbquests change_progress @a reset AF8E7862041DE12C
ftbquests change_progress @a reset DDFBB6C45DD5E98B
ftbquests change_progress @a reset 6145EFCD1DBEA350
ftbquests change_progress @a reset 46E2095F2357426F
ftbquests change_progress @a reset 8CA72E3EF31E3419
ftbquests change_progress @a reset 000E3123FACFC641
ftbquests change_progress @a reset 55F51C09F9CA1025
ftbquests change_progress @a reset CDDB1C66FE19DD82
ftbquests change_progress @a reset D416C228525ED49F
ftbquests change_progress @a reset 15ED4390EB972793
ftbquests change_progress @a reset 26BEE202F4AB1770
ftbquests change_progress @a reset B86D6769503F1DF9
ftbquests change_progress @a reset 88AD1A6A59C28098
ftbquests change_progress @a reset 32E1DC6BB2D341C9
ftbquests change_progress @a reset 5ACF092BB3044DD3
ftbquests change_progress @a reset C86F5A9CA10749C7
ftbquests change_progress @a reset E39F217E73843A49
ftbquests change_progress @a reset A020A1076698863D
ftbquests change_progress @a reset 0FDC3E3C48594883
ftbquests change_progress @a reset 18C6DC9B44DFC49F
ftbquests change_progress @a reset EF90D40A19C1D872
ftbquests change_progress @a reset 8E33CA264762AA20
```

Reset sonrası hoş geldin, dragon, 64 elmas, minecart ve mevcut vanilla/mod
advancement'lar yeniden uzlaştırılır; evcilleştirme, sandık ve yangın sayaçları
dağıtımdan sonra yapılan eylemleri sayar.

## Kimlik sınırı

Sunucu `online-mode=false` iken bu sistem eylemi yapan Minecraft login adını
kanıtlar, klavyedeki gerçek insanı değil. Kişiye güç/OP/claim bypass veren
ödüller bağlanmamalıdır. Gerçek kişi garantisi istenirse ayrı kararla
`online-mode=true`; en azından kapalı grup için whitelist gerekir.

## Sonraki kişi zincirleri

- Emir: sabit checkpoint kutuları ve scoreboard süreli yarış ligi.
- Emin: public hayvanat bahçesi; kaliteyi NPC/OP kayıt eder, BlueMap yalnız
  kamusal yapının marker'ını gösterir.
- Mert Onal: 5 km minecart ve ev görevi canlı; sonraki adım resmi araç paketiyle
  bir garaj veya yolculuk zinciridir.
- Salih + Mert: belirlenmiş eğitim koordinatında ortak yangın sigortası tatbikatı.
- Recep: 120 saniye nöbetten sonra kasaba arşivi/charter sorumluluğu.
- Enes (`Thekingim`): jetpack uçuş lisansı.
- Yusuf, Ali ve Ertu: login'leri gelince ilk ziyaret/waystone
  pasaportu; tahminî isimle kişisel hak açılmaz.
