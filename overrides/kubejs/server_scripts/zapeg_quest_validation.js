// ZapeG quest authority — SERVER-SIDE ONLY.
// FTB Quests is the UI/reward surface; custom advancement criteria are the
// non-clickable bridge. Only these server checks (or an explicit OP review)
// can grant a criterion in zapeg:verified.
// Deploy: scripts/apply-overrides.sh ; full restart required for data/advancements.

const ZAPEG_QUEST_PLAYERS = {
  emir: 'kralxlarge',
  emin: 'eminomi12',
  salih: 'SalihKarahan',
  recep: 'Mizar__107',
  mert: 'MertOnal',
  enes: 'Thekingim'
}

const ZAPEG_DRAGON_TYPES = [
  'iceandfire:fire_dragon',
  'iceandfire:ice_dragon',
  'iceandfire:lightning_dragon'
]

// FTB Teams shares quest state, so these rewards bypass FTB claims and go once,
// directly to the exact login that owns the personal quest.
const ZAPEG_PERSONAL_REWARDS = {
  merton_house: {
    owner: 'MertOnal',
    item: 'minecraft:brick',
    name: "MertOnal'ın Tapusu",
    lore: 'Kendi elleriyle kurduğu evin resmî hatırası'
  },
  emin_fountain: {
    owner: 'eminomi12',
    item: 'minecraft:heart_of_the_sea',
    name: 'Kasaba Fıskiyesinin Kalbi',
    lore: 'Emin Taha tarafından kasabaya kazandırıldı'
  },
  emir_dragon_owner: {
    owner: 'kralxlarge',
    item: 'iceandfire:dragon_horn',
    name: "Emir'in Ejderha Boynuzu",
    lore: "Emir'in ilk evcil ejderhasının hatırası"
  },
  salih_dragon_owner: {
    owner: 'SalihKarahan',
    item: 'iceandfire:dragon_flute',
    name: "Salih'in Ejderha Düdüğü",
    lore: "Salih'in ilk evcil ejderhasının hatırası"
  }
}

const ZAPEG_REWARD_ITEM_ERRORS = {}
const ZAPEG_REWARD_FULL_NOTICE = {}
let ZAPEG_DRAGON_API_ERROR = false

const ZAPEG_CATACLYSM_BOSSES = [
  'cataclysm:ender_guardian',
  'cataclysm:netherite_monstrosity',
  'cataclysm:ignis',
  'cataclysm:the_harbinger',
  'cataclysm:the_leviathan',
  'cataclysm:ancient_remnant',
  'cataclysm:maledictus',
  'cataclysm:scylla'
]

const ZAPEG_PENDING_FIRES = {}
const ZAPEG_FIRE_ATTEMPTS = {}
const ZAPEG_VERIFIED_CACHE = {}
const ZAPEG_VERIFIED_PROBES = {}
const ZAPEG_REWARD_RECHECK_TICKS = 100

function zapegVerifiedCacheKey(player) {
  return `uuid:${String(player.uuid)}`
}

function zapegVerifiedCache(player) {
  const key = zapegVerifiedCacheKey(player)
  if (!ZAPEG_VERIFIED_CACHE[key]) ZAPEG_VERIFIED_CACHE[key] = {}
  return ZAPEG_VERIFIED_CACHE[key]
}

function zapegVerifiedProbes(player) {
  const key = zapegVerifiedCacheKey(player)
  if (!ZAPEG_VERIFIED_PROBES[key]) ZAPEG_VERIFIED_PROBES[key] = {}
  return ZAPEG_VERIFIED_PROBES[key]
}

function zapegClearVerifiedCache(player) {
  const key = zapegVerifiedCacheKey(player)
  delete ZAPEG_VERIFIED_CACHE[key]
  delete ZAPEG_VERIFIED_PROBES[key]
}

function zapegIsVerifiedCached(player, criterion) {
  return Boolean(zapegVerifiedCache(player)[criterion])
}

function zapegRememberVerified(player, criterion) {
  zapegVerifiedCache(player)[criterion] = true
}

