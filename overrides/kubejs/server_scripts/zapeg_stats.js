// ZapeG istatistikleri — SERVER-SIDE ONLY (scoreboards sync to vanilla clients).
// Tracks: total deaths, deaths-to-dragons. Feeds the yearly "ZapeG Ödülleri".
// View in-game:  /scoreboard objectives setdisplay sidebar zapeg_deaths
// Hide:          /scoreboard objectives setdisplay sidebar
// Deploy: scripts/apply-overrides.sh ; reload: /kubejs reload server_scripts

ServerEvents.loaded(event => {
  const s = event.server
  // idempotent — "already exists" errors are harmless noise we pre-check away
  if (!s.scoreboard.getObjective('zapeg_deaths')) {
    s.runCommandSilent('scoreboard objectives add zapeg_deaths deathCount "§bZapeG §7— Ölümler"')
  }
  if (!s.scoreboard.getObjective('zapeg_ejder')) {
    s.runCommandSilent('scoreboard objectives add zapeg_ejder dummy "§cEjderhaya Yem"')
  }
})

EntityEvents.death('minecraft:player', event => {
  const victim = event.entity
  const killer = event.source?.actual
  if (!killer) return

  // Count only Ice and Fire's three actual dragon entity types. Other mobs in
  // the namespace (for example cyclopes or sirens) are not dragons.
  const dragonTypes = [
    'iceandfire:fire_dragon',
    'iceandfire:ice_dragon',
    'iceandfire:lightning_dragon'
  ]
  if (dragonTypes.indexOf(String(killer.type)) !== -1) {
    const server = victim.server
    server.runCommandSilent(`scoreboard players add ${victim.username} zapeg_ejder 1`)
    server.tell(Text.of('🐉 ').append(Text.of(victim.username).red()).append(' bir ejderhaya yem oldu.'))
  }
})
