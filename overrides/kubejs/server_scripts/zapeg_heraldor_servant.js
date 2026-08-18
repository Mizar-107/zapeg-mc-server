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
const ZH_DEATH_OBJECTIVE = 'zh_death'
const ZH_CONTROL_STORAGE = 'zapeg:heraldor'
const ZH_CONTROL_TOKEN_VERSION = 'zhctl1'
const ZH_CONTROL_TTL_SECONDS = 90
const ZH_LIFETIME_TICKS = 2400
const ZH_MAX_DISTANCE = 48
const ZH_NUMEN_CLASS = 'com.dwinovo.numen.entity.NumenPlayer'
const ZH_PLAYER_CLASS = Java.loadClass('net.minecraft.world.entity.player.Player')

let ZH_TICK_COUNTER = 0
let ZH_GATE_WAS_ACTIVE = false

function zhHasTag(entity, tag) {
  return Boolean(entity && entity.tags && entity.tags.contains(tag))
}

// Rhino bean naming on this build: getScoreboardName() -> .scoreboardName, but
// getUUID() stays .UUID (leading all-caps segment is never decapitalized), and
// no username getter exists at all. A missing getter reads back as undefined
// and String(undefined) === 'undefined' passes the name regex, so names and
// UUIDs must come from these exact accessors.
function zhEntityUuid(entity) {
  return String(entity.getUUID())
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
  const name = String(player.scoreboardName)
  return /^[A-Za-z0-9_]{1,16}$/.test(name) ? name : null
}

function zhDimensionId(level) {
  return String(level.dimension().location())
}

function zhDirectorSourceAllowed(source) {
  if (!source.hasPermission(2)) return false
  try {
    const player = source.player
    if (player && zhSafePlayerName(player)) {
      // `execute as <op>` changes the effective player but retains the command
      // block/function as source.source. Admit only a command typed by this
      // exact real ServerPlayer.
      const rawSource = source.source
      return Boolean(
        rawSource &&
        String(rawSource.getClass().getName()) ===
          'net.minecraft.server.level.ServerPlayer' &&
        String(rawSource.getUUID()) === zhEntityUuid(player)
      )
    }
  } catch (_) {
    // Console-like sources do not expose a player.
  }
  try {
    // This exact class check admits RCON but rejects command blocks. The local
    // server console is intentionally left to host-side admin/raw commands;
    // KubeJS cannot reliably distinguish it from every function context.
    return String(source.source.getClass().getName()) ===
      'net.minecraft.server.rcon.RconConsoleSource'
  } catch (_) {
    return false
  }
}

function zhDirectorOperatorName(source) {
  try {
    return zhSafePlayerName(source.player) || 'console'
  } catch (_) {
    return 'console'
  }
}

function zhControlNonce() {
  let milliseconds = Date.now().toString(16)
  let random = Math.floor(Math.random() * 0x100000000).toString(16)
  while (milliseconds.length < 12) milliseconds = '0' + milliseconds
  while (random.length < 8) random = '0' + random
  return milliseconds + random
}