function zapegProbeVerifiedOnce(player, criterion) {
  const probes = zapegVerifiedProbes(player)
  if (probes[criterion]) return zapegIsVerifiedCached(player, criterion)
  probes[criterion] = true
  return zapegHasVerified(player, criterion)
}

function zapegGrantVerified(player, criterion, title) {
  if (zapegIsVerifiedCached(player, criterion)) return true

  const name = String(player.username)
  const changed = player.server.runCommandSilent(
    `execute as ${name} if entity @s[advancements={zapeg:verified={${criterion}=false}}] run advancement grant @s only zapeg:verified ${criterion}`
  )

  // A zero result can mean "already complete" or "not grantable". Cache only
  // confirmed positives so a missing/temporarily unavailable criterion retries.
  if (changed <= 0) return zapegHasVerified(player, criterion)

  zapegRememberVerified(player, criterion)
  player.server.tell(
    Text.of('✓ ').green()
      .append(Text.of(name).aqua())
      .append(Text.of(` doğrulandı: ${title}`).gold())
  )

  if (ZAPEG_PERSONAL_REWARDS[criterion]) zapegGivePersonalRewards(player, true)
  return true
}

function zapegReconcileVanillaAdvancement(player, source, criterion) {
  if (zapegIsVerifiedCached(player, criterion)) return

  const name = String(player.username)
  const changed = player.server.runCommandSilent(
    `execute as ${name} if entity @s[advancements={${source}=true,zapeg:verified={${criterion}=false}}] run advancement grant @s only zapeg:verified ${criterion}`
  )
  if (changed > 0) zapegRememberVerified(player, criterion)
  else zapegHasVerified(player, criterion)
}

function zapegScore(server, objective, name, value) {
  server.runCommandSilent(`scoreboard players set ${name} ${objective} ${value}`)
}

function zapegHasVerified(player, criterion) {
  if (zapegIsVerifiedCached(player, criterion)) return true

  const name = String(player.username)
  const verified = player.server.runCommandSilent(
    `execute as ${name} if entity @s[advancements={zapeg:verified={${criterion}=true}}] run data get entity @s UUID`
  ) > 0
  if (verified) zapegRememberVerified(player, criterion)
  return verified
}

function zapegGivePersonalRewards(player, forceCriterionCheck) {
  const name = String(player.username)

  for (const criterion in ZAPEG_PERSONAL_REWARDS) {
    const reward = ZAPEG_PERSONAL_REWARDS[criterion]
    if (name !== reward.owner) continue

    const stage = `zapeg_reward_${criterion}`
    const marker = `zapegReward_${criterion}_v1`
    if (Boolean(player.persistentData[marker]) || player.stages.has(stage)) continue

    const cached = zapegIsVerifiedCached(player, criterion)
    const recheckDue = Number(player.age) % ZAPEG_REWARD_RECHECK_TICKS === 0
    if (!cached && !forceCriterionCheck && !recheckDue) continue
    if (!zapegHasVerified(player, criterion)) continue

    if (!Item.exists(reward.item)) {
      if (!ZAPEG_REWARD_ITEM_ERRORS[criterion]) {
        console.error(`[ZapeG] Kişisel ödül bulunamadı: ${reward.item} (${criterion})`)
        ZAPEG_REWARD_ITEM_ERRORS[criterion] = true
      }
      continue
    }

    const item = Item.of(reward.item, {
      zapeg: {
        personal: true,
        owner: reward.owner,
        quest: criterion,
        version: '1'
      }
    })
      .withName(Text.of(reward.name).gold().italic(false))
      .withLore([
        Text.of(reward.lore).gray().italic(false),
        Text.of(`Sahibi: ${reward.owner}`).gray().italic(false)
      ])

    if (!player.inventory.insertItem(item, true).isEmpty()) {
      const notice = `${name}:${criterion}`
      if (!ZAPEG_REWARD_FULL_NOTICE[notice]) {
        player.tell(Text.of(`Kişisel hatıran bekliyor (${reward.name}); envanterinde bir yer aç.`).gold())
        ZAPEG_REWARD_FULL_NOTICE[notice] = true
      }
      continue
    }

    const remaining = player.inventory.insertItem(item, false)
    if (!remaining.isEmpty()) {
      console.error(`[ZapeG] ${reward.name} ${name} envanterine eklenemedi; teslimat yeniden denenecek.`)
      continue
    }

    player.persistentData[marker] = true
    player.stages.add(stage)
    delete ZAPEG_REWARD_FULL_NOTICE[`${name}:${criterion}`]
    player.tell(Text.of(`Kişisel hatıran teslim edildi: ${reward.name}`).gold())
  }
}

