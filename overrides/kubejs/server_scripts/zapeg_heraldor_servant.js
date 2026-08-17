// Heraldor servant rehearsal — SERVER-SIDE ONLY.
// Manual, OP-only baseline encounter. No custom client entity or assets.

const ZH_SERVANT_TAG = 'zh_hserv'
const ZH_REHEARSAL_TAG = 'zh_hserv_rehearsal'
const ZH_EXPIRED_TAG = 'zh_hserv_expired'
const ZH_COUNTED_TAG = 'zh_hserv_counted'
const ZH_INSTANCE_PREFIX = 'zh_hi_'
const ZH_EXPIRY_OBJECTIVE = 'zh_svc_exp'
const ZH_KILL_OBJECTIVE = 'zapeg_hsvc'
const ZH_WORLD_OBJECTIVE = 'zh_svc_world'
const ZH_INSTANCE_OBJECTIVE = 'zh_svc_id'
const ZH_LIFETIME_TICKS = 2400
const ZH_MAX_DISTANCE = 48
const ZH_NUMEN_CLASS = 'com.dwinovo.numen.entity.NumenPlayer'

let ZH_TICK_COUNTER = 0
let ZH_GATE_WAS_ACTIVE = false

function zhHasTag(entity, tag) {
  return Boolean(entity && entity.tags && entity.tags.contains(tag))
}

function zhIsNumenPlayer(player) {
  if (!player) return false
  try {
    if (String(player.getClass().getName()) === ZH_NUMEN_CLASS) return true
  } catch (_) {
    // The exact pinned Numen class check above is authoritative when available.
  }
  try {
    return player.ownerUuid != null
  } catch (_) {
    return false
  }
}

function zhSafePlayerName(player) {
  if (!player) return null
  const name = String(player.username)
  return /^[A-Za-z0-9_]{1,16}$/.test(name) ? name : null
}

function zhEnsureObjectives(server) {
  if (!server.scoreboard.getObjective(ZH_EXPIRY_OBJECTIVE)) {
    server.runCommandSilent(`scoreboard objectives add ${ZH_EXPIRY_OBJECTIVE} dummy`)
  }
  if (!server.scoreboard.getObjective(ZH_KILL_OBJECTIVE)) {
    server.runCommandSilent(`scoreboard objectives add ${ZH_KILL_OBJECTIVE} dummy`)
  }
  if (!server.scoreboard.getObjective(ZH_WORLD_OBJECTIVE)) {
    server.runCommandSilent(`scoreboard objectives add ${ZH_WORLD_OBJECTIVE} dummy`)
  }
  if (!server.scoreboard.getObjective(ZH_INSTANCE_OBJECTIVE)) {
    server.runCommandSilent(`scoreboard objectives add ${ZH_INSTANCE_OBJECTIVE} dummy`)
  }
  server.runCommandSilent(`scoreboard players add #now ${ZH_EXPIRY_OBJECTIVE} 0`)
  server.runCommandSilent(`scoreboard players add #active_until ${ZH_EXPIRY_OBJECTIVE} 0`)
  server.runCommandSilent(`scoreboard players add #total ${ZH_KILL_OBJECTIVE} 0`)
  server.runCommandSilent(`scoreboard players add #world ${ZH_WORLD_OBJECTIVE} 0`)
  server.runCommandSilent(`scoreboard players add #active_id ${ZH_INSTANCE_OBJECTIVE} 0`)
  const worldToken = Math.floor(Math.random() * 2000000000) + 1
  server.runCommandSilent(
    `execute if score #world ${ZH_WORLD_OBJECTIVE} matches 0 ` +
    `run scoreboard players set #world ${ZH_WORLD_OBJECTIVE} ${worldToken}`
  )
}

function zhRefreshGameTime(server) {
  server.runCommandSilent(
    `execute store result score #now ${ZH_EXPIRY_OBJECTIVE} run time query gametime`
  )
}

function zhForEachLevel(server, callback) {
  const iterator = server.getAllLevels().iterator()
  while (iterator.hasNext()) callback(iterator.next())
}

