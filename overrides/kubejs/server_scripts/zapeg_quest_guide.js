// ZapeG quest-guide bridge — SERVER-SIDE ONLY.
//
// EasyNPC dialogs call this permission-0 command after closing their menu. The
// player may also type it directly. Only fixed, reviewed quest IDs are exposed;
// the bridge cannot complete quests, grant rewards, or run arbitrary commands.

const ZQ_ROUTES = {
  new_player: '8129D7094B2D7000',
  all_paths: 'E3BD6E35F91448B4',
  technology: '5061F687C93750E0',
  magic: 'E81A3ADBB5F701B7',
  town: '69B229ED4B037D62',
  space: 'D5E7D3BA9C25ECCD',
  bosses: '821E9FAD62271BBF',
  ice_and_fire: '429426FD4B5915C7',
  petroleum: '9391D68FDF8F23F3',
  immersive_vehicles: '6E58166666B15922',
  eureka: '6E58166666B15922',
  nifty_ships: '6E58166666B15922',
  transport: '6E58166666B15922',
  alexs_caves: 'F797B1DC12120B19',
  aquamirae: '91C5554EDE74C6DD',
  mowzies_mobs: '7B0B261CD2C3568D',
  born_in_chaos: '77063A2CC2E2E0E9',
  combat: '7CF703870D771D84',
  citizens: 'A6BEC08AEDDF6619',
  incendium: '932933A8CBB67BBA'
}

function zqReply(source, message, failure) {
  if (failure) source.sendFailure(Text.of(message).red())
  else source.sendSuccess(() => Text.of(message).gray(), false)
}

function zqSafePlayerName(source) {
  try {
    const player = source.player
    const name = String(player.username)
    return /^[A-Za-z0-9_]{1,16}$/.test(name) ? name : null
  } catch (_) {
    return null
  }
}

function zqOpen(source, route) {
  const playerName = zqSafePlayerName(source)
  const questId = ZQ_ROUTES[route]
  if (!playerName || !questId) {
    zqReply(source, 'Bu rehber komutu yalnız oyundaki bir oyuncu tarafından kullanılabilir.', true)
    return 0
  }

  // FTB Quests 2001.4.14 requires a ServerPlayer command source. RCON/console
  // alone cannot open a client screen, so retain the real player with execute.
  const opened = source.server.runCommandSilent(
    `execute as ${playerName} run ftbquests open_book ${questId}`
  )
  if (opened <= 0) {
    zqReply(source, `Görev sayfası açılamadı: ${route}. Sunucu güncellemesini kontrol edin.`, true)
    return 0
  }
  return 1
}

ServerEvents.commandRegistry(event => {
  const { commands: Commands } = event
  const open = Commands.literal('open')

  Object.keys(ZQ_ROUTES).forEach(route => {
    open.then(
      Commands.literal(route)
        .executes(ctx => zqOpen(ctx.source, route))
    )
  })

  event.register(
    Commands.literal('zapeg-guide')
      .then(open)
  )
})
