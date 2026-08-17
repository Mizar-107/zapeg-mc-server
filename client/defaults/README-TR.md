# ZapeG istemci ön-ayarları

ATM9 zaten Oculus + Embeddium + Complementary shader paketleriyle geliyor — kapalı duruyorlar. Buradaki ön-ayarlar yeni profilde shader'ı **açık** getirir ve Entity Culling'in Immersive Vehicles araçlarını yanlışlıkla görünmez yapmasını engeller.

Yeni oyuncular ayrıca bir defaults zip'i kurmaz. `Build-ClientZip.ps1 -PatchOnly` tarafından üretilen tek **ZapeG Kurulum Yaması**, Oculus shader ayarını, doğrulanmış `entityculling.json` dosyasını ve PackMenu logosunu doğru yapıyla ekler. Lisanslı oyuncunun bütün kişisel ayarlarını tutan `options.txt` bilerek yamaya konmaz.

- Shader aç/kapa tuşu: **K**
- Kasarsa: Video Settings → Shader Packs → **MakeUp-UltraFast** seç (o da pakette var)
- "Shader seçili ama açılmıyor" dersen: `shaderpacks/` klasöründeki gerçek dosya adına bak, `config/oculus.properties` içindeki `shaderPack=` satırını eşitle
- IV aracı kayboluyor/görünmüyorsa: `config/entityculling.json` içindeki `entityWhitelist` bölümünde `mts:builder_existing`, `mts:builder_rendering` ve `mts:builder_seat` bulunmalı
- Shader açıkken araç göstergesi/yakıt yazısı görünmüyorsa: **P → IV config → Rendering → `LightsTransp=true`** yap

Eski bir profilde özel Entity Culling ayarların varsa dosyayı körlemesine değiştirmek yerine yukarıdaki üç `mts:` kimliğini mevcut `entityWhitelist` listene birleştir. `options.txt` dosyasını kopyalamak tuş, dil, ses, video ve erişilebilirlik ayarlarını sıfırlar; sadece sıfırdan kurulan offline profilde kullanılır.
