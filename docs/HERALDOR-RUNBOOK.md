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
  `servants_after_three_v1`. When explicitly enabled, the isolated Discord
  voice relay resolves that ID to a hash-pinned 23.6-second Opus clip, joins one
  fixed voice channel self-deafened, plays once and immediately leaves.
- A permission-level-2 Director bridge with a persistent campaign phase,
  orthogonal pause state and hardcoded apparition profiles. Minecraft only
  writes one short-lived request; the Python Director is the authority that
  validates, records and dispatches it to the client/server runtime.

There is no automatic servant schedule, custom Heraldor body, boss fight or
LLM-driven combat in this slice. In an active, unpaused campaign with voice
disabled, the audio request is recorded as `suppressed_no_sink`; enabling the
relay later never revives an old event. Dormant/paused suppression is described
below. Pending live requests expire after five minutes rather than ambushing a
channel hours later.

## Operate the campaign Director

Every new Minecraft world starts implicitly at `dormant`. In that phase the
old ambient whisper/global/Discord/shadow roll is suppressed. Phases only move
forward through `presence`, `servants` and `manifestation`; an explicit
`phase start` may intentionally skip forward, while `phase advance` moves one
step. Neither interface can rewind a phase, and `confrontation` is not released.

```text
/zapeg-lore director status
/zapeg-lore director phase start presence
/zapeg-lore director phase start servants
/zapeg-lore director phase start manifestation
/zapeg-lore director phase advance
/zapeg-lore director pause
/zapeg-lore director resume
/zapeg-lore director cancel
```

`pause` does not alter the phase. It suppresses ambient rolls and new live
Director scenes. Rehearsals and `cancel` remain available; `cancel` only stops
the runtime's current scene and never resets, pauses or rewinds the campaign.

The apparition names are command literals, not user-controlled runtime profile
strings:

```text
/zapeg-lore director event rehearse apparition echo <player>
/zapeg-lore director event rehearse apparition threshold <player>
/zapeg-lore director event rehearse apparition motion-echo <player>
/zapeg-lore director event rehearse apparition light-fault <player>
/zapeg-lore director event rehearse apparition peripheral <player>
/zapeg-lore director event rehearse apparition footsteps <player>

/zapeg-lore director event trigger apparition echo <player>
/zapeg-lore director event trigger apparition threshold <player>
/zapeg-lore director event trigger apparition motion-echo <player>
/zapeg-lore director event trigger apparition light-fault <player>
/zapeg-lore director event trigger apparition peripheral <player>
/zapeg-lore director event trigger apparition footsteps <player>
```

`echo`, `threshold` and `peripheral` require `presence`; `motion-echo` and
`footsteps` require `servants`; `light-fault` requires `manifestation`. These
phase gates apply to both the high-level rehearsal and live forms. Live
triggers carry a Director-computed, phase-scaled scene length (presence ×1.0,
servants ×1.15, manifestation ×1.35 of the profile default, clamped to
1200 ticks); rehearsals always use the profile default. Raw OP `/zapegscene`
commands remain an effects-only manual test/override: they consume only the
runtime UUID ledger and never mutate the Python campaign phase or pause state.

The high-level command is asynchronous. Its immediate response says **queued**,
not executed. KubeJS writes one allowlisted token tied to the current hidden
world ID and expiring after 90 seconds. It refuses a second request until the
Director conditionally removes the exact first value. The Director validates
the token again, writes a deterministic SQLite event and only then invokes
`/zapegscene`. A duplicate terminal token is acknowledged without replay;
anything interrupted after the replay barrier is `ambiguous` and is never
retried automatically. Issue a fresh command if an `ambiguous` cancel or scene
must be attempted again.

The Director subtree accepts an actual permission-level-2 player command source
or the exact RCON console source. Command-block sources fail closed. The local
server console is intentionally not admitted through KubeJS because its source
cannot be separated reliably from every function context; use authenticated
RCON for the high-level bridge and `admin status` for host inspection.

Servant scores are still ingested while `dormant` or paused, so high-water and
story observations remain correct. If the third-victory threshold is crossed
then, its voice output is born terminally as `suppressed_campaign_dormant` or
`suppressed_campaign_paused`. Starting/resuming later cannot bank and surprise-
deliver that old audio.

Normally an occupied slot clears within a few seconds. If a hand-edited or
malformed value fails strict parsing, the Director deliberately leaves it for
inspection instead of deleting unknown state. Inspect it, then clear only this
exact path after confirming no valid request is pending:

```text
/data get storage zapeg:heraldor control_request
/data remove storage zapeg:heraldor control_request
```

## Deploy

Apply the tracked overrides using the normal deployment workflow, then restart
Minecraft so the new server script registers cleanly. Rebuild the optional
Director service because its image now contains `heraldor_director.py`:

The high-level apparition commands also require the matching ZapeG runtime on
the server and every participating client. Confirm raw `/zapegscene status`
through authenticated RCON before accepting a live Director scene; an
unavailable runtime is stored as a terminal failed/ambiguous attempt, never
silently retried.

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
docker compose --profile heraldor-voice stop heraldor-voice
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
`suppressed_campaign_dormant`/`suppressed_campaign_paused` when gated,
`suppressed_no_sink` while active with voice disabled, or `pending` followed by
one terminal relay result while active with voice enabled.

## Configure and rehearse Discord voice

The existing DCI Minecraft-chat bot may also be the Heraldor voice identity.
Discord explicitly permits multiple Gateway sessions for an application, so
DCI can retain its chat session while the isolated relay owns voice. Reusing it
is the simplest option for this small, single-guild deployment. It does couple
the relay secret to DCI's broader chat permissions and couples token rotation
and bot-account failure across both features, so a dedicated Heraldor bot
remains an optional stronger isolation boundary.

