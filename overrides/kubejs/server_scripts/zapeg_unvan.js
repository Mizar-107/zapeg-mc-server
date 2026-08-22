// ZapeG unvan sistemi — SERVER-SIDE ONLY.
// Tören advancement'ı verildiğinde (bkz. datapacks/zapeg-lore) oyuncuya
// otomatik renkli tab/sohbet öneki takar + sunucu geneli tören duyurusu yapar.
// Tören akışı tek komuta iner:
//   /advancement grant <nick> only zapeg:kral_unvani
// Manuel düzeltme/geri alma: /zapeg-unvan (OP).
// "dokuzuncu" advancement'ı BİLEREK listede yok — gizli kalır, önek takmaz.

const ZU_TITLES = {
  kral_unvani: {
    team: 'zapeg_kral',
    prefix: '[Kral] ',
    color: 'gold',
    announce: '👑 Taç giydi',
    detail: 'ZapeG artık bir krallık.'
  },
  vali: {
    team: 'zapeg_vali',
    prefix: '[Vali] ',
    color: 'dark_green',
    announce: '🏛 Vali atandı',
    detail: 'Köy nihayet resmiyet kazandı.'
  },
  garaj_krali: {
    team: 'zapeg_garaj',
    prefix: '[Garaj Kralı] ',
    color: 'gray',
    announce: '🔧 Garaj Kralı ilan edildi',
    detail: 'Motor sesi duyan ona baksın.'
  },
  gokyuzu_bekcisi: {
    team: 'zapeg_gokyuzu',
    prefix: '[Gökyüzü Bekçisi] ',
    color: 'aqua',
    announce: '🪽 Gökyüzü Bekçisi göreve başladı',
    detail: 'Yukarısı artık emin ellerde.'
  },
  itfaiye_sefi: {
    team: 'zapeg_itfaiye',
    prefix: '[İtfaiye Şefi] ',
    color: 'red',
    announce: '🚒 İtfaiye Şefi yemin etti',
    detail: 'Yangını en iyi bilen söndürür.'
  }
}

function zuTitleIds() {
  return Object.keys(ZU_TITLES)
}

function zuReply(source, text, failure) {
  if (failure) source.sendFailure(text)
  else source.sendSuccess(() => text, false)
}

function zuEnsureTeam(server, id) {
  const t = ZU_TITLES[id]
  // team add zaten varsa sessizce başarısız olur — idempotent.
  server.runCommandSilent(`team add ${t.team}`)
  server.runCommandSilent(
    `team modify ${t.team} prefix ${JSON.stringify({ text: t.prefix, color: t.color })}`
  )
  server.runCommandSilent(`team modify ${t.team} color ${t.color}`)
  server.runCommandSilent(`team modify ${t.team} friendlyFire true`)
}

function zuApply(server, name, id, announce) {
  const t = ZU_TITLES[id]
  if (!t) return 0
  zuEnsureTeam(server, id)
  // Vanilla kural: oyuncu tek takımda olabilir → yeni unvan eskisini değiştirir.
  const joined = server.runCommandSilent(`team join ${t.team} ${name}`)
  if (!joined) return 0
  if (announce) {
    server.runCommandSilent(
      `title @a subtitle ${JSON.stringify({ text: name, color: t.color, bold: true })}`
    )
    server.runCommandSilent(
      `title @a title ${JSON.stringify({ text: t.announce, color: t.color })}`
    )
    server.runCommandSilent('playsound minecraft:ui.toast.challenge_complete master @a ~ ~ ~ 0.7')
    server.tell(
      Text.of('★ ').gold()
        .append(Text.of(name).aqua())
        .append(Text.of(' — ' + t.prefix.trim() + ' · ' + t.detail).gray())
    )
  }
  return 1
}

function zuRemove(server, name) {
  return server.runCommandSilent(`team leave ${name}`) ? 1 : 0
}

// --- otomatik: tören advancement'ı verilince unvanı tak --------------------

