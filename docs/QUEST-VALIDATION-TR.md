# ZapeG görev doğrulama sistemi

## Model

FTB Quests artık başarı gerçeğinin sahibi değil; yalnız kitap ve ödül yüzeyidir.
`zapeg:verified` içindeki görünmez advancement kriterleri sunucu otoritesidir.
Başarı görevlerinde oyuncunun basabileceği `checkmark` bırakılmaz.

Yol Haritası da düzeltilmiştir: hoş geldin kriteri girişte; ilk gece yatakta
uyuyunca; teknoloji/büyü/ejderha yolları gerçek item görülünce; şehir/uzay/boss
yolları ilgili mod veya vanilla advancement'ı gelince açılır. Rehberde de boş
tikle kaynak alma kalmaz.

- Ölçülebilir hedef: KubeJS/vanilla/mod advancement olayı kriteri verir.
- Yapı, güvenlik veya kalite hedefi: OP dünyada gördükten sonra kriteri verir.
- FTB Teams ortak partisinde kriteri alan bir üye grup görevini tamamlar.
- Kupa item ödülleri `team_reward: true` olduğu için takım başına bir kez alınır.

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
| Mert | `MertOnal` | 64 ray yerleştirme | Exact actor + canlı dimension/koordinat defteri; aynı yer ikinci kez sayılmaz, eksilen ray düşer |
| Enes | kesin değil | Arbalet | Exact login girilene kadar kilitli; sonra `ol_betsy` |

`zapeg_tames`, `zapeg_chest_s` ve `zapeg_rails` scoreboard'ları canlı
test/sayaç görünümü sağlar. Ray defteri yalnız `MertOnal` tarafından 64 farklı
dimension/koordinata yerleştirilen vanilla rayları ve `create:track` bloklarını
sayar; her yeni yerleştirmede kayıtlı rayların hâlâ orada olduğu taranır. Böylece
tek rayı 64 yere taşıma ilerleme üretmez. Modlu canlıların hepsi vanilla
tame tetikleyicisini kullanmayabilir; ilk test kurt/kedi/at ile yapılmalıdır.
Dağıtımdan önce yerleştirilmiş rayların kimin tarafından konduğunu güvenilir
biçimde çıkaramadığımız için onlar geçmişe dönük sayılmaz.

## İncelemeli kişisel hedefler ve doğrudan ödüller

Yapının niteliği salt blok sayısıyla güvenilir biçimde ölçülemez. Bu iki görevde
oyuncu tiki yoktur; OP aşağıdaki ölçütleri dünyada görür ve yalnız doğru login
çevrimiçiyken kriteri verir:

| Login | Hedef | İnceleme tabanı | Yalnız sahibine bir kez verilen eşya |
|---|---|---|---|
| `MertOnal` | Ev | Kapalı dış duvar/çatı, kapı, yatak, ışık, sandık; oyuncu yapı yanında | `MertOnal'ın Tapusu` (brick) |
| `eminomi12` | Kasaba fıskiyesi | Ortak alan, görünür su/havuz, ışık; yol veya yapıları su basmıyor | `Kasaba Fıskiyesinin Kalbi` (heart of the sea) |

Otomatik 64-ray ve iki owner-UUID ejderha görevi de aynı teslimat kanalını
kullanır: `MertOnal Ekspresi`, `Emir'in Ejderha Boynuzu` ve `Salih'in Ejderha
Düdüğü` yalnız ilgili exact login'e (`SalihKarahan` dahil) bir kez verilir.

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

1. `MertOnal` bir vanilla ray koyar; `zapeg_rails` 1 olur. Rayı söküp başka yere
   taşıyınca sayaç 1'de kalır. Ardından bir `create:track` koyup sayacı kontrol
   edin; Create özel yerleştirme olayı bu sürümde sayılmazsa canlı görev metnini
   test düzelene kadar vanilla rayla sınırlayın.
2. Emir veya Salih kendi evcil Ice and Fire ejderhasına biner; ilgili kişisel
   kriter ve grup `dragon_rider` kriteri açılır. Başkasına ait ejderha kişisel
   kriteri açmamalıdır.
3. Bir kişisel ödül teslim olurken NBT sahibi doğru, FTB ödül talebi yok ve aynı
   kriter sonraki girişte ikinci eşya üretmiyor olmalıdır.

Yeni beş task daha önce var olmadığı için eski onur-tiki temizleme listesine
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
- Mert Onal: ev ve 64 farklı ray görevi canlı; sonraki adım bu hattı kasaba
  istasyonu veya limana bağlayan rota görevidir.
- Salih + Mert: belirlenmiş eğitim koordinatında ortak yangın sigortası tatbikatı.
- Recep: 120 saniye nöbetten sonra kasaba arşivi/charter sorumluluğu.
- Enes: exact nick sonrası jetpack uçuş lisansı.
- Yusuf, Ali ve Ertu: login'leri gelince ilk ziyaret/waystone
  pasaportu; tahminî isimle kişisel hak açılmaz.