function zhExpireLoadedServants(server) {
  zhRefreshGameTime(server)
  zhForEachLevel(server, level => {
    const dimension = String(level.dimension)
    server.runCommandSilent(
      `execute in ${dimension} as @e[type=minecraft:wither_skeleton,tag=${ZH_SERVANT_TAG}] ` +
      `unless score @s ${ZH_EXPIRY_OBJECTIVE} matches 1.. run tag @s add ${ZH_EXPIRED_TAG}`
    )
    server.runCommandSilent(
      `execute in ${dimension} as @e[type=minecraft:wither_skeleton,tag=${ZH_SERVANT_TAG}] ` +
      `if score @s ${ZH_EXPIRY_OBJECTIVE} <= #now ${ZH_EXPIRY_OBJECTIVE} ` +
      `run tag @s add ${ZH_EXPIRED_TAG}`
    )
    server.runCommandSilent(
      `execute in ${dimension} run kill ` +
      `@e[type=minecraft:wither_skeleton,tag=${ZH_SERVANT_TAG},tag=${ZH_EXPIRED_TAG}]`
    )
  })
  server.runCommandSilent(
    `execute if score #active_until ${ZH_EXPIRY_OBJECTIVE} <= #now ${ZH_EXPIRY_OBJECTIVE} ` +
    `run scoreboard players set #active_until ${ZH_EXPIRY_OBJECTIVE} 0`
  )
  server.runCommandSilent(
    `execute if score #active_until ${ZH_EXPIRY_OBJECTIVE} matches 0 ` +
    `run scoreboard players set #active_id ${ZH_INSTANCE_OBJECTIVE} 0`
  )
}

function zhActiveGateIsOpen(server) {
  zhRefreshGameTime(server)
  return server.runCommandSilent(
    `execute if score #active_until ${ZH_EXPIRY_OBJECTIVE} > #now ${ZH_EXPIRY_OBJECTIVE} ` +
    `run scoreboard players get #active_until ${ZH_EXPIRY_OBJECTIVE}`
  ) > 0
}

function zhSafeSpawn(level, target) {
  const baseX = Math.floor(Number(target.x))
  const baseY = Math.floor(Number(target.y))
  const baseZ = Math.floor(Number(target.z))
  const ring = [
    [8, 0], [6, 6], [0, 8], [-6, 6], [-8, 0], [-6, -6], [0, -8], [6, -6],
    [12, 0], [8, 8], [0, 12], [-8, 8], [-12, 0], [-8, -8], [0, -12], [8, -8]
  ]
  const vertical = [0, 1, -1, 2, -2, 3, -3, 4, -4]
  const servant = level.createEntity('minecraft:wither_skeleton')
  if (!servant) return null
  const start = Math.floor(Math.random() * ring.length)

  for (let index = 0; index < ring.length; index++) {
    const offset = ring[(start + index) % ring.length]
    for (const dy of vertical) {
      const x = baseX + offset[0]
      const y = baseY + dy
      const z = baseZ + offset[1]
      const floor = level.getBlock(x, y - 1, z)
      const feet = level.getBlock(x, y, z)
      const head = level.getBlock(x, y + 1, z)
      const top = level.getBlock(x, y + 2, z)

      if (!floor.blockState.isCollisionShapeFullBlock(level, floor.pos)) continue
      if (floor.hasTag('minecraft:leaves')) continue
      if (!feet.blockState.isAir() || !head.blockState.isAir() || !top.blockState.isAir()) continue

      servant.setPosition(x + 0.5, y, z + 0.5)
      if (level.noCollision(servant)) return servant
    }
  }
  return null
}

function zhExpireServant(servant) {
  try {
    servant.tags.add(ZH_EXPIRED_TAG)
    servant.kill()
  } catch (_) {
    // It may already have died or unloaded between checks.
  }
}

function zhMaintainTargets(server) {
  server.getAllLevels().forEach(level => {
    level.entities.forEach(servant => {
      if (!zhHasTag(servant, ZH_SERVANT_TAG)) return
      try {
        const targetName = String(servant.persistentData.zhTargetName || '')
        const target = targetName ? server.getPlayer(targetName) : null
        const invalid = !target || !target.isAlive() || zhIsNumenPlayer(target) ||
          String(target.level.dimension) !== String(servant.level.dimension) ||
          Number(servant.distanceTo(target)) > ZH_MAX_DISTANCE
        if (invalid) zhExpireServant(servant)
        else servant.target = target
      } catch (_) {
        zhExpireServant(servant)
      }
    })
  })
}

function zhReply(source, message, failure) {
  if (failure) source.sendFailure(Text.of(message).red())
  else source.sendSuccess(() => Text.of(message).gray(), false)
}

