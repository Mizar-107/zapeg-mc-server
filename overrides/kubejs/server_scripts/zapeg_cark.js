// ZapeG Çarkı — SERVER-SIDE ONLY, herkese açık kumar komutu.
// /zapeg-cark oyna: ana eldeki elmasları (en fazla 16) çarka yatırır.
// Ağırlıklar (1000 üzerinden): x0=620, x2=260, x3=80, x5=35, x10=5
// Beklenen getiri ≈ 0.985 → kasa payı %1.5; kurallarda açıkça yazar.
// Büyük kazançlar (x5/x10) sunucu geneline duyurulur. Elmas dışında bahis yok.

const ZC_MAX_BET = 16
const ZC_SPIN_MS = 1800
const ZC_OUTCOMES = [
  { mult: 0, weight: 620 },
  { mult: 2, weight: 260 },
  { mult: 3, weight: 80 },
  { mult: 5, weight: 35 },
  { mult: 10, weight: 5 }
]
const ZC_WEIGHT_TOTAL = 1000
const ZC_BET_OBJECTIVE = 'zc_bet_total'
const ZC_WON_OBJECTIVE = 'zc_won_total'

// Çark dönerken ikinci bir oynamayı engelle (oyuncu adı → true).
const ZC_SPINNING = {}

const ZC_LOSS_LINES = [
  'Çark durdu: boş. Elmaslar kasaya.',
  'Bu sefer olmadı. Kasa teşekkür eder.',
  'Boş! Muhtar not aldı: bir daha düşün.',
  'Çark seni sevmedi. Belki bir dahaki sefere.'
]

function zcReply(source, text, failure) {
  if (failure) source.sendFailure(text)
  else source.sendSuccess(() => text, false)
}

function zcFindPlayer(server, name) {
  // server.getPlayer(name) bu Rhino yapısında güvenilir değil — listeden tara.
  let found = null
  server.players.forEach(p => {
    if (String(p.scoreboardName) === name) found = p
  })
  return found
}

function zcRoll() {
  let ticket = Math.floor(Math.random() * ZC_WEIGHT_TOTAL)
  for (let i = 0; i < ZC_OUTCOMES.length; i++) {
    ticket -= ZC_OUTCOMES[i].weight
    if (ticket < 0) return ZC_OUTCOMES[i].mult
  }
  return 0
}

function zcEnsureObjectives(server) {
  server.runCommandSilent(`scoreboard objectives add ${ZC_BET_OBJECTIVE} dummy`)
  server.runCommandSilent(`scoreboard objectives add ${ZC_WON_OBJECTIVE} dummy`)
}

function zcRules(source) {
  zcReply(source, Text.of('🎰 ZapeG Çarkı').gold(), false)
  zcReply(source, Text.of('Ana eline elmas al (1-' + ZC_MAX_BET + '), sonra: /zapeg-cark oyna').yellow(), false)
  zcReply(source, Text.of('Çarklar: x2 (%26) · x3 (%8) · x5 (%3.5) · x10 (%0.5) · boş (%62)').gray(), false)
  zcReply(source, Text.of('Kasa payı %1.5 — kasa her zaman kazanır, azar azar.').gray(), false)
  return 1
}

function zcPlay(source) {
  const player = source.player
  if (!player) {
    zcReply(source, Text.of('Bu komutu bir oyuncu kullanmalı.').red(), true)
    return 0
  }
  const name = String(player.scoreboardName)
  if (ZC_SPINNING[name]) {
    zcReply(source, Text.of('Çark zaten dönüyor. Sabret.').red(), true)
    return 0
  }
  const held = player.getMainHandItem()
  if (!held || String(held.id) !== 'minecraft:diamond') {
    zcReply(source, Text.of('Bahis için ana eline elmas al.').red(), true)
    return 0
  }
  const count = Number(held.count)
  if (!(count > 0)) {
    zcReply(source, Text.of('Bahis için ana eline elmas al.').red(), true)
    return 0
  }
  if (count > ZC_MAX_BET) {
    zcReply(source, Text.of('Tek seferde en fazla ' + ZC_MAX_BET + ' elmas. Fazlasını cebe koy.').red(), true)
    return 0
  }
  const bet = count
  const server = player.server
  const mult = zcRoll()

  // Önce sonucu planla, SONRA bahsi al: planlama patlarsa kimse elmas kaybetmez.
  server.scheduleInTicks(Math.max(1, Math.round(ZC_SPIN_MS / 50)), () => {
    delete ZC_SPINNING[name]
    const p = zcFindPlayer(server, name)
    if (!p) return
    if (mult <= 0) {
      const line = ZC_LOSS_LINES[Math.floor(Math.random() * ZC_LOSS_LINES.length)]
      p.tell(Text.of('💨 ').gray().append(Text.of(line).gray()))
      server.runCommandSilent(`execute at ${name} run playsound minecraft:block.fire.extinguish master ${name} ~ ~ ~ 0.6 1.0`)
      return
    }
    const payout = bet * mult
    p.give(Item.of('minecraft:diamond', payout))
    server.runCommandSilent(`scoreboard players add ${name} ${ZC_WON_OBJECTIVE} ${payout}`)
    p.tell(
      Text.of('💎 x' + mult + '! ').aqua()
        .append(Text.of(payout + ' elmas kazandın.').green())
    )
    server.runCommandSilent(`execute at ${name} run playsound minecraft:entity.player.levelup master ${name} ~ ~ ~ 0.8 1.2`)
    if (mult >= 5) {
      server.tell(
        Text.of('🎰 ').gold()
          .append(Text.of(name).aqua())
          .append(Text.of(' çarkta ').gray())
          .append(Text.of('x' + mult).gold())
          .append(Text.of(' vurdu: ' + payout + ' elmas!').gray())
      )
      server.runCommandSilent('playsound minecraft:ui.toast.challenge_complete master @a ~ ~ ~ 0.5')
    }
  })

  // Plan kuruldu — bahsi peşin al. bet === eldeki tüm stack, o yüzden
  // shrink(bet) ile setCount(0) birebir eşdeğer.
  try {
    held.shrink(bet)
  } catch (_) {
    held.setCount(0)
  }
  zcEnsureObjectives(server)
  server.runCommandSilent(`scoreboard players add ${name} ${ZC_BET_OBJECTIVE} ${bet}`)

  ZC_SPINNING[name] = true
  player.tell(Text.of('🎰 ').gold().append(Text.of('Çark dönüyor… (' + bet + ' elmas)').yellow()))
  server.runCommandSilent(`execute at ${name} run playsound minecraft:block.note_block.hat master ${name} ~ ~ ~ 0.8 1.4`)
  return 1
}

ServerEvents.commandRegistry(event => {
  const { commands: Commands } = event

  const root = Commands.literal('zapeg-cark')
    .executes(ctx => zcRules(ctx.source))

  root.then(Commands.literal('oyna').executes(ctx => zcPlay(ctx.source)))
  event.register(root)
})