function zapegOwnsMountedDragon(player) {
  const dragon = player.vehicle
  if (!dragon || ZAPEG_DRAGON_TYPES.indexOf(String(dragon.type)) === -1) return false
  try {
    return Boolean(dragon.isTame()) && Boolean(dragon.isOwnedBy(player))
  } catch (error) {
    if (!ZAPEG_DRAGON_API_ERROR) {
      console.error(`[ZapeG] Ice and Fire owner API kontrolü çalışmadı; ejderha smoke testi gerekli: ${error}`)
      ZAPEG_DRAGON_API_ERROR = true
    }
    return false
  }
}

ServerEvents.loaded(event => {
  const server = event.server
  if (!server.scoreboard.getObjective('zapeg_tames')) {
    server.runCommandSilent('scoreboard objectives add zapeg_tames dummy "§aZapeG §7— Evcilleştirilen"')
  }
  if (!server.scoreboard.getObjective('zapeg_chest_s')) {
    server.runCommandSilent('scoreboard objectives add zapeg_chest_s dummy "§6ZapeG §7— Sandık Nöbeti (sn)"')
  }
})

PlayerEvents.loggedIn(event => {
  const player = event.player
  const name = String(player.username)
  zapegClearVerifiedCache(player)

  zapegGrantVerified(player, 'welcome', 'ZapeG’e Hoş Geldin')

  if (name === ZAPEG_QUEST_PLAYERS.emir) {
    zapegReconcileVanillaAdvancement(player, 'minecraft:end/kill_dragon', 'emir_dragon')
    const diamondsDone = zapegProbeVerifiedOnce(player, 'emir_diamonds')
    if (!diamondsDone && Number(player.inventory.count('minecraft:diamond')) >= 64) {
      zapegGrantVerified(player, 'emir_diamonds', 'Emir — Mavi Servet')
    }
  }

  if (name === ZAPEG_QUEST_PLAYERS.mert) {
    const minecartDone = zapegProbeVerifiedOnce(player, 'mert_minecart')
    if (!minecartDone && Number(player.stats.get('minecraft:minecart_one_cm')) >= 500000) {
      zapegGrantVerified(player, 'mert_minecart', 'Mert — Raylarda 5 km')
    }
  }

  if (name === ZAPEG_QUEST_PLAYERS.enes) {
    zapegReconcileVanillaAdvancement(player, 'minecraft:adventure/ol_betsy', 'enes_crossbow')
  }

  if (name === ZAPEG_QUEST_PLAYERS.emin) {
    zapegScore(player.server, 'zapeg_tames', name, Number(player.persistentData.zapegTames || 0))
  }
  if (name === ZAPEG_QUEST_PLAYERS.recep) {
    let chestDone = zapegProbeVerifiedOnce(player, 'recep_chest_watch')
    const storedSeconds = Number(player.persistentData.zapegChestSeconds || 0)
    if (!chestDone && storedSeconds >= 120) {
      chestDone = zapegGrantVerified(player, 'recep_chest_watch', 'Recep — 120 saniyelik Sandık Nöbeti')
    }
    const displaySeconds = chestDone ? 120 : Math.min(120, storedSeconds)
    if (displaySeconds !== storedSeconds) player.persistentData.zapegChestSeconds = displaySeconds
    zapegScore(player.server, 'zapeg_chest_s', name, displaySeconds)
  }
  zapegGivePersonalRewards(player, true)
})

PlayerEvents.loggedOut(event => {
  zapegClearVerifiedCache(event.player)
})