function zhSpawnServant(source, target, rehearsal) {
  const server = source.server
  zhEnsureObjectives(server)

  if (zhIsNumenPlayer(target)) {
    zhReply(source, 'A Citizen body cannot be a Heraldor rehearsal target.', true)
    return 0
  }
  const targetName = zhSafePlayerName(target)
  if (!targetName) {
    zhReply(source, 'The target has a command-unsafe offline username.', true)
    return 0
  }
  if (zhActiveGateIsOpen(server)) {
    zhReply(source, 'A Heraldor servant rehearsal is already active.', true)
    return 0
  }

  const servant = zhSafeSpawn(target.level, target)
  if (!servant) {
    zhReply(source, 'No safe 3-block-high spawn point was found within 12 blocks.', true)
    return 0
  }

  const instanceId = Math.floor(Math.random() * 2000000000) + 1
  const instanceTag = ZH_INSTANCE_PREFIX + Date.now().toString(36) + '_' +
    instanceId.toString(36)
  const tags = [ZH_SERVANT_TAG, instanceTag]
  if (rehearsal) tags.push(ZH_REHEARSAL_TAG)
  servant.mergeNbt({
    Tags: tags,
    CustomName: JSON.stringify({
      text: "Heraldor'un Hizmetkârı",
      color: 'dark_red',
      italic: false
    }),
    CustomNameVisible: 0,
    PersistenceRequired: 1,
    CanPickUpLoot: 0,
    DeathLootTable: 'minecraft:empty',
    Health: 40,
    Attributes: [
      { Name: 'minecraft:generic.max_health', Base: 40 },
      { Name: 'minecraft:generic.attack_damage', Base: 6 },
      { Name: 'minecraft:generic.movement_speed', Base: 0.27 },
      { Name: 'minecraft:generic.follow_range', Base: 24 },
      { Name: 'minecraft:generic.knockback_resistance', Base: 0.15 }
    ]
  })
  servant.mainHandItem = Item.of('minecraft:stone_sword')
  servant.persistentData.zhTargetUuid = String(target.uuid)
  servant.persistentData.zhTargetName = targetName
  servant.persistentData.zhInstanceId = instanceId
  servant.spawn()
  servant.target = target
  const dimension = String(target.level.dimension)
  const selector =
    `@e[type=minecraft:wither_skeleton,tag=${ZH_SERVANT_TAG},tag=${instanceTag},limit=1]`
  server.runCommandSilent(
    `execute in ${dimension} as ${selector} store result score @s ${ZH_EXPIRY_OBJECTIVE} ` +
    `run time query gametime`
  )
  server.runCommandSilent(
    `execute in ${dimension} as ${selector} run scoreboard players add ` +
    `@s ${ZH_EXPIRY_OBJECTIVE} ${ZH_LIFETIME_TICKS}`
  )
  server.runCommandSilent(
    `execute in ${dimension} as ${selector} run scoreboard players operation ` +
    `#active_until ${ZH_EXPIRY_OBJECTIVE} = @s ${ZH_EXPIRY_OBJECTIVE}`
  )
  server.runCommandSilent(
    `scoreboard players set #active_id ${ZH_INSTANCE_OBJECTIVE} ${instanceId}`
  )
  const initialized = server.runCommandSilent(
    `execute in ${dimension} as ${selector} ` +
    `if score @s ${ZH_EXPIRY_OBJECTIVE} = #active_until ${ZH_EXPIRY_OBJECTIVE} ` +
    `run scoreboard players get @s ${ZH_EXPIRY_OBJECTIVE}`
  )
  if (initialized <= 0) {
    zhExpireServant(servant)
    zhReply(source, 'Servant expiry state could not be initialized; spawn was cancelled.', true)
    return 0
  }
  server.runCommandSilent(
    `execute at ${targetName} run playsound ` +
    `minecraft:entity.wither_skeleton.ambient hostile ${targetName} ~ ~ ~ 0.8 0.65`
  )
  const mode = rehearsal ? 'rehearsal (no story progress)' : 'LIVE'
  zhReply(
    source,
    `Awakened Heraldor'un Hizmetkârı for ${String(target.username)} — ${mode}.`,
    false
  )
  return 1
}

function zhCleanupServants(source) {
  const server = source.server
  zhEnsureObjectives(server)
  let affected = 0
  zhForEachLevel(server, level => {
    const dimension = String(level.dimension)
    server.runCommandSilent(
      `execute in ${dimension} run tag ` +
      `@e[type=minecraft:wither_skeleton,tag=${ZH_SERVANT_TAG}] add ${ZH_EXPIRED_TAG}`
    )
    affected += server.runCommandSilent(
      `execute in ${dimension} run kill ` +
      `@e[type=minecraft:wither_skeleton,tag=${ZH_SERVANT_TAG}]`
    )
  })
  server.runCommandSilent(`scoreboard players set #active_until ${ZH_EXPIRY_OBJECTIVE} 0`)
  server.runCommandSilent(`scoreboard players set #active_id ${ZH_INSTANCE_OBJECTIVE} 0`)
  zhReply(source, `Cleaned up ${affected} loaded Heraldor servant(s).`, false)
  return 1
}