When reusing DCI, copy the same token into
`secrets/heraldor_discord_bot_token.txt`; do not mount, parse or expose
`data/config/Discord-Integration.toml` to the relay. Give that existing bot
`View Channel`, `Connect`, `Speak` and `Use Voice Activity` in exactly the
private rehearsal and eventual live voice channels. Do not run any other voice
controller for the same bot in this guild. If using a dedicated bot instead,
invite it with only those permissions. Neither option needs a privileged
intent, message permission or slash command for the relay. See Discord's
[Gateway session guidance](https://docs.discord.com/developers/events/gateway).

Set `HERALDOR_DISCORD_SHARED_BOT=true` when reusing DCI. This prevents the
relay's second Gateway session from changing DCI's visible presence. Start the
relay only after DCI reports ready so the two processes do not spend the same
application's concurrent Identify allowance at once. For a dedicated Heraldor
bot, use `false` instead.

Create `secrets/heraldor_discord_bot_token.txt` locally with only the token,
restrict its host permissions, and set these non-secret values in `.env`:

```dotenv
HERALDOR_VOICE_ENABLED=false
HERALDOR_DISCORD_GUILD_ID=<server-id>
HERALDOR_DISCORD_VOICE_CHANNEL_ID=<eventual-live-channel-id>
HERALDOR_DISCORD_TEST_VOICE_CHANNEL_ID=<private-rehearsal-channel-id>
HERALDOR_DISCORD_SHARED_BOT=true
```

Keep `HERALDOR_VOICE_ENABLED=false` through setup. Build and verify the baked
catalog, then start the relay. The relay receives no RCON secret, Minecraft
data, webhook, LLM key or Docker socket:

[Discord voice](https://docs.discord.com/developers/topics/voice-connections)
uses outbound HTTPS/WebSocket plus UDP hole punching. No Docker port is
published, but the host/provider firewall must allow outbound UDP and its return
traffic; a bot that logs in yet times out while joining voice usually indicates
that network boundary or missing channel permissions.

```bash
docker compose --profile heraldor-voice build heraldor-voice
docker compose --profile heraldor-voice run --rm --no-deps heraldor-voice \
  python heraldor_voice.py validate
docker compose --profile heraldor-voice up -d heraldor-voice
docker compose --profile heraldor-voice logs --tail=100 heraldor-voice
```

Join the private rehearsal voice channel with a human account that is not
self/server-deafened, then enqueue one short-lived rehearsal. It never changes
servant victories or story flags:

```bash
docker compose --profile heraldor exec heraldor \
  python heraldor.py admin voice-rehearse
docker compose --profile heraldor exec heraldor \
  python heraldor.py admin status
```

Success is one join, one complete `servants_after_three_v1` playback, immediate
disconnect, and outbox status `delivered`. With nobody audible in the test
channel it must remain silent and finish `suppressed_empty_channel`. A stopped/crashed
relay leaves an uncertain attempt `ambiguous`; it is never replayed. Rehearsal
requests expire in two minutes and have a 30-second pacing gate.

Only after this passes, set `HERALDOR_VOICE_ENABLED=true` and recreate the
Director so future live threshold events are born `pending`:

```bash
docker compose --profile heraldor up -d --force-recreate heraldor
```

Changing the flag does not modify any row already stored as
`suppressed_no_sink`. The live relay also requires a human already present in
the fixed channel and enforces a six-hour voice-attempt gap.

## Restore from a normal server archive

The normal archive contains both live WAL database files and the known-good
online snapshot. Do not start Heraldor directly from the archived live files.
After extracting the normal archive and while the Heraldor daemon is stopped,
promote the verified snapshot and then start it:

```bash
docker compose --profile heraldor-voice stop heraldor-voice
docker compose --profile heraldor stop heraldor
docker compose --profile heraldor run --rm --no-deps heraldor \
  python heraldor.py admin restore-snapshot
docker compose --profile heraldor up -d heraldor
docker compose --profile heraldor-voice up -d heraldor-voice
```

`restore-snapshot` verifies SQLite integrity, atomically replaces the live DB,
and removes archived `-wal`/`-shm` files. It takes both process locks and refuses
while either the Director or voice relay is active.

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
10. Validate the audio catalog/hash/decode, rehearse once with an audible human
    in the private channel, then repeat with an empty or fully deafened channel.
    Verify one self-deafened join/play/
    leave, `delivered` once, and terminal `suppressed_empty_channel` once.
11. Stop the relay during a mocked/private playback, restart it and verify the
    uncertain row becomes `ambiguous` without replay. Verify restore refuses
    while the voice relay lock is held.
12. On a fresh copied world, `director status` reports `dormant` and no ambient
    output is rolled until `phase start presence` is acknowledged.
13. Verify each hardcoded scene profile opens only at its documented phase.
    Pause the campaign: live triggers and ambient stop, rehearsal remains
    available, and `cancel` leaves both phase and pause unchanged.
14. Stop the Director, queue one request and confirm a second is refused. Start
    it after the first token expires and verify terminal suppression. Interrupt
    one mocked scene after its SQLite claim and confirm restart reports
    `ambiguous` without a second `/zapegscene` dispatch.
15. Cross the third-servant threshold once while paused in the copy, resume and
    verify the story observation remains but its terminally suppressed audio is
    never delivered later.

Use `/zapeg-lore servant cleanup` immediately if any targeting or drop invariant
fails. Keep the feature manual until this gate passes.
