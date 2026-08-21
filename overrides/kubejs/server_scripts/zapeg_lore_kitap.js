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
  zkReply(source, Text.of('/zapeg-kitap ver <oyuncu> <kitap>').yellow(), false)
  zkReply(source, Text.of('/zapeg-kitap hepsi <oyuncu>').yellow(), false)
  zkReply(source, Text.of('Harabe için: /place template zapeg:harabe_1 — sonra "kayip_sayfa" kitabını kürsüye sağ tıkla.').gray(), false)
}

function zkList(source) {
  const ids = zkBookIds()
  for (let i = 0; i < ids.length; i++) {
    const book = ZK_BOOKS[ids[i]]
    zkReply(source, Text.of('• ' + ids[i]).aqua()
      .append(Text.of(' — ' + book.title + ' (' + book.pages.length + ' sayfa)').gray()), false)
  }
  return 1
}

ServerEvents.commandRegistry(event => {
  const { commands: Commands, arguments: Arguments } = event

  const root = Commands.literal('zapeg-kitap')
    .requires(source => source.hasPermission(2))
    .executes(ctx => {
      zkUsage(ctx.source)
      return 1
    })

  const liste = Commands.literal('liste').executes(ctx => zkList(ctx.source))

  const ver = Commands.literal('ver')
  const bookIds = zkBookIds()
  // Sayısal/serbest argüman yerine kitap başına literal alt komut: bu Rhino
  // yapısında Arguments.STRING/INTEGER sarmalayıcıları güvenilmez (bkz.
  // zapeg_heraldor_servant.js "goto" notu) — literaller sekme tamamlama da verir.
  const verTarget = Commands.argument('target', Arguments.PLAYER.create(event))
  for (let i = 0; i < bookIds.length; i++) {
    const id = bookIds[i]
    verTarget.then(Commands.literal(id)
      .executes(ctx => zkGive(
        ctx.source,
        Arguments.PLAYER.getResult(ctx, 'target'),
        id
      ))
    )
  }
  ver.then(verTarget)

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
