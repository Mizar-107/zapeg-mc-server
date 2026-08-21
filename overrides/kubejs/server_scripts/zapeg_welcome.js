// ZapeG kişisel karşılama mesajları — SERVER-SIDE ONLY.
// Her girişte oyuncuya özel havuzdan rastgele bir satır herkese duyurulur.
//
// !!! ANAHTARLAR MINECRAFT KULLANICI ADI OLMALI (oyuna girilen adla birebir) !!!
// kralxlarge (Emir), Mizar__107 (Recep), eminomi12 (Emin Taha),
// MertOnal (araba meraklısı Mert), SalihKarahan (Salih),
// Thekingim (Enes Küçük) ve Darkfire6161 (Yunus Sancak) kesin.
// Yusuf (Subaşı) / Ali / diğer Mert / Enes (Öztürk) şimdilik gerçek adla.
// Deploy: scripts/apply-overrides.sh ; reload: /kubejs reload server_scripts

const WELCOME_LINES = {
  'kralxlarge': [                       // Emir — grinder; zartinium/zurtinium avcısı
    'uyumadı, kazdı.',
    'nether daha açılmadan pusuya yattı.',
    'enderdragon şimdiden tedirgin.',
    'ilerleme barı yine ona yetişemiyor.',
    'boss\'lar toplantıya çağrıldı.',
    'zartinium damarı bulundu, çoktan oraya gitti.',
    'zurtinium bitmeden uyumayacak.',
    'önemsiz-ium koleksiyonuna yeni parça arıyor.',
  ],
  'Mizar__107': [                       // Recep — admin / sunucunun sahibi
    'admin geldi, düzgün oturun.',
    'yetkiyle giriş yapıldı.',
    'sunucunun efendisi döndü.',
    'log\'lar okunuyor, haberiniz olsun.',
  ],
  'eminomi12': [                       // Emin Taha — hayvan ordusu; bedava çalışır
    'usta geldi, şantiye yeniden açıldı.',
    'yarım kalan hardcore speedrun sessizce onu bekliyor.',
    'speedrun yine köy arama simülasyonuna döndü.',
    'köy çanları ve evcil hayvanlar tetikte.',
    'bedava mesai resmen başladı.',
    'maaş yok. motivasyon tam.',
  ],
  'MertOnal': [                        // Mert — köyün tek gerçek inşaatçısı; demiri/kömürü hep eksik
    'garaj açıldı, araba modu sonunda geldi.',
    'minecart\'ı araba saymayı hâlâ reddediyor.',
    'bu ev için yangın sigortası yaptırdı.',
    'Salih\'e çakmak teslim formu imzalatıldı.',
    'köyün tek gerçek inşaatçısı iş başında.',
    'demir listesi yine kabardı, kömür stoğu kritik.',
  ],
  'Thekingim': [                        // Enes Küçük — sandık cevheri "ödünç" alır; her yamada kurulumu yeniden öğrenir
    'jetpack özlemi bugün bitebilir.',
    'önce jetpack, gerisi detay.',
    'sandıklarınızı sayın. o geldi.',
    'cevherler kendi kendine yer değiştirmez. değiştirirse o gelmiştir.',
    'istemci güncellemeyi bu yama için de yeniden öğrendi.',
  ],
  'SalihKarahan': [                     // Salih — yangın vakaları + osuruk şakaları + Comolokko
    'evleri kilitleyin, kibritleri saklayın.',
    'itfaiye teyakkuza geçti.',
    'yangın sigortanızı yenileyin.',
    'çakmağı kapıda bıraktığını iddia ediyor.',
    'Comolokko sesleri yaklaşıyor.',
    'osuruk şakası envanteri güncellendi, bölgeyi havalandırın.',
  ],
  'Darkfire6161': [                     // Yunus Sancak — Trabzon; herkesin sevdiği, Emir'in el üstünde tuttuğu
    'herkesin sevgilisi giriş yaptı.',
    'Trabzon\'dan canlı bağlantı kuruldu.',
    'Emir\'in özel karşılama protokolü devrede.',
    'hamsi stokları güncellendi.',
  ],
  'Yusuf': ['vay, gerçekten geldi!', 'takvime işaretleyin: bugün geldi.', 'mangal reisi geldi, közler hazırlansın.'],
  'Enes':  ['insan taklidi modülü aktif, hoş geldi.', 'pilini şarj etmiş, gelmiş.'],  // Enes Öztürk — nick bekleniyor; köy onu android sanıyor
  'Ali':   ['yılın sürprizi.', 'kendisi de şaşırdı ama geldi.'],
  'Mert':  ['efsaneye göre bazen giriş yaparmış.', 'ekran görüntüsü alın, kanıt lazım.'],
}

const DEFAULT_LINES = [
  'kapıları kilitleyin.',
  'ejderhalar haberdar edildi.',
  'bugün de bir şeyler patlayacak.',
  'quest book seni bekliyor.',
]

PlayerEvents.loggedIn(event => {
  const name = event.player.username
  const pool = WELCOME_LINES[name] && WELCOME_LINES[name].length
    ? WELCOME_LINES[name]
    : DEFAULT_LINES
  const line = pool[Math.floor(Math.random() * pool.length)]
  event.server.tell(
    Text.of('⚡ ').gold()
      .append(Text.of(name).aqua())
      .append(Text.of(' geldi — ' + line).gray())
  )
})