PlayerEvents.advancement(event => {
  const player = event.player
  const name = String(player.username)
  const advancement = String(event.advancement.id)

  if (advancement === 'minecraft:end/kill_dragon' && name === ZAPEG_QUEST_PLAYERS.emir) {
    zapegGrantVerified(player, 'emir_dragon', 'Emir — Son Darbe')
    return
  }

  if (advancement === 'zapeg:detectors/village' && name === ZAPEG_QUEST_PLAYERS.emin) {
    zapegGrantVerified(player, 'emin_village', 'Emin Taha — Köy Peşinde')
    return
  }

  if (advancement === 'zapeg:detectors/tame') {
    // This detector must be repeatable; revoke it after every tame event.
    player.server.runCommandSilent(`advancement revoke ${name} only zapeg:detectors/tame`)
    if (name !== ZAPEG_QUEST_PLAYERS.emin) return

    const tames = Number(player.persistentData.zapegTames || 0) + 1
    player.persistentData.zapegTames = tames
    zapegScore(player.server, 'zapeg_tames', name, tames)
    if (tames >= 10) {
      zapegGrantVerified(player, 'emin_tames', 'Emin Taha — Büyük Kafile')
    }
    return
  }

  if (advancement === 'minecraft:adventure/ol_betsy' && name === ZAPEG_QUEST_PLAYERS.enes) {
    zapegGrantVerified(player, 'enes_crossbow', 'Enes — Arbaletçi')
  }
})

PlayerEvents.inventoryChanged('minecraft:diamond', event => {
  const player = event.player
  if (String(player.username) !== ZAPEG_QUEST_PLAYERS.emir) return
  if (zapegIsVerifiedCached(player, 'emir_diamonds')) return
  if (Number(player.inventory.count('minecraft:diamond')) >= 64) {
    zapegGrantVerified(player, 'emir_diamonds', 'Emir — Mavi Servet')
  }
})

function zapegFireBlock(id) {
  return id === 'minecraft:fire' || id === 'minecraft:soul_fire'
}

function zapegSafeFireBlock(id) {
  if (!id.startsWith('minecraft:')) return false
  const block = id.substring('minecraft:'.length)
  return /^(air|cave_air|void_air|fire|soul_fire|water|lava|netherrack|soul_soil|soul_sand|stone|cobblestone|deepslate|cobbled_deepslate|blackstone|polished_blackstone.*|basalt|smooth_basalt|obsidian|crying_obsidian|bedrock|sand|red_sand|gravel|dirt|coarse_dirt|rooted_dirt|grass_block|clay|bricks|.*_bricks|.*_concrete|.*_terracotta|glass|tinted_glass|.*_glass|.*_glass_pane)$/.test(block)
}

function zapegSafeFireArea(level, x, y, z) {
  for (let dx = -2; dx <= 2; dx++) {
    for (let dy = -1; dy <= 2; dy++) {
      for (let dz = -2; dz <= 2; dz++) {
        if (!zapegSafeFireBlock(String(level.getBlock(x + dx, y + dy, z + dz).id))) return false
      }
    }
  }
  return true
}

function zapegFireMatches(player, x, y, z) {
  return Boolean(player.persistentData.zapegFireActive) &&
    String(player.persistentData.zapegFireDimension) === String(player.level.dimension) &&
    Number(player.persistentData.zapegFireX) === x &&
    Number(player.persistentData.zapegFireY) === y &&
    Number(player.persistentData.zapegFireZ) === z
}