function zhQueueDirectorRequest(source, action, argument, target) {
  const server = source.server
  zhEnsureObjectives(server)
  const allowedActions = [
    'status', 'pause', 'resume', 'phase_start', 'phase_advance',
    'scene_rehearse', 'scene_trigger', 'cancel'
  ]
  const allowedArguments = [
    '-', 'presence', 'servants', 'manifestation',
    'echo_01', 'threshold_01', 'motion_echo_01', 'light_fault_01',
    'peripheral_01', 'footsteps_01', 'sky_mark_01', 'false_passage_01',
    'chroma_break_01', 'near_miss_01', 'whisper_steps_01'
  ]
  if (allowedActions.indexOf(action) < 0 || allowedArguments.indexOf(argument) < 0) {
    zhReply(source, 'The Director request was not allowlisted.', true)
    return 0
  }
  const noArgumentActions = ['status', 'pause', 'resume', 'phase_advance', 'cancel']
  const phases = ['presence', 'servants', 'manifestation']
  const profiles = [
    'echo_01', 'threshold_01', 'motion_echo_01', 'light_fault_01',
    'peripheral_01', 'footsteps_01', 'sky_mark_01', 'false_passage_01',
    'chroma_break_01', 'near_miss_01', 'whisper_steps_01'
  ]
  const sceneAction = action === 'scene_rehearse' || action === 'scene_trigger'
  const validShape =
    (noArgumentActions.indexOf(action) >= 0 && argument === '-' && !target) ||
    (action === 'phase_start' && phases.indexOf(argument) >= 0 && !target) ||
    (sceneAction && profiles.indexOf(argument) >= 0 && Boolean(target))
  if (!validShape) {
    zhReply(source, 'The Director request arguments were not allowlisted.', true)
    return 0
  }

  const targetName = target ? zhSafePlayerName(target) : '-'
  if (!targetName) {
    zhReply(source, 'The target has a command-unsafe username.', true)
    return 0
  }
  const operatorName = zhDirectorOperatorName(source)
  const occupied = server.runCommandSilent(
    `execute if data storage ${ZH_CONTROL_STORAGE} control_request ` +
    `run scoreboard players get #world ${ZH_WORLD_OBJECTIVE}`
  ) > 0
  if (occupied) {
    zhReply(source, 'The Director already has one request waiting for acknowledgement.', true)
    return 0
  }

  const worldToken = Number(server.runCommandSilent(
    `scoreboard players get #world ${ZH_WORLD_OBJECTIVE}`
  ))
  if (worldToken !== Math.floor(worldToken) || worldToken < 1 || worldToken > 2000000000) {
    zhReply(source, 'The Director world token is unavailable.', true)
    return 0
  }

  const expiresAt = Math.floor(Date.now() / 1000) + ZH_CONTROL_TTL_SECONDS
  const token = [
    ZH_CONTROL_TOKEN_VERSION,
    String(worldToken),
    zhControlNonce(),
    String(expiresAt),
    action,
    argument,
    targetName,
    operatorName
  ].join(':')
  const changed = server.runCommandSilent(
    `data modify storage ${ZH_CONTROL_STORAGE} control_request ` +
    `set value ${JSON.stringify(token)}`
  )
  if (changed < 1) {
    zhReply(source, 'The Director request could not be queued.', true)
    return 0
  }
  zhReply(source, `Director request queued for ${action}; this is not an execution receipt.`, false)
  return 1
}

function zhDirectorApparitionBranch(Commands, Arguments, event, action) {
  const apparition = Commands.literal('apparition')
  const profiles = [
    ['echo', 'echo_01'],
    ['threshold', 'threshold_01'],
    ['motion-echo', 'motion_echo_01'],
    ['light-fault', 'light_fault_01'],
    ['peripheral', 'peripheral_01'],
    ['footsteps', 'footsteps_01'],
    ['sky-mark', 'sky_mark_01'],
    ['false-passage', 'false_passage_01'],
    ['chroma-break', 'chroma_break_01'],
    ['near-miss', 'near_miss_01'],
    ['whisper-steps', 'whisper_steps_01']
  ]
  profiles.forEach(profile => {
    apparition.then(Commands.literal(profile[0])
      .then(Commands.argument('target', Arguments.PLAYER.create(event))
        .executes(ctx => zhQueueDirectorRequest(
          ctx.source,
          action,
          profile[1],
          Arguments.PLAYER.getResult(ctx, 'target')
        ))
      )
    )
  })
  return apparition
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
  if (!server.scoreboard.getObjective(ZH_DEATH_OBJECTIVE)) {
    server.runCommandSilent(`scoreboard objectives add ${ZH_DEATH_OBJECTIVE} dummy`)
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
    const dimension = zhDimensionId(level)
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
          zhDimensionId(target.level) !== zhDimensionId(servant.level) ||
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
  servant.persistentData.zhTargetUuid = zhEntityUuid(target)
  servant.persistentData.zhTargetName = targetName
  servant.persistentData.zhInstanceId = instanceId
  servant.spawn()
  servant.target = target
  const dimension = zhDimensionId(target.level)
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
    `Awakened Heraldor'un Hizmetkârı for ${targetName} — ${mode}.`,
    false
  )
  return 1
}

