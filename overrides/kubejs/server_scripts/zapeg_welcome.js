// ZapeG kişisel karşılama mesajları — SERVER-SIDE ONLY.
// Her girişte oyuncuya özel havuzdan rastgele bir satır herkese duyurulur.
//
// !!! ANAHTARLAR MINECRAFT KULLANICI ADI OLMALI (whitelist'tekiyle birebir) !!!
// Aşağıdaki satırlar YER TUTUCU — grubun iç şakalarıyla değiştirin.
// Deploy: scripts/apply-overrides.sh ; reload: /kubejs reload server_scripts

const WELCOME_LINES = {
  // 'EnesinKullaniciAdi': [
  //   'iç şaka 1',
  //   'iç şaka 2',
  // ],
  // 'SalihinKullaniciAdi': [ ... ],
  // 'EmirinKullaniciAdi': [ ... ],
  // 'RecebinKullaniciAdi': [ ... ],
}

const DEFAULT_LINES = [
  'kapıları kilitleyin.',
  'ejderhalar haberdar edildi.',
  'madene inmeden dursun bakalım.',
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