BlockEvents.rightClicked(event => {
  const player = event.player
  if (String(player.username) !== ZAPEG_QUEST_PLAYERS.salih) return

  const item = String(event.item.id)
  const block = event.block
  if (item === 'minecraft:flint_and_steel' && [
    'minecraft:netherrack', 'minecraft:soul_soil', 'minecraft:soul_sand'
  ].indexOf(String(block.id)) !== -1) {
    const x = Number(block.x)
    const y = Number(block.y)
    const z = Number(block.z)
    ZAPEG_PENDING_FIRES[String(player.username)] = {
      expires: Number(player.age) + 10,
      positions: [
        [x, y + 1, z], [x, y - 1, z],
        [x + 1, y, z], [x - 1, y, z],
        [x, y, z + 1], [x, y, z - 1]
      ]
    }
  }

  if (item === 'minecraft:water_bucket' && Boolean(player.persistentData.zapegFireActive)) {
    const dx = Number(block.x) - Number(player.persistentData.zapegFireX)
    const dy = Number(block.y) - Number(player.persistentData.zapegFireY)
    const dz = Number(block.z) - Number(player.persistentData.zapegFireZ)
    if (dx * dx + dy * dy + dz * dz <= 9) {
      ZAPEG_FIRE_ATTEMPTS[String(player.username)] = Number(player.age) + 40
    }
  }
})

BlockEvents.leftClicked(event => {
  const player = event.player
  if (String(player.username) !== ZAPEG_QUEST_PLAYERS.salih) return
  if (!zapegFireBlock(String(event.block.id))) return
  if (zapegFireMatches(player, Number(event.block.x), Number(event.block.y), Number(event.block.z))) {
    ZAPEG_FIRE_ATTEMPTS[String(player.username)] = Number(player.age) + 40
  }
})

