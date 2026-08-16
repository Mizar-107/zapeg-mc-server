# ZapeG görsel ön-ayarı (shaders açık başlasın)

ATM9 zaten Oculus + Embeddium + Complementary shader paketleriyle geliyor — kapalı duruyorlar. Buradaki ön-ayarlar yeni profilde shader'ı **açık** getirir.

Yeni oyuncular ayrıca bir defaults zip'i kurmaz. `Build-ClientZip.ps1 -PatchOnly` tarafından üretilen tek **ZapeG Kurulum Yaması**, Oculus shader ayarını ve PackMenu logosunu doğru yapıyla ekler. Lisanslı oyuncunun bütün kişisel ayarlarını tutan `options.txt` bilerek yamaya konmaz.

- Shader aç/kapa tuşu: **K**
- Kasarsa: Video Settings → Shader Packs → **MakeUp-UltraFast** seç (o da pakette var)
- "Shader seçili ama açılmıyor" dersen: `shaderpacks/` klasöründeki gerçek dosya adına bak, `config/oculus.properties` içindeki `shaderPack=` satırını eşitle

Eski bir profilde yalnızca `config/oculus.properties` dosyasını kopyalamak güvenlidir. `options.txt` dosyasını kopyalamak tuş, dil, ses, video ve erişilebilirlik ayarlarını sıfırlar; sadece sıfırdan kurulan offline profilde kullanılır.
