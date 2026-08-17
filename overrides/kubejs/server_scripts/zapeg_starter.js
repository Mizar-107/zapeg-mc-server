// ZapeG starter kit + custom recipes — SERVER-SIDE ONLY.
// No registered items/startup scripts => stock ATM9 clients stay 100% compatible
// (recipes and given items sync from the server).
// Deploy: scripts/apply-overrides.sh ; reload: /kubejs reload server_scripts

const KIT_STAGE = 'zapeg_starter_kit'
const MERT_GIFT_STAGE = 'zapeg_mert_personal_gift_v1'
const SALIH_GIFT_STAGE = 'zapeg_salih_personal_gift_v1'
const ENES_GIFT_STAGE = 'zapeg_enes_personal_gift_v1'

// Kişiye özel ilk-giriş hediyeleri (isimli eşyalar; şaka gereği).
// Anahtar = Minecraft kullanıcı adı — nick'ler netleşince güncelle.
const PERSONAL_GIFTS = {
  'kralxlarge': { item: 'minecraft:compass',        name: 'Acele Etme Pusulası' },   // Emir
  'Mizar__107': { item: 'minecraft:stick',          name: 'Admin Sopası' },          // Recep
  'eminomi12':  { item: 'minecraft:lead',           name: 'Hayvanat Bahçesi Ruhsatı' }, // Emin Taha
  'MertOnal':   { item: 'minecraft:minecart',       name: 'Araba Modu Geldi — Hatıra Vagonu' }, // Mert
  'Thekingim':  { item: 'minecraft:feather',        name: 'Jetpack Ruhu' },          // Enes — Iron Jetpacks pakette
  'SalihKarahan': { item: 'minecraft:flint_and_steel', name: 'Salih\'in Çakmağı (Ev Yakmak Yasak)' }, // Salih
  'Yusuf':      { item: 'minecraft:cake',           name: 'Hoş Geldin Pastası' },
  'Ali':        { item: 'minecraft:cake',           name: 'Hoş Geldin Pastası' },
  'Mert':       { item: 'minecraft:cake',           name: 'Nadir Ziyaretçi Pastası' }, // Diğer Mert; nick bekleniyor
}

PlayerEvents.loggedIn(event => {
  const p = event.player
  const username = String(p.username)

  // Mert's, Salih's and Enes's former keys were wrong/placeholders. If a
  // corrected login already claimed the generic kit, deliver only its missed gift.
  if (p.stages.has(KIT_STAGE)) {
    if (username === 'MertOnal' && !p.stages.has(MERT_GIFT_STAGE)) {
      const gift = PERSONAL_GIFTS[username]
      p.give(Item.of(gift.item).withName(Text.of(gift.name).gold().italic(false)))
      p.stages.add(MERT_GIFT_STAGE)
      p.tell(Text.of('Düzeltilen nick hediyen teslim edildi: Araba Modu Geldi — Hatıra Vagonu').gold())
    }
    if (username === 'SalihKarahan' && !p.stages.has(SALIH_GIFT_STAGE)) {
      const gift = PERSONAL_GIFTS[username]
      p.give(Item.of(gift.item).withName(Text.of(gift.name).gold().italic(false)))
      p.stages.add(SALIH_GIFT_STAGE)
      p.tell(Text.of('Düzeltilen nick hediyen teslim edildi: Salih\'in Çakmağı').gold())
    }
    if (username === 'Thekingim' && !p.stages.has(ENES_GIFT_STAGE)) {
      const gift = PERSONAL_GIFTS[username]
      p.give(Item.of(gift.item).withName(Text.of(gift.name).gold().italic(false)))
      p.stages.add(ENES_GIFT_STAGE)
      p.tell(Text.of('Exact nick hediyen teslim edildi: Jetpack Ruhu').gold())
    }
    return
  }
  p.stages.add(KIT_STAGE)

  p.give(Item.of('minecraft:bread', 16))
  p.give(Item.of('minecraft:torch', 64))
  p.give('waystones:warp_stone')

  const gift = PERSONAL_GIFTS[username]
  if (gift) {
    p.give(Item.of(gift.item).withName(Text.of(gift.name).gold().italic(false)))
    if (username === 'MertOnal') p.stages.add(MERT_GIFT_STAGE)
    if (username === 'SalihKarahan') p.stages.add(SALIH_GIFT_STAGE)
    if (username === 'Thekingim') p.stages.add(ENES_GIFT_STAGE)
  }

  p.tell(Text.of('ZapeG\'e hoş geldin! Başlangıç kitin envanterinde, yol haritası quest book\'ta (sol üst).').gold())
})

ServerEvents.recipes(event => {
  // Name tag vanilla'da craft edilemez — ejderha sahipleri için bizim tarif:
  // kağıt + ip + demir külçe (shapeless)
  event.shapeless('minecraft:name_tag', [
    'minecraft:paper',
    'minecraft:string',
    'minecraft:iron_ingot'
  ]).id('zapeg:name_tag')
})