ServerEvents.loaded(event => {
  zhEnsureObjectives(event.server)
  event.server.runCommandSilent('data modify storage zapeg:heraldor schema set value 1')
  zhExpireLoadedServants(event.server)
})

ServerEvents.tick(event => {
  ZH_TICK_COUNTER++
  if (ZH_TICK_COUNTER % 20 !== 0) return
  if (zhActiveGateIsOpen(event.server)) {
    // The heavier entity scan runs once a second only during a two-minute encounter.
    ZH_GATE_WAS_ACTIVE = true
    zhExpireLoadedServants(event.server)
    zhMaintainTargets(event.server)
  } else if (ZH_GATE_WAS_ACTIVE || ZH_TICK_COUNTER % 100 === 0) {
    // Idle safety sweep catches an expired servant when an old chunk reloads.
    ZH_GATE_WAS_ACTIVE = false
    zhExpireLoadedServants(event.server)
  }
})

ServerEvents.commandRegistry(event => {
  const { commands: Commands, arguments: Arguments } = event
  event.register(
    Commands.literal('zapeg-lore')
      .requires(source => source.hasPermission(2))
      .then(Commands.literal('servant')
        .then(Commands.literal('rehearse')
          .then(Commands.argument('target', Arguments.PLAYER.create(event))
            .executes(ctx => zhSpawnServant(
              ctx.source,
              Arguments.PLAYER.getResult(ctx, 'target'),
              true
            ))
          )
        )
        .then(Commands.literal('awaken')
          .then(Commands.argument('target', Arguments.PLAYER.create(event))
            .executes(ctx => zhSpawnServant(
              ctx.source,
              Arguments.PLAYER.getResult(ctx, 'target'),
              false
            ))
          )
        )
        .then(Commands.literal('cleanup')
          .executes(ctx => zhCleanupServants(ctx.source))
        )
      )
  )
})

EntityEvents.hurt(event => {
  const attacker = event.source.entity || event.source.actual
  if (!zhHasTag(attacker, ZH_SERVANT_TAG)) return

  const intended = String(attacker.persistentData.zhTargetUuid || '')
  if (!intended || String(event.entity.uuid) !== intended) event.cancel()
})

EntityEvents.drops('minecraft:wither_skeleton', event => {
  if (zhHasTag(event.entity, ZH_SERVANT_TAG)) event.drops.clear()
})

EntityEvents.death('minecraft:wither_skeleton', event => {
  const servant = event.entity
  if (!zhHasTag(servant, ZH_SERVANT_TAG)) return

  const instanceId = Number(servant.persistentData.zhInstanceId || 0)
  if (instanceId > 0) {
    const server = servant.server
    server.runCommandSilent(
      `execute if score #active_id ${ZH_INSTANCE_OBJECTIVE} matches ${instanceId} ` +
      `run scoreboard players set #active_until ${ZH_EXPIRY_OBJECTIVE} 0`
    )
    server.runCommandSilent(
      `execute if score #active_id ${ZH_INSTANCE_OBJECTIVE} matches ${instanceId} ` +
      `run scoreboard players set #active_id ${ZH_INSTANCE_OBJECTIVE} 0`
    )
  }
  if (
    zhHasTag(servant, ZH_EXPIRED_TAG) ||
    zhHasTag(servant, ZH_COUNTED_TAG) ||
    zhHasTag(servant, ZH_REHEARSAL_TAG)
  ) return
  const killer = event.source.player
  if (!killer || zhIsNumenPlayer(killer)) return
  const name = zhSafePlayerName(killer)
  if (!name) return

  servant.tags.add(ZH_COUNTED_TAG)
  const server = killer.server
  server.runCommandSilent(`scoreboard players add ${name} ${ZH_KILL_OBJECTIVE} 1`)
  server.runCommandSilent(`scoreboard players add #total ${ZH_KILL_OBJECTIVE} 1`)
  server.runCommandSilent(
    `data modify storage zapeg:heraldor last_minion_kill.player set value ${JSON.stringify(name)}`
  )
  server.runCommandSilent(
    `execute store result storage zapeg:heraldor last_minion_kill.sequence int 1 ` +
    `run scoreboard players get #total ${ZH_KILL_OBJECTIVE}`
  )
  server.runCommandSilent(
    `execute store result storage zapeg:heraldor last_minion_kill.world_token int 1 ` +
    `run scoreboard players get #world ${ZH_WORLD_OBJECTIVE}`
  )
  server.runCommandSilent(
    'execute store result storage zapeg:heraldor last_minion_kill.game_time long 1 ' +
    'run time query gametime'
  )
})
