# ZapeG — Oyuncu Kurulumu

ZapeG, **All the Mods 9 sürüm 1.1.1** üzerine hazırlanmıştır. Modları tek tek indirmen gerekmiyor.

> Telefonda daha rahat okunan görsel sürüm: `zapeg-kurulum.html`

## Lisanslıysan en kısa yol

1. CurseForge'dan **ATM9 1.1.1** kur.
2. **Profile Options** içinden modloader sürümünü **Forge 47.4.10** yap.
3. Ertu'nun gönderdiği **tek ZapeG Kurulum Yaması zip'ini** profil klasörüne aç.
4. Kullanıcı adını bir kez seç ve sunucuya gir. Kişisel karşılama istiyorsan adı Ertu'ya ayrıca bildir.

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
7. ZapeG kurulum zip'inin **içindekileri**, az önce açılan profil klasörüne çıkar. ZapeG dosyaları için üzerine yazma sorulursa onayla; yama kişisel `options.txt` dosyanı içermez, tuş/ses/dil ayarlarını sıfırlamaz.
8. Doğru kurulumda şu yapı görünür:

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

9. CurseForge ayarlarından Minecraft RAM'ini ayarla: 16 GB RAM'li bilgisayarda **8–10 GB**, 32 GB ve üzerindeyse **10–12 GB**.
10. Oyunu aç → **Multiplayer → Add Server** → adres: `81.213.77.41`.

Kurulum yaması 17 gerekli ek modu, ZapeG logosunu ve shader ayarını birlikte getirir. Shader varsayılan olarak açıktır; oyun içinde **K** ile kapatabilirsin.

## Yol B — Lisansın yoksa

Ertu sana `ZapeG-Offline-ATM9-1.1.1-YYYYMMDD.zip` dosyasını verecek. Bu dosya bir launcher veya Forge kurucusu değildir; hazır oyun-dizini içeriğidir.

1. Kullandığın launcher'da **Minecraft 1.20.1 + Forge 47.4.10** kullanan yeni ve izole bir profil oluştur. Launcher Java sürümü sorarsa **Java 17** seç.
2. Kullanıcı adını bir kez seç; sonra değiştirme.
3. Profili bir kez açıp ana menüye gel, sonra oyunu ve launcher'ı kapat.
4. Launcher'dan o profilin **oyun klasörünü** aç. Global `.minecraft` veya başka bir modpack klasörü kullanma.
5. Offline zip'inin içindekileri bu oyun klasörüne çıkar; üzerine yazmayı onayla.
6. `mods\iceandfire-....jar` dosyasının doğrudan profil altında olduğunu kontrol et. Arada ikinci bir ZapeG klasörü olmamalı.
7. RAM'i **8–10 GB** yap, oyunu aç ve `81.213.77.41` adresine bağlan.

Launcher'da izole profil/oyun klasörü oluşturma seçeneğini bulamıyorsan rastgele klasöre kurma; ekran görüntüsüyle Ertu'ya sor.

## Sorun giderme

### “Mod uyuşmazlığı” veya girişte mod listesi hatası

- ATM9 sürümünün **1.1.1** olduğunu kontrol et.
- Modloader sürümünün **Forge 47.4.10** olduğunu kontrol et.
- Profil kökünde `ZAPEG-BUILD.txt` var mı kontrol et.
- `mods` içinde ZapeG modlarından birinin iki farklı sürümü varsa eski jar'ı kaldır.
- Yama zip'ini yanlışlıkla iç içe klasöre açmadığından emin ol.

### Oyun açılırken çöküyor veya çok kasıyor

- Önce ayrılan RAM'i kontrol et.
- Shader'ı **K** ile kapat.
- Render distance değerini 8'e indir.
- Devam ederse `crash-reports` klasöründeki en yeni dosyayı gruba gönder.

## Güncellemeler

Yeni bir ZapeG yaması paylaşılmadıkça hiçbir şeyi elle güncelleme. Yeni yama duyurulursa Minecraft kapalıyken talimattaki gibi profil köküne uygula. Mod sürümü değişen güncellemelerde Ertu eski jar'ın kaldırılması gerekip gerekmediğini ayrıca söyleyecek.