PlayerEvents.tick(event => {
  const player = event.player
  const name = String(player.username)

  // Fire placement/extinguish needs tick-level observation; all other checks run at 1 Hz.
  if (name === ZAPEG_QUEST_PLAYERS.salih) {
    const pending = ZAPEG_PENDING_FIRES[name]
    if (pending) {
      if (Number(player.age) > pending.expires) {
        delete ZAPEG_PENDING_FIRES[name]
      } else {
        for (const pos of pending.positions) {
          if (!zapegFireBlock(String(player.level.getBlock(pos[0], pos[1], pos[2]).id))) continue
          if (!zapegSafeFireArea(player.level, pos[0], pos[1], pos[2])) {
            player.tell(Text.of('Tatbikat ateşi reddedildi: 2 blok çevrede güvenli olmayan malzeme var.').red())
            delete ZAPEG_PENDING_FIRES[name]
            break
          }

          player.persistentData.zapegFireActive = true
          player.persistentData.zapegFireDimension = String(player.level.dimension)
          player.persistentData.zapegFireX = pos[0]
          player.persistentData.zapegFireY = pos[1]
          player.persistentData.zapegFireZ = pos[2]
          delete ZAPEG_PENDING_FIRES[name]
          zapegGrantVerified(player, 'salih_ignite', 'Salih — Kontrollü Ateş')
          break
        }
      }
    }

    const attemptUntil = Number(ZAPEG_FIRE_ATTEMPTS[name] || 0)
    if (attemptUntil >= Number(player.age) && Boolean(player.persistentData.zapegFireActive)) {
      const x = Number(player.persistentData.zapegFireX)
      const y = Number(player.persistentData.zapegFireY)
      const z = Number(player.persistentData.zapegFireZ)
      const sameDimension = String(player.persistentData.zapegFireDimension) === String(player.level.dimension)
      const dx = Number(player.x) - (x + 0.5)
      const dy = Number(player.y) - (y + 0.5)
      const dz = Number(player.z) - (z + 0.5)
      if (sameDimension && dx * dx + dy * dy + dz * dz <= 36 && !zapegFireBlock(String(player.level.getBlock(x, y, z).id))) {
        player.persistentData.zapegFireActive = false
        delete ZAPEG_FIRE_ATTEMPTS[name]
        zapegGrantVerified(player, 'salih_extinguish', 'Salih — Alan Güvenli')
      }
    }
  }

  if (Number(player.age) % 20 !== 0) return

  if (name === ZAPEG_QUEST_PLAYERS.emir &&
      !zapegIsVerifiedCached(player, 'emir_diamonds') &&
      Number(player.inventory.count('minecraft:diamond')) >= 64) {
    zapegGrantVerified(player, 'emir_diamonds', 'Emir — Mavi Servet')
  }

  if (name === ZAPEG_QUEST_PLAYERS.mert &&
      !zapegIsVerifiedCached(player, 'mert_minecart') &&
      Number(player.stats.get('minecraft:minecart_one_cm')) >= 500000) {
    zapegGrantVerified(player, 'mert_minecart', 'Mert — Raylarda 5 km')
  }

  const needsDragonRider = !zapegIsVerifiedCached(player, 'dragon_rider')
  const needsEmirDragon = name === ZAPEG_QUEST_PLAYERS.emir &&
    !zapegIsVerifiedCached(player, 'emir_dragon_owner')
  const needsSalihDragon = name === ZAPEG_QUEST_PLAYERS.salih &&
    !zapegIsVerifiedCached(player, 'salih_dragon_owner')
  if ((needsDragonRider || needsEmirDragon || needsSalihDragon) && zapegOwnsMountedDragon(player)) {
    if (needsDragonRider) zapegGrantVerified(player, 'dragon_rider', 'İlk Evcil Ejderha')
    if (needsEmirDragon) {
      zapegGrantVerified(player, 'emir_dragon_owner', 'Emir — Kendi Ejderhası')
    }
    if (needsSalihDragon) {
      zapegGrantVerified(player, 'salih_dragon_owner', 'Salih — Kendi Ejderhası')
    }
  }

  if (name === ZAPEG_QUEST_PLAYERS.recep) {
    if (!zapegIsVerifiedCached(player, 'recep_chest_watch')) {
      // Also probes once after /kubejs reload, when loggedIn did not run again.
      const chestDone = zapegProbeVerifiedOnce(player, 'recep_chest_watch')
      const previousSeconds = Number(player.persistentData.zapegChestSeconds || 0)
      if (chestDone) {
        if (previousSeconds !== 120) {
          player.persistentData.zapegChestSeconds = 120
          zapegScore(player.server, 'zapeg_chest_s', name, 120)
        }
      } else if (previousSeconds >= 120) {
        // The threshold was earned; latch it while a transient grant failure retries.
        zapegGrantVerified(player, 'recep_chest_watch', 'Recep — 120 saniyelik Sandık Nöbeti')
      } else {
        const under = String(player.level.getBlock(
          Math.floor(Number(player.x)),
          Math.floor(Number(player.y) - 0.05),
          Math.floor(Number(player.z))
        ).id)
        const onChest = under === 'minecraft:chest' || under === 'minecraft:trapped_chest'
        const seconds = onChest ? Math.min(120, previousSeconds + 1) : 0
        if (seconds !== previousSeconds) {
          player.persistentData.zapegChestSeconds = seconds
          zapegScore(player.server, 'zapeg_chest_s', name, seconds)
        }
        if (seconds >= 120) {
          zapegGrantVerified(player, 'recep_chest_watch', 'Recep — 120 saniyelik Sandık Nöbeti')
        }
      }
    }
  }

  zapegGivePersonalRewards(player, false)

  const dimension = String(player.level.dimension)
  if (dimension === 'ad_astra:moon' && !player.stages.has('zapeg_moon_landed')) {
    player.stages.add('zapeg_moon_landed')
  } else if (dimension === 'minecraft:overworld' &&
             player.stages.has('zapeg_moon_landed') &&
             !zapegIsVerifiedCached(player, 'moon_return')) {
    zapegGrantVerified(player, 'moon_return', 'Ay’a gidildi ve dönüldü')
  }
})

function zapegActualPlayer(event) {
  const actual = event.source?.actual
  return actual && String(actual.type) === 'minecraft:player' ? actual : null
}

for (const boss of ZAPEG_CATACLYSM_BOSSES) {
  EntityEvents.death(boss, event => {
    const player = zapegActualPlayer(event)
    if (player) zapegGrantVerified(player, 'cataclysm', 'Cataclysm — İlk Boss')
  })
}

EntityEvents.death('draconicevolution:draconic_guardian', event => {
  const player = zapegActualPlayer(event)
  if (player) zapegGrantVerified(player, 'chaos_guardian', 'Chaos Guardian düştü')
})