// Savunmacı kayıt: bu binding canlı KubeJS yapısında yoksa TÜM dosya
// ölmesin — komut yine kayıt olsun, otomasyon kapansın ve log söylesin.
if (typeof PlayerEvents.advancement === 'function') {
  PlayerEvents.advancement(event => {
    let id = null
    try {
      id = String(event.advancement.id)
    } catch (_) {
      return
    }
    if (!id || id.indexOf('zapeg:') !== 0) return
    const key = id.substring('zapeg:'.length)
    if (!ZU_TITLES[key]) return
    const player = event.player
    if (!player) return
    const name = String(player.scoreboardName)
    if (!/^[A-Za-z0-9_]{1,16}$/.test(name)) return
    zuApply(player.server, name, key, true)
  })
} else {
  console.log('[zapeg] zapeg_unvan: PlayerEvents.advancement bu yapıda yok — otomatik unvan KAPALI; törenle birlikte /zapeg-unvan ver <unvan> <oyuncu> çalıştır')
}

// --- manuel OP komutu -------------------------------------------------------

ServerEvents.commandRegistry(event => {
  const { commands: Commands, arguments: Arguments } = event

  console.log('[zapeg] /zapeg-unvan registering')
  const root = Commands.literal('zapeg-unvan')
    .requires(source => source.hasPermission(2))
    .executes(ctx => {
      zuReply(ctx.source, Text.of('/zapeg-unvan ver <unvan> <oyuncu> — sessiz takar (tören için /advancement grant kullan)').yellow(), false)
      zuReply(ctx.source, Text.of('/zapeg-unvan kaldir <oyuncu>').yellow(), false)
      zuReply(ctx.source, Text.of('/zapeg-unvan liste').yellow(), false)
      return 1
    })

  const liste = Commands.literal('liste').executes(ctx => {
    const ids = zuTitleIds()
    for (let i = 0; i < ids.length; i++) {
      var t = ZU_TITLES[ids[i]]
      zuReply(ctx.source, Text.of('• ' + ids[i]).aqua()
        .append(Text.of(' — ' + t.prefix.trim() + ' (advancement: zapeg:' + ids[i] + ')').gray()), false)
    }
    return 1
  })

  // Kanıtlanmış desen: önce unvan literal'i, sonra oyuncu argümanı; döngü
  // değişkeni callback'e kapatılmaz — parametre yakalar (bkz. kitap notu).
  function zuAttachTitle(parent, id) {
    parent.then(Commands.literal(id)
      .then(Commands.argument('target', Arguments.PLAYER.create(event))
        .executes(ctx => {
          const target = Arguments.PLAYER.getResult(ctx, 'target')
          const name = String(target.scoreboardName)
          const done = zuApply(target.server, name, id, false)
          if (done) zuReply(ctx.source, Text.of('Unvan takıldı: ' + name + ' → ' + ZU_TITLES[id].prefix.trim()).gray(), false)
          else zuReply(ctx.source, Text.of('Unvan takılamadı.').red(), true)
          return done
        })
      )
    )
  }
  const ver = Commands.literal('ver')
  const ids = zuTitleIds()
  for (let i = 0; i < ids.length; i++) {
    zuAttachTitle(ver, ids[i])
  }

  const kaldir = Commands.literal('kaldir')
    .then(Commands.argument('target', Arguments.PLAYER.create(event))
      .executes(ctx => {
        const target = Arguments.PLAYER.getResult(ctx, 'target')
        const name = String(target.scoreboardName)
        const done = zuRemove(target.server, name)
        zuReply(ctx.source, Text.of(done ? 'Unvan kaldırıldı: ' + name : name + ' zaten unvansız.').gray(), false)
        return 1
      })
    )

  root.then(liste)
  root.then(ver)
  root.then(kaldir)
  event.register(root)
})

console.log('[zapeg] zapeg_unvan.js loaded (r3: const-in-loop fix + attach-helper — yerel Rhino testinde REG/RUN doğrulandı)')
