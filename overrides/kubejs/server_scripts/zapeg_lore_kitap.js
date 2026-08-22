// ZapeG lore kitapları — SERVER-SIDE ONLY, OP aracı.
// /zapeg-kitap: Muhtar'ın defterlerini (yazılı kitap) oyunculara verir.
// Kitap 3 ("Kayıp Sayfa") harabe kürsüsüne konmak için tasarlandı:
//   /place template zapeg:harabe_1  →  kitabı elinde tut, kürsüye sağ tık.
// Oyunculara Heraldor'dan asla bahsedilmez; 9. kanun ve "Kayıp Sayfa"
// inkâr edilebilir göz kırpmalardır — açıklama yok, cevap yok.

const ZK_BOOKS = {
  kurulus: {
    title: 'Zape Kayıtları I — Kuruluş',
    author: 'Muhtar',
    pages: [
      'Sekiz kişi geldi. Ellerinde hiçbir şey, akıllarında her şey vardı.\n\nBuraya ZapeG dediler.\n\nNeden? Kimse hatırlamıyor. Ben yazıyorum diye biliyorlar.',
      'Toprak cömert çıktı. Demir istedik, verdi. Elmas istedik, nazlandı ama verdi.\n\nAy\'a bile gittik.\n\nAy bizi beklemiyordu.',
      'İlk kış bir ev yandı.\n\nKaza mıydı? Kimse sormadı. Ama o günden beri çakmaktaşları sayılıyor.\n\nKanun oldu bu. Cilt II\'ye yazdım.',
      'Görevim: saymak, yazmak, unutmamak.\n\nKim ne yaptı, kim ne yaktı, kim nereye gitti.\n\nBu defterler onun için var. Okuyan bilsin.',
      '— Muhtar\n\nZapeG\'in ilk günlerinde yazıldı.\n\nDevamı: Zape Kayıtları II.'
    ]
  },
  kanunlar: {
    title: 'Zape Kayıtları II — Kanunlar',
    author: 'Muhtar',
    pages: [
      'ZapeG Kanunları.\n\nKimse yazmadı bunları. Hep vardılar.\n\nBen sadece kâğıda geçirdim.',
      '1. Kimse kimsenin sandığına dokunmaz.\n\n2. Dokunan görülmüştür. Kim gördü, sorma.',
      '3. Yatağı olmayan geceye çıkmaz.\n\n4. Creeper\'ı evine sokan, evini creeper\'a vermiş sayılır.',
      '5. Elması olan konuşur. Olmayan kazar.\n\n6. Ay\'da bırakılan eşya Ay\'ındır.',
      '7. Muhtar her zaman haklıdır.\n\n8. Muhtar haksız çıkarsa 7. kanun uygulanır.',
      '9. Dokuzuncu kanun yoktur.\n\nDokuzuncu kanunu sormayın.'
    ]
  },
  tutanaklar: {
    // Nick beklemeyen oyuncu lore'u (owner 2026-08-21: "add lores without
    // waiting for their nicks, other players can still see"): meclis mizahı.
    title: 'Zape Kayıtları III — Meclis Tutanakları',
    author: 'Muhtar',
    pages: [
      'Meclis Tutanağı, Celse 1.\n\nGündem: Salih\'in osuruk şakaları.\n\nKarar: yasaklandı.\n\nEk karar: yasak işlemedi. Dosya kapandı.',
      'Celse 2: "Comolokko" nedir?\n\nSalih\'e soruldu. Cevap anlaşılamadı.\n\nKarar: sormamaya devam edilecek.',
      'Celse 3: Enes Öztürk\'ün android olduğu iddiası.\n\nKanıt: fazla düzgün yürüyor.\n\nSavunma: reddetmedi.\n\nKarar: gözlem sürecek.',
      'Celse 4: Mangal yetkisi.\n\nKarar: Yusuf Subaşı her mangalın doğal reisidir.\n\nKöz, ona sorulmadan dürtülemez.',
      'Celse 5: Emin\'in maaş talebi.\n\nDüzeltme: talep yok.\n\nKarar: bedava çalışmaya teşekkür edildi. Zam istemediği için plaket verilecek (bedava).',
      'Celse 6: Mert\'in demir-kömür dilekçesi.\n\n"Tek inşaat yapan benim, madem öyle demir gelsin."\n\nKarar: haklı. Kimse kazmadı.',
      'Celse 7: Sandık dokunulmazlığı ihlalleri.\n\nŞüpheli: bilinen biri (Enes K.).\n\nKarar: Kanun 2 okundu. Şüpheli "yamayı nasıl kuruyordum" diye sorarak oturumu dağıttı.',
      'Celse 8: Yunus\'a özel muamele iddiası.\n\nEmir: "evet, yapıyorum, ne olacak?"\n\nKarar: Trabzon\'a selam gönderildi. Oturum sevgi gösterileriyle kapandı.',
      'Celse 9: Emir\'in zartinium ruhsatı.\n\n"Zurtinium da olabilir" dedi.\n\nKarar: kazmasına izin verildi. Ne bulduğu sorulmayacak.',
      'Tutanakları tutan: Muhtar.\n\nOkuyan: siz.\n\nİtiraz süresi: geçti.'
    ]
  },
  kayip_sayfa: {
    title: 'Kayıp Sayfa',
    author: '…',
    pages: [
      '…saydım. Sekiz haneydi.\n\nDokuzuncu haneye kimse taşınmadı. Ama bacası tütüyor.\n\nGece sayınca dokuz çıkıyor. Gündüz sekiz.\n\nBir daha saymayacağım.',
      '(sayfanın gerisi yırtık)'
    ]
  }
}

