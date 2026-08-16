// ZapeG kişisel karşılama mesajları — SERVER-SIDE ONLY.
// Her girişte oyuncuya özel havuzdan rastgele bir satır herkese duyurulur.
//
// !!! ANAHTARLAR MINECRAFT KULLANICI ADI OLMALI (oyuna girilen adla birebir) !!!
// kralxlarge (Emir), Mizar__107 (Recep), eminomi12 (Emin Taha),
// MertOnal (araba meraklısı Mert) ve SalihKarahan (Salih) kesin.
// Enes/Yusuf/Ali/diğer Mert şimdilik gerçek adla.
// Deploy: scripts/apply-overrides.sh ; reload: /kubejs reload server_scripts

const WELCOME_LINES = {
  'kralxlarge': [                       // Emir — grinder, her şeyde birinci olacak
    'uyumadı, kazdı.',
    'nether daha açılmadan pusuya yattı.',
    'enderdragon şimdiden tedirgin.',
    'ilerleme barı yine ona yetişemiyor.',
    'boss\'lar toplantıya çağrıldı.',
  ],
  'Mizar__107': [                       // Recep — admin / sunucunun sahibi
    'admin geldi, düzgün oturun.',
    'yetkiyle giriş yapıldı.',
    'sunucunun efendisi döndü.',
    'log\'lar okunuyor, haberiniz olsun.',
  ],
  'eminomi12': [                       // Emin Taha — builder; köy speedrun'u + hayvan ordusu
    'usta geldi, şantiye yeniden açıldı.',
    'yarım kalan hardcore speedrun sessizce onu bekliyor.',
    'speedrun yine köy arama simülasyonuna döndü.',
    'köy çanları ve evcil hayvanlar tetikte.',
  ],
  'MertOnal': [                        // Mert — arabalar, ev + ray; Salih'in yaktığı eski ev
    'garaj hazır, araba modu hâlâ yok.',
    'minecart\'ı araba saymayı hâlâ reddediyor.',
    'bu ev için yangın sigortası yaptırdı.',
    'Salih\'e çakmak teslim formu imzalatıldı.',
    'şantiye açıldı, tapu sıraya girdi.',
    'ray ihalesini tek başına aldı.',
    'evin önünden tren geçecekmiş.',
  ],
  'Enes': [                             // jetpack özlemi
    'jetpack özlemi bugün bitebilir.',
    'önce jetpack, gerisi detay.',
    'gökyüzü hazırlıklara başladı.',
  ],
  'SalihKarahan': [                     // Salih — meşhur başkalarının evini yakma vakaları
    'evleri kilitleyin, kibritleri saklayın.',
    'itfaiye teyakkuza geçti.',
    'yangın sigortanızı yenileyin.',
    'çakmağı kapıda bıraktığını iddia ediyor.',
  ],
  'Yusuf': ['vay, gerçekten geldi!', 'takvime işaretleyin: bugün geldi.'],
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
