# ZapeG — Oyuncu Kurulumu

ZapeG, **All the Mods 9 sürüm 1.1.1** üzerine hazırlanmıştır. Modları tek tek indirmen gerekmiyor.

> Telefonda daha rahat okunan görsel sürüm: `zapeg-kurulum.html`

## Lisanslıysan en kısa yol

1. CurseForge'dan **ATM9 1.1.1** kur.
2. **Profile Options** içinden modloader sürümünü **Forge 47.4.10** yap.
3. Oyunu ve CurseForge'ı kapat; `mods` içindeki tüm `cc-tweaked-1.20.1-forge-*.jar` ve `zapeg-citizens-forge-1.20.1-*.jar` dosyalarını sil. Buna eski `cc-tweaked-1.20.1-forge-1.113.1.jar` ve `zapeg-citizens-forge-1.20.1-0.2.0.jar` da dahildir.
4. Ertu'nun gönderdiği **tek ZapeG Kurulum Yaması zip'ini** profil klasörüne aç.
5. Kullanıcı adını bir kez seç ve sunucuya gir. Kişisel karşılama istiyorsan adı Ertu'ya ayrıca bildir.

> Önemli: Sunucu offline-mode çalışır. Kullanıcı adın envanter, claim ve kişisel lore kimliğindir. Bir ad seçtikten sonra değiştirme.

## Yol A — Minecraft lisansın varsa (önerilen)

Gerekenler:

- CurseForge App
- `ZapeG-Kurulum-Yamasi-ATM9-1.1.1-YYYYMMDD.zip` — Ertu paylaşacak
- Kullanacağın sabit kullanıcı adı

Adımlar:

1. [CurseForge App](https://www.curseforge.com/download/app) uygulamasını kur.
2. **Minecraft → Browse Modpacks → All the Mods 9 → Install** yolunu izle.
3. Profil sayfasında **⋮ → Change Version** ile sürümün **1.1.1** olduğunu doğrula.
4. **⋮ → Profile Options → Modloader Version** yolundan **Forge 47.4.10** seçip **Done** de. [CurseForge'un görsel anlatımı](https://support.curseforge.com/support/solutions/articles/9000230030-changing-the-modloader-version-of-a-modpack-or-custom-profile)
5. Aynı menüden **⋮ → Open Folder** seçeneğine bas. Açılan klasör senin profil kökün.
6. Minecraft'ı ve CurseForge'ı tamamen kapat.
7. Yamayı çıkarmadan önce `mods` içindeki **tüm** `cc-tweaked-1.20.1-forge-*.jar` ve `zapeg-citizens-forge-1.20.1-*.jar` dosyalarını sil. Özellikle `cc-tweaked-1.20.1-forge-1.113.1.jar` ve `zapeg-citizens-forge-1.20.1-0.2.0.jar` artık bulunmamalı.
8. ZapeG kurulum zip'inin **içindekileri**, az önce açılan profil klasörüne çıkar. ZapeG dosyaları için üzerine yazma sorulursa onayla; yama kişisel `options.txt` dosyanı içermez, tuş/ses/dil ayarlarını sıfırlamaz.
9. Doğru kurulumda şu yapı görünür:

   ```text
   All the Mods 9\
   ├─ mods\
   │  ├─ iceandfire-....jar
   │  └─ ...diğer ZapeG modları
   ├─ config\
   ├─ packmenu\
   ├─ INSTALL-TR.txt
   └─ ZAPEG-BUILD.txt
   ```

   `All the Mods 9\ZapeG-Kurulum-Yamasi-...\mods` şeklinde iç içe klasör oluştuysa yanlış yere çıkardın. Zip'in içindeki `mods` klasörü doğrudan profil kökünde olmalı.

   Ayrıca `mods` içinde yalnız `cc-tweaked-1.20.1-forge-1.116.1.jar` ve `zapeg-citizens-forge-1.20.1-0.2.1.jar` bulunmalı.

10. CurseForge ayarlarından Minecraft RAM'ini ayarla: 16 GB RAM'li bilgisayarda **8–10 GB**, 32 GB ve üzerindeyse **10–12 GB**.
11. Oyunu aç → **Multiplayer → Add Server** → adres: `81.213.77.41`.

Kurulum yaması 18 gerekli ek modu (Numen ve ZapeG Citizens dahil), ZapeG logosunu ve shader ayarını birlikte getirir. Oyuncuların ayrıca bir LLM anahtarı veya ayrı uygulama kurması gerekmez. Shader varsayılan olarak açıktır; oyun içinde **K** ile kapatabilirsin.

## Yol B — Lisansın yoksa

Ertu sana `ZapeG-Offline-ATM9-1.1.1-YYYYMMDD.zip` dosyasını verecek. Bu dosya bir launcher veya Forge kurucusu değildir; hazır oyun-dizini içeriğidir.

1. Kullandığın launcher'da **Minecraft 1.20.1 + Forge 47.4.10** kullanan yeni ve izole bir profil oluştur. Launcher Java sürümü sorarsa **Java 17** seç.
2. Kullanıcı adını bir kez seç; sonra değiştirme.
3. Profili bir kez açıp ana menüye gel, sonra oyunu ve launcher'ı kapat.
4. Launcher'dan o profilin **oyun klasörünü** aç. Global `.minecraft` veya başka bir modpack klasörü kullanma.
5. Zip'i çıkarmadan önce `mods` içindeki tüm `cc-tweaked-1.20.1-forge-*.jar` ve `zapeg-citizens-forge-1.20.1-*.jar` dosyalarını sil; buna eski `cc-tweaked-1.20.1-forge-1.113.1.jar` ve `zapeg-citizens-forge-1.20.1-0.2.0.jar` da dahildir.
6. Offline zip'inin içindekileri bu oyun klasörüne çıkar; üzerine yazmayı onayla.
7. `mods\iceandfire-....jar` dosyasının doğrudan profil altında olduğunu ve yalnız `cc-tweaked-1.20.1-forge-1.116.1.jar` ile `zapeg-citizens-forge-1.20.1-0.2.1.jar` bulunduğunu kontrol et. Arada ikinci bir ZapeG klasörü olmamalı.
8. RAM'i **8–10 GB** yap, oyunu aç ve `81.213.77.41` adresine bağlan.

Launcher'da izole profil/oyun klasörü oluşturma seçeneğini bulamıyorsan rastgele klasöre kurma; ekran görüntüsüyle Ertu'ya sor.

## ZapeG Citizens kullanımı

Bir OP sana bir vatandaş atadıktan sonra normal Minecraft sohbetine adını `@` ile
yazarak görev verirsin:

```text
@Atlas git demir topla
```

Bu komut genel sohbette yayınlanmaz; yalnız sana atanmış vatandaşı kontrol
edebilirsin. Devam eden görevi hemen durdurmak için:

```text
@Atlas stop
```

İlk kazma, savaş veya eşya taşıma denemelerini evlerin yanında değil, boş ve
claim'siz bir test alanında yap. Oyuncu tarafında Ollama anahtarı veya ayrı bir
uygulama gerekmez.

## Sorun giderme

### “Mod uyuşmazlığı” veya girişte mod listesi hatası

- ATM9 sürümünün **1.1.1** olduğunu kontrol et.
- Modloader sürümünün **Forge 47.4.10** olduğunu kontrol et.
- Profil kökünde `ZAPEG-BUILD.txt` var mı kontrol et.
- `mods` içinde ZapeG modlarından birinin iki farklı sürümü varsa eski jar'ı kaldır. Yalnız `cc-tweaked-1.20.1-forge-1.116.1.jar` ve `zapeg-citizens-forge-1.20.1-0.2.1.jar` kalmalı; eski 1.113.1 ve Citizens 0.2.0 silinmelidir.
- Yama zip'ini yanlışlıkla iç içe klasöre açmadığından emin ol.

### Oyun açılırken çöküyor veya çok kasıyor

- Önce ayrılan RAM'i kontrol et.
- Shader'ı **K** ile kapat.
- Render distance değerini 8'e indir.
- Devam ederse `crash-reports` klasöründeki en yeni dosyayı gruba gönder.

## Güncellemeler

Yeni bir ZapeG yaması paylaşılmadıkça hiçbir şeyi elle güncelleme. Yeni yama duyurulursa Minecraft kapalıyken talimattaki gibi profil köküne uygula. Mod sürümü değişen güncellemelerde Ertu eski jar'ın kaldırılması gerekip gerekmediğini ayrıca söyleyecek.