function zhCleanupServants(source) {
  const server = source.server
  zhEnsureObjectives(server)
  let affected = 0
  zhForEachLevel(server, level => {
    const dimension = zhDimensionId(level)
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
      .then(Commands.literal('director')
        .requires(source => zhDirectorSourceAllowed(source))
        .then(Commands.literal('status')
          .executes(ctx => zhQueueDirectorRequest(ctx.source, 'status', '-', null))
        )
        .then(Commands.literal('pause')
          .executes(ctx => zhQueueDirectorRequest(ctx.source, 'pause', '-', null))
        )
        .then(Commands.literal('resume')
          .executes(ctx => zhQueueDirectorRequest(ctx.source, 'resume', '-', null))
        )
        .then(Commands.literal('phase')
          .then(Commands.literal('start')
            .then(Commands.literal('presence')
              .executes(ctx => zhQueueDirectorRequest(
                ctx.source, 'phase_start', 'presence', null
              ))
            )
            .then(Commands.literal('servants')
              .executes(ctx => zhQueueDirectorRequest(
                ctx.source, 'phase_start', 'servants', null
              ))
            )
            .then(Commands.literal('manifestation')
              .executes(ctx => zhQueueDirectorRequest(
                ctx.source, 'phase_start', 'manifestation', null
              ))
            )
          )
          .then(Commands.literal('advance')
            .executes(ctx => zhQueueDirectorRequest(
              ctx.source, 'phase_advance', '-', null
            ))
          )
        )
        .then(Commands.literal('event')
          .then(Commands.literal('rehearse')
            .then(zhDirectorApparitionBranch(
              Commands, Arguments, event, 'scene_rehearse'
            ))
          )
          .then(Commands.literal('trigger')
            .then(zhDirectorApparitionBranch(
              Commands, Arguments, event, 'scene_trigger'
            ))
          )
        )
        .then(Commands.literal('cancel')
          .executes(ctx => zhQueueDirectorRequest(ctx.source, 'cancel', '-', null))
        )
      )
  )
})

EntityEvents.hurt(event => {
  const attacker = event.source.entity
  if (!zhHasTag(attacker, ZH_SERVANT_TAG)) return

  const intended = String(attacker.persistentData.zhTargetUuid || '')
  if (!intended || zhEntityUuid(event.entity) !== intended) event.cancel()
})

EntityEvents.drops('minecraft:wither_skeleton', event => {
  if (zhHasTag(event.entity, ZH_SERVANT_TAG)) event.drops.clear()
})

// Grave echoes: the Director's log tail. Each real player death advances a
// per-player counter and remembers the last death site; the Director polls
// both over RCON and may answer an old site with a much later, quiet scene.
// Nothing is shown to anyone here — no message, no sound, no mockery.
EntityEvents.death('minecraft:player', event => {
  const player = event.entity
  if (zhIsNumenPlayer(player)) return
  const name = zhSafePlayerName(player)
  if (!name) return
  const server = player.server
  zhEnsureObjectives(server)
  server.runCommandSilent(`scoreboard players add ${name} ${ZH_DEATH_OBJECTIVE} 1`)
  const x = Math.floor(Number(player.x))
  const y = Math.floor(Number(player.y))
  const z = Math.floor(Number(player.z))
  const dimension = zhDimensionId(player.level)
  server.runCommandSilent(
    `data modify storage ${ZH_CONTROL_STORAGE} death_${name} set value ` +
    `{x:${x},y:${y},z:${z},dim:"${dimension}"}`
  )
  server.runCommandSilent(
    `execute store result storage ${ZH_CONTROL_STORAGE} death_${name}.game_time long 1 ` +
    `run time query gametime`
  )
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
  // source.player only sees the DIRECT entity, so projectile final blows
  // resolve to the arrow and never count. source.entity is the true attacker
  // (the shooter for projectiles); instanceof keeps mob/environment kills out.
  const attacker = event.source.entity
  const killer = attacker instanceof ZH_PLAYER_CLASS ? attacker : null
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
