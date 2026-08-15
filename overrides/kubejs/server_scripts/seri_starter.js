// Seri starter kit + custom recipes — SERVER-SIDE ONLY.
// No registered items/startup scripts => stock ATM9 clients stay 100% compatible
// (recipes and given items sync from the server).
// Deploy: scripts/apply-overrides.sh ; reload: /kubejs reload server_scripts

const KIT_STAGE = 'seri_starter_kit'

PlayerEvents.loggedIn(event => {
  const p = event.player
  if (p.stages.has(KIT_STAGE)) return
  p.stages.add(KIT_STAGE)

  p.give(Item.of('minecraft:bread', 16))
  p.give(Item.of('minecraft:torch', 64))
  p.give('waystones:warp_stone')

  p.tell(Text.of('Seri ATM9+\'a hoş geldin! Başlangıç kitin envanterinde, yol haritası quest book\'ta (sol üst).').gold())
})

ServerEvents.recipes(event => {
  // Name tag vanilla'da craft edilemez — ejderha sahipleri için bizim tarif:
  // kağıt + ip + demir külçe (shapeless)
  event.shapeless('minecraft:name_tag', [
    'minecraft:paper',
    'minecraft:string',
    'minecraft:iron_ingot'
  ]).id('seri:name_tag')
})
