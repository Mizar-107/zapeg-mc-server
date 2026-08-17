# Heraldor Director v2 — host runbook

This is a private operator feature. Do not distribute this document to players
or explain the command, tags, counters, thresholds, or audio trigger.

## What is live in this slice

- Existing rare whispers, global lines, webhook posts and optional shadow visits.
- Persistent SQLite pacing with one ambient event at most per roll, a six-hour
  global quiet period, a 24-hour target quiet period, a two-event rolling daily
  budget, seven-day Discord/shadow cooldowns and a 24-hour quiet period after a
  major story beat.
- A manually summoned vanilla wither-skeleton rehearsal displayed as
  `Heraldor'un Hizmetkârı`.
- A hidden, durable global victory counter consumed by the Director through
  RCON. Repeated polls and restarts cannot replay a consumed victory. Every
  Minecraft world gets a persistent random token, so replacing a throwaway
  world starts a separate stream instead of looking like a score regression.
- One typed audio request at the third legitimate victory, stored with clip ID
  `servants_after_three_v1`.

There is no automatic servant schedule, voice relay, custom Heraldor body, boss
fight or LLM-driven combat in this slice. With no relay, the audio request is
recorded as `suppressed_no_sink`; installing a relay later will not unexpectedly
play an old event.

## Deploy

Apply the tracked overrides using the normal deployment workflow, then restart
Minecraft so the new server script registers cleanly. Rebuild the optional
Director service because its image now contains `heraldor_director.py`:

`apply-overrides.sh` synchronizes the entire tracked override tree, not only
Heraldor. Finish and commit any concurrent quest/NPC/mod work first; deploy only
from the intended clean release checkout. Follow the mandatory snapshot ritual:

```bash
git status --short
scripts/snapshot.sh pre-heraldor-director-v2
mkdir -p data/heraldor
./scripts/apply-overrides.sh
docker compose restart mc
docker compose --profile heraldor up -d --build heraldor
docker compose --profile heraldor logs --tail=100 heraldor
```

If the boot log or `/kubejs errors` is not clean, run the cleanup command when
available, then stop Heraldor, backup and Minecraft. Return the host to the
previous release and restore the pre-change archive while everything is still
stopped. Both archive extraction and `apply-overrides.sh` are additive, so the
old release cannot remove these new scripts by itself. Delete only these two
exact live files after extraction, re-apply the old release's overrides, and
then start Minecraft/backup:

```bash
docker compose --profile heraldor stop heraldor
docker compose stop backup mc
# Restore the pre-Heraldor archive over data/ and return to the prior release.
rm -f -- data/kubejs/server_scripts/zapeg_heraldor_servant.js
rm -f -- data/kubejs/startup_scripts/zapeg_heraldor_servant_xp.js
./scripts/apply-overrides.sh
docker compose up -d mc backup
```

The service creates `data/heraldor/heraldor.sqlite3` plus a consistent online
snapshot at `data/heraldor/backup/heraldor.sqlite3`. Both stay server-side and
are included in the normal `data/` archive.

## Rehearse in a disposable arena

The target must be a real online player standing near open, solid ground with
three blocks of headroom:

```text
/zapeg-lore servant rehearse <player>
/zapeg-lore servant cleanup
```

`rehearse` exercises the full encounter but never touches the story-victory
counter. The deliberately explicit `/zapeg-lore servant awaken <player>` is the
live form; only its legitimate player final blows advance Heraldor. Use `awaken`
for counter/threshold acceptance only in a fully isolated copied deployment
with its own `data/heraldor/`, then discard that test state.

Only permission-level-2 operators can see or execute the command. The servant:

- has 40 health, 6 attack, a stone sword and a 120-second game-time deadline;
- searches for safe ground 8–12 blocks from the target and fails closed;
- repeatedly targets only the selected player and cannot damage other players,
  Citizens/Numen bodies, villagers, pets, or other living entities;
- disappears if the target logs out, dies, changes dimension or moves over 48
  blocks away;
- yields no mob loot, equipment, skull or XP;
- counts only a real-player final blow. Timeout, environment, `/kill`, another
  mob or a Numen body does not count.

## Inspect the hidden state

Minecraft-side checks:

```text
/scoreboard players get #total zapeg_hsvc
/scoreboard players get #world zh_svc_world
/data get storage zapeg:heraldor last_minion_kill
/kubejs errors
```

Director-side check:

```bash
docker compose --profile heraldor exec heraldor python heraldor.py admin status
```

At the first transition to three victories, status should show the same
`servant_world_token` as the hidden world score, `servant_high_water: 3`, a
recent `servant_threshold` event and an outbox row named
`story:heraldor-servants:defeated:3:v1:world:<token>` with status
`suppressed_no_sink`.

## Restore from a normal server archive

The normal archive contains both live WAL database files and the known-good
online snapshot. Do not start Heraldor directly from the archived live files.
After extracting the normal archive and while the Heraldor daemon is stopped,
promote the verified snapshot and then start it:

```bash
docker compose --profile heraldor stop heraldor
docker compose --profile heraldor run --rm --no-deps heraldor \
  python heraldor.py admin restore-snapshot
docker compose --profile heraldor up -d heraldor
```

`restore-snapshot` verifies SQLite integrity, atomically replaces the live DB,
and removes archived `-wal`/`-shm` files. Never run it while the Heraldor daemon
is active.

## Acceptance gate

Before using it in the story, verify all of these in a copied/disposable world:

1. `/kubejs errors` remains empty after deploy and a full restart.
2. A non-OP cannot see or execute `/zapeg-lore`.
3. Flat open ground spawns one rehearsal servant; water/cramped ground fails without a
   spawn; a second servant is refused while the first deadline is active.
4. The servant harms its selected player but cannot harm a nearby Citizen,
   helper player, villager or pet.
5. Rehearsal final blows do not count. In the isolated copy, live `awaken`
   player melee and projectile final blows count exactly once. Lava, fall,
   timeout, cleanup, and Citizen final blows do not count.
6. It drops no item, equipment, skull or XP.
7. Logout, death, dimension change, distance and the 2,400-tick deadline clean
   it up. Unload/reload its chunk across the deadline and verify cleanup within
   the five-second idle safety sweep.
8. Restart Minecraft and the Director between victories; the hidden score and
   SQLite high-water mark remain aligned and the third-victory event appears
   exactly once.
9. Run the normal backup, restore it with `admin restore-snapshot`, then inspect
   the promoted live DB with `admin status`; no event is duplicated.

Use `/zapeg-lore servant cleanup` immediately if any targeting or drop invariant
fails. Keep the feature manual until this gate passes.
