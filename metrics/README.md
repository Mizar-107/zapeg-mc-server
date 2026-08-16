# ZapeG gözlemleme yığını

Yığın opt-in çalışır:

`minecraft-exporter 0.24.0 → Prometheus 3.12.0 → Grafana 13.1.0`

Hazır dashboard; online sayısı/geçmişi, genel ve boyut TPS'i, tick süresi,
aktif entity sayısı, oyun süresi, ölümler, mob öldürme, elmas cevheri,
mesafe, minecart mesafesi ve verilen hasarı gösterir. Prometheus veriyi 60
saniyede bir alır; 400 gün veya 10 GB sınırlarından hangisine önce ulaşırsa
onu uygular.

## Canlı sunucuda ilk açılış

Exporter RCON parolasını Minecraft ile paylaşmalıdır. Bu nedenle ilk açılış
planlı bir Minecraft yeniden yaratması/restartı gerektirir:

```bash
./scripts/snapshot.sh pre-metrics
openssl rand -hex 32
openssl rand -hex 32
# .env:
# RCON_PASSWORD=<ilk çıktı>
# GRAFANA_PASSWORD=<ikinci çıktı>
# GRAFANA_BIND_ADDRESS=127.0.0.1
# GRAFANA_ANONYMOUS_ENABLED=false

docker compose --profile metrics pull metrics-exporter prometheus grafana
docker compose --profile metrics up -d --force-recreate \
  mc backup metrics-exporter prometheus grafana
```

İki sırrı birbirinden farklı tutun; sohbete, dokümana veya repoya koymayın.
RCON portu hosta açılmaz. BlueMap render cache'i günlük dünya arşivlerinden
çıkarılmıştır; dünya verisinin kendisi yedeklenmeye devam eder.

## Erişim

Grafana varsayılan olarak yalnız sunucunun `127.0.0.1:3000` adresini dinler.
Yönetici bilgisayarından en basit güvenli erişim:

```bash
ssh -L 3000:127.0.0.1:3000 <sunucu-kullanicisi>@zapeg.duckdns.org
```

Ardından tarayıcıda `http://127.0.0.1:3000` açılır. Gruba kalıcı web erişimi
verilecekse 443/HTTPS üzerinde kimlik doğrulamalı reverse proxy veya VPN
kullanın. `zapeg.duckdns.org:3000` portunu doğrudan NAT/public açmayın.

## Doğrulama

```bash
docker compose --profile metrics ps
docker compose logs --tail=100 metrics-exporter prometheus grafana
docker compose exec mc curl -fsS http://metrics-exporter:9150/metrics \
  | grep -E 'minecraft_(tps|ticktime_ms|player_online|play_time_ticks_total)' \
  | head -30
```

Grafana'da **ZapeG — Sunucu** dashboard'unu açın. İlk scrape'ten sonra TPS
yaklaşık 20 ve `up{job="minecraft"}` değeri 1 olmalıdır.

Offline-mode yüzünden exporter oyuncu etiketini UUID olarak üretir. Prometheus
şimdilik doğrulanmış beş login'i yeniden adlandırır: `kralxlarge`,
`Mizar__107`, `eminomi12`, `MertOnal`, `SalihKarahan`. Yeni bir
gerçek nick kesinleşince `metrics/prometheus.yml` içindeki eşleme
genişletilir; tahminî ad eklenmez.

## Güvenlik notu

Grafana anonymous erişimi varsayılan kapalıdır. Bir reverse proxy arkasında
özellikle istenirse `GRAFANA_ANONYMOUS_ENABLED=true` yapılabilir, ancak rol
Viewer olarak kalmalıdır. BlueMap de oyuncu ve yapı konumlarını gösterebildiği
için aynı erişim sınırının arkasına alınmalıdır.
