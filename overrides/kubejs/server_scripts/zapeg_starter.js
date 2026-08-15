// ZapeG starter kit + custom recipes — SERVER-SIDE ONLY.
// No registered items/startup scripts => stock ATM9 clients stay 100% compatible
// (recipes and given items sync from the server).
// Deploy: scripts/apply-overrides.sh ; reload: /kubejs reload server_scripts

const KIT_STAGE = 'zapeg_starter_kit'

// Kişiye özel ilk-giriş hediyeleri (isimli eşyalar; şaka gereği).
// Anahtar = Minecraft kullanıcı adı — nick'ler netleşince güncelle.
const PERSONAL_GIFTS = {
  'kralxlarge': { item: 'minecraft:compass',        name: 'Acele Etme Pusulası' },   // Emir
  'Mizar__107': { item: 'minecraft:stick',          name: 'Admin Sopası' },          // Recep
  'Enes':       { item: 'minecraft:feather',        name: 'Jetpack Ruhu' },          // Iron Jetpacks pakette, gerisi sende
  'Salih':      { item: 'minecraft:flint_and_steel', name: 'Salih\'in Çakmağı (Ev Yakmak Yasak)' },
  'Yusuf':      { item: 'minecraft:cake',           name: 'Hoş Geldin Pastası' },
  'Ali':        { item: 'minecraft:cake',           name: 'Hoş Geldin Pastası' },
  'Mert':       { item: 'minecraft:cake',           name: 'Nadir Ziyaretçi Pastası' },
}

PlayerEvents.loggedIn(event => {
  const p = event.player
  if (p.stages.has(KIT_STAGE)) return
  p.stages.add(KIT_STAGE)

  p.give(Item.of('minecraft:bread', 16))
  p.give(Item.of('minecraft:torch', 64))
  p.give('waystones:warp_stone')

  const gift = PERSONAL_GIFTS[p.username]
  if (gift) {
    p.give(Item.of(gift.item).withName(Text.of(gift.name).gold().italic(false)))
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