function zkReply(source, text, failure) {
  if (failure) source.sendFailure(text)
  else source.sendSuccess(() => text, false)
}

function zkBookIds() {
  return Object.keys(ZK_BOOKS)
}

function zkMakeBook(id) {
  const book = ZK_BOOKS[id]
  if (!book) return null
  const pages = []
  for (let i = 0; i < book.pages.length; i++) {
    // written_book sayfaları JSON metin bileşeni ister.
    pages.push(JSON.stringify({ text: book.pages[i] }))
  }
  // JSON çıktısı geçerli SNBT'dir; nesne→NBT dönüşümüne güvenmek yerine
  // deterministik tek yol: stringify edilmiş compound.
  return Item.of('minecraft:written_book', JSON.stringify({
    title: book.title,
    author: book.author,
    generation: 0,
    pages: pages
  }))
}

function zkGive(source, target, id) {
  const item = zkMakeBook(id)
  if (!item) {
    zkReply(source, Text.of('Bilinmeyen kitap: ' + id).red(), true)
    return 0
  }
  target.give(item)
  zkReply(source, Text.of('📖 ').gold()
    .append(Text.of(ZK_BOOKS[id].title).aqua())
    .append(Text.of(' → ' + String(target.scoreboardName)).gray()), false)
  return 1
}

function zkGiveAll(source, target) {
  const ids = zkBookIds()
  let given = 0
  for (let i = 0; i < ids.length; i++) {
    given += zkGive(source, target, ids[i])
  }
  return given > 0 ? 1 : 0
}

function zkUsage(source) {
  zkReply(source, Text.of('/zapeg-kitap liste').yellow(), false)
  zkReply(source, Text.of('/zapeg-kitap ver kurulus|kanunlar|tutanaklar|kayip_sayfa <oyuncu>').yellow(), false)
  zkReply(source, Text.of('/zapeg-kitap hepsi <oyuncu>').yellow(), false)
  zkReply(source, Text.of('Harabe için: /place template zapeg:harabe_1 — sonra "kayip_sayfa" kitabını kürsüye sağ tıkla.').gray(), false)
}

function zkList(source) {
  const ids = zkBookIds()
  for (let i = 0; i < ids.length; i++) {
    var book = ZK_BOOKS[ids[i]]
    zkReply(source, Text.of('• ' + ids[i]).aqua()
      .append(Text.of(' — ' + book.title + ' (' + book.pages.length + ' sayfa)').gray()), false)
  }
  return 1
}

ServerEvents.commandRegistry(event => {
  const { commands: Commands, arguments: Arguments } = event

  console.log('[zapeg] /zapeg-kitap registering')
  const root = Commands.literal('zapeg-kitap')
    .requires(source => source.hasPermission(2))
    .executes(ctx => {
      zkUsage(ctx.source)
      return 1
    })

  const liste = Commands.literal('liste').executes(ctx => zkList(ctx.source))

  // GERÇEK kök neden (yerel test sunucusunda kanıtlandı, 2026-08-22):
  // döngü GÖVDESİNDEKİ `const id` — bu Rhino ikinci iterasyonda
  // "redeclaration of var" fırlatıyor, handler ölüyor, komut kayıt olmuyor
  // VE alfabetik sırada sonraki scriptlerin kayıtları da iptal oluyor
  // (canlıda unvan bu yüzden yoktu). Ağaç şekli suçsuzdu; yine de
  // literal-önce şekli kaldı (ver <kitap> <oyuncu>). Değer callback'e
  // parametreyle bağlanır (var kapatılırsa hepsi son kitabı verir).
  // Döngü değişkenini callback'e KAPATMA (var = tek paylaşılan binding, hepsi
  // son kitabı verir); değer bir fonksiyon PARAMETRESİ ile yakalanır — her
  // çağrı ayrı aktivasyon. zhAttachDirectorProfiles ile aynı desen.
  function zkAttachBook(parent, id) {
    parent.then(Commands.literal(id)
      .then(Commands.argument('target', Arguments.PLAYER.create(event))
        .executes(ctx => zkGive(
          ctx.source,
          Arguments.PLAYER.getResult(ctx, 'target'),
          id
        ))
      )
    )
  }
  const ver = Commands.literal('ver')
  const bookIds = zkBookIds()
  for (let i = 0; i < bookIds.length; i++) {
    zkAttachBook(ver, bookIds[i])
  }

  const hepsi = Commands.literal('hepsi')
    .then(Commands.argument('target', Arguments.PLAYER.create(event))
      .executes(ctx => zkGiveAll(
        ctx.source,
        Arguments.PLAYER.getResult(ctx, 'target')
      ))
    )

  root.then(liste)
  root.then(ver)
  root.then(hepsi)
  event.register(root)
})

console.log('[zapeg] zapeg_lore_kitap.js loaded (r3: const-in-loop fix + attach-helper — yerel Rhino testinde REG/RUN doğrulandı)')
