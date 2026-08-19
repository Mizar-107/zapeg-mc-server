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
- Fourteen apparition profiles on runtime protocol `7` (v0.4): the original
  families plus `rift` (eclipse / tear / unmoor / witness). Protocol 6 clients
  fail the handshake rather than mis-decoding wire id 13 or a non-colossus
  stage. `light-fault` and `chroma-break` remain public aliases of rift
  stages 0 and 1; `whisper-steps` is haunt stage 2 of `footsteps`. The
  operator-only `visitation` OS-level scare (a brief face blink outside the
  game window, a glitched window title, a small window pulse and an optional
  taskbar flash — all exactly restored, per-client opt-out via the runtime's
  `osScares` client config) is unchanged.
- A client-side gaze-pull layer: during an allowlisted scene's pull window
  the target's rendered camera is dragged toward the apparition's glowing
  eyes at a slow bounded rate. The player can fight it, but the pull wins
  smoothly, eases in and out, and releases cleanly with zero residual
  rotation.
- In-game Discord bridge actions: `/zapeg-lore discord whisper`
  posts one seeded Turkish unease line through the configured webhook
  (fail-closed when unconfigured, audited, paced by a per-world cooldown),
  and `/zapeg-lore voice rehearse` enqueues a rehearsal-only voice
  clip under the same gates as the host-side `admin voice-rehearse`.
- An opt-in autonomous scene scheduler (off by default) that clusters scenes
  into a "night of activity" followed by days of silence, enforces a
  per-subject gap, and never runs while dormant, paused, inside a story quiet
  window, or while any scene is still in flight.
- Stalking memory: the daemon samples online player positions on a slow
  interval and collapses them into coarse 32-block cells, per world and per
  player, capped per player. Ground-anchored live scenes then prefer anchors
  near cells the target actually visits. Nothing finer than a cell is ever
  stored, and every cell is purged the moment a different world token appears.
- Grave echoes: player deaths are counted in a hidden scoreboard and the death
  site is stored server-side. Rarely, long after a death, the scheduler may
  answer it with one quiet scene near the site. Fresh deaths are never
  answered, and the scene never mocks the player.
- Servant aftermath: after a legitimate servant victory, that player's next
  scheduled scene is always `footsteps_01`. Pure pacing; nothing else changes.

There is no automatic servant schedule, custom Heraldor body, boss fight or
LLM-driven combat in this slice. In an active, unpaused campaign with voice
disabled, the audio request is recorded as `suppressed_no_sink`; enabling the
relay later never revives an old event. Dormant/paused suppression is described
below. Pending live requests expire after five minutes rather than ambushing a
channel hours later.

## Operate Heraldor from in-game OP

OP drives the story by hand. There is no `/zapeg-lore director` tree, and no
in-game `status` / `pause` / `resume` / `phase` / `colossus reset`. A new
world still starts `dormant` (ambient rolls stay quiet). Delivered **live
triggers** promote campaign memory to at least that profile's floor so the
daemon can ingest servant kills and optional scheduler beats; **rehearse**
never does.

```text
/zapeg-lore
/zapeg-lore servant rehearse <player>
/zapeg-lore servant awaken <player>
/zapeg-lore servant cleanup
/zapeg-lore rehearse <profile> <player>
/zapeg-lore trigger <profile> <player>
/zapeg-lore cancel
/zapeg-lore discord whisper
/zapeg-lore voice rehearse
```

A bare `/zapeg-lore`, or any incomplete OP command, replies with that usage.
`cancel` only stops the runtime's current scene (`zapegscene cancel-all`).
Raw `/zapegscene` remains effects-only.

Apparition names are command literals:

```text
/zapeg-lore rehearse echo|threshold|peripheral|sky-mark|motion-echo|near-miss|footsteps|closing-steps|whisper-steps|false-passage|rift|eclipse|unmoor|witness|light-fault|chroma-break|colossus|visitation <player>
/zapeg-lore trigger echo|threshold|peripheral|sky-mark|motion-echo|near-miss|footsteps|closing-steps|whisper-steps|false-passage|rift|eclipse|unmoor|witness|light-fault|chroma-break|colossus|visitation <player>
```

`rift` / `eclipse` / `light-fault` are the same eclipse beat; `chroma-break` is
rift tear; `unmoor` is the slow acid warp; `witness` is HUD-off fullscreen
eyes. `whisper-steps` and `closing-steps` are haunt stages of `footsteps`.

Live triggers carry a Director-computed, phase-scaled scene length using at
least the profile floor (presence ×1.0, servants ×1.15, manifestation ×1.35,
clamped to 1200 ticks); rehearsals always use the profile default.
Ground-anchored live profiles (`echo`, `threshold`, `peripheral`, `footsteps`,
`false-passage`) additionally carry a coarse anchor hint from stalking memory
when one exists, so the scene appears near a place the target actually visits.

The `colossus` apparition is the escalation encounter: the Director stores one
approach stage (0–4) per target per world and sends it with the scene. A
delivered live trigger advances the stage by one — horizon silhouette, distant
figure, looming, towering near-presence, then the watching finale — and the
trigger after the finale wraps back to the horizon. Rehearsals play at the
stored stage without advancing it, a rejected or failed trigger leaves it
untouched. There is no in-game colossus reset; host SQLite remains the
authority if a stage must be cleared. The autonomous scheduler can never pick `colossus` on its
own; it only ever moves when an operator triggers it. To preview a specific
stage without touching stored state, use the raw runtime form `/zapegscene
rehearse <player> colossus_01 <0-4>`. Raw OP `/zapegscene` commands remain an
effects-only manual test/override: they consume only the runtime UUID ledger
and never mutate the Python campaign phase, pause state or colossus stage.

The `visitation` apparition is the OS-level scare: the target's client
briefly shows the bundled face in a borderless always-on-top window, glitches
the game window title into block glyphs, pulses the window position and
optionally flashes the taskbar — then restores everything exactly. It is
operator-only like `colossus` (the scheduler never plans it), renders nothing
in-game, and each player can disable any of its beats locally in the
runtime's `osScares` client config. The two Discord bridge actions are
operator beats too: `discord whisper` posts one seeded Turkish unease line as
Heraldor through the configured webhook — it fails closed when no webhook is
set, audits every attempt in SQLite, and enforces a per-world cooldown
(`HERALDOR_DISCORD_MANUAL_GAP_SECONDS`, default 600) so the channel can never
be spammed — and `voice rehearse` enqueues a rehearsal-only voice clip under
exactly the same gates as the host-side `admin voice-rehearse`. Neither
action takes arguments, and neither advances any story state.

## How the campaign advances

Everything is operator-driven; nothing advances on its own unless the optional
scheduler is enabled. **rehearse** is practice — it plays the effect and
records a rehearsal event, but never moves campaign memory, pacing or the
colossus stage. **trigger** is live — it is validated, recorded, and counts
immediately from dormant: live scenes feed pacing, campaign memory rises to
the profile floor, and each delivered live `colossus` trigger climbs the
stored approach stage by one. The third legitimate servant victory still arms
the one-time voice clip once the world is no longer dormant. A typical evening
is: `trigger <profile> <player>` for live beats (rehearse first when unsure),
`servant awaken` when you want the minion, `discord whisper` for an occasional
channel beat, and `colossus` triggers spaced across sessions.

The high-level command is asynchronous. Its immediate response says **queued**,
not executed. KubeJS writes one allowlisted token tied to the current hidden
world ID and expiring after 90 seconds. It refuses a second request until the
Director conditionally removes the exact first value. The Director validates
the token again, writes a deterministic SQLite event and only then invokes
`/zapegscene`. A duplicate terminal token is acknowledged without replay;
anything interrupted after the replay barrier is `ambiguous` and is never
retried automatically. Issue a fresh command if an `ambiguous` cancel or scene
must be attempted again.

The `/zapeg-lore` mailbox accepts an actual permission-level-2 player command source
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

## Configure the autonomous scene scheduler

The scheduler is off by default. Enable it only after the two-client privacy
gate below has passed, and only on a campaign that is already in an active
phase:

```dotenv
HERALDOR_SCENE_SCHEDULER=true
SCHEDULER_INTERVAL=60
STALK_SAMPLE_INTERVAL=45
DEATH_POLL_INTERVAL=30
```

With the scheduler on, the Director periodically considers one scene for one
online player. A scene is planned only when all of these hold: the campaign is
active and unpaused, no story quiet window is running, no scene is reserved or
in flight, and the cluster pacing allows it — scenes cluster into a "night of
activity" (a bounded budget of scenes with short gaps) followed by days of
silence, and each subject has their own cooldown. Even then, two probability
gates keep openings and follow-up beats rare. Every planned scene is a normal
audited Director event with `planner=scheduler` and a reason of
`cluster_open`, `cluster_beat`, `aftermath` or `grave_echo`. The `colossus`
profile is operator-only and is never planned, scheduled or otherwise started
without an explicit OP command.

Stalking memory never stores exact positions: samples collapse into 32-block
cells, capped per player, and the moment a new world token is observed every
old cell is purged. Grave echoes require a death at least twenty minutes old,
fire at most once per death, and mark the death event `echoed` so it is never
answered twice. Disabling the scheduler stops new plans; stalk sampling and
death ingestion keep running so the memory stays warm.

## Deploy

Apply the tracked overrides using the normal deployment workflow, then restart
Minecraft so the new server script registers cleanly. The Director image bakes
in `heraldor.py` and `heraldor_director.py` at build time, so rebuild the
optional service whenever the Python side changes:

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
12. On a fresh copied world, campaign memory stays `dormant` and no ambient
    output is rolled until a live `/zapeg-lore trigger` is delivered.
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
16. Two-client privacy for every protocol-6 profile: the target renders/hears
    the full scene while a nearby observer receives no packet, no sound, no
    GUI artifact and no sky/doorway geometry — verify with both clients in
    first and third person, with shaders on and off (Embeddium/Oculus) and
    Entity Culling enabled. On every humanoid figure (`echo`, `threshold`,
    `motion-echo`, `peripheral`, `near-miss`) confirm the two ember-orange
    eyes ride the head: visible on the dark silhouettes, and on `motion-echo`
    glowing on the newest copy's own face while the lag copies stay eyeless.
    Walk around an `echo` figure: the eyes fade out past the front hemisphere
    instead of shining through the back of the head.
17. Photosensitivity check on `chroma-break`: intensity stays capped, the
    pulse stays slow, and there is no rapid full-screen flashing even at the
    longest phase-scaled TTL. The eye glow on every profile is steady — it
    never strobes; the only motion is the colossus finale's slow narrowing.
18. Cleanup paths: logout, death, dimension change and `/zapegscene
    cancel-all` mid-scene remove every trace — sky mark, passage, chroma
    overlay, camera unease and fog dip all decay to zero immediately.
19. Scheduler dry run in the copy: enable `HERALDOR_SCENE_SCHEDULER`, confirm
    scenes cluster then fall silent for days, confirm `planner=scheduler`
    events in `admin status`, and confirm a fresh death is never echoed while
    an old one is echoed at most once near its site. Confirm a long idle run
    never starts a `colossus` scene on its own.
20. Stalking-memory boundary: inspect the SQLite `stalk_cells` table and
    confirm only coarse 32-block cells exist, then change the world token and
    confirm every old cell is purged.
21. Two-client privacy for the colossus at every stage: the target sees the
    silhouette and feels the footfall pulses while a nearby observer — even
    standing beside the target and looking the same way — receives no packet,
    no silhouette, no boom, no heartbeat and no camera shake. Verify in first
    and third person. Confirm the two orange eyes read clearly at every stage
    distance (280 → 70 blocks), by day and by night, sit slightly too far
    apart, hold after the body starts fading, and slowly narrow during the
    stage-4 watch.
22. Shake comfort check: during a stage-3/4 rehearsal the footfall pulses read
    as deep ground thuds, not motion sickness — each pulse decays within about
    a second, the camera never drifts between steps, and the target keeps full
    control (walking, aiming, inventory) throughout. If anyone reports
    discomfort, stop using stages 3–4 until the caps are re-tuned.
23. Stage progression, rehearsal vs live: rehearse `colossus` twice and
    confirm both play at the same stored stage; live-trigger once and confirm
    the next rehearsal has moved one stage closer. Restart the Director between steps and
    confirm the stage survives in SQLite, and confirm a second player has an
    independent stage.
24. Colossus cleanup paths: logout, death, dimension change and
    `/zapegscene cancel-all` mid-scene remove the silhouette, the shake and
    the heartbeat immediately, with no residue after relog.
25. Colossus shader matrix: rehearse stage 1 and stage 4 with shaders off,
    with Embeddium, and with Oculus + a common pack — the silhouette must read
    as a dark shape in the fog (never invisible, never body-glowing), the eyes
    must punch through darkness and fog as steady orange glows at 280 blocks,
    terrain in front of it must occlude it honestly, and the fog dip prelude
    must not fight the pack's own fog.
26. Gaze-pull comfort and release: during an `echo` live scene the pull
    window drags the camera toward the figure's eyes slowly enough to fight;
    the target can still walk, and resisting mouse input is visibly partial —
    the pull wins over seconds, never snaps. When the scene resolves (or is
    cancelled, or the target logs out, dies or changes dimension) the camera
    is exactly where the player's own input left it: no residual drift, no
    velocity, no offset. Repeat for the colossus stage-4 finale. If anyone
    reports nausea, treat it as a tuning bug.
27. Two-client privacy for `visitation`: rehearse it with a bystander beside
    the target — the bystander's PC shows no popup, no title flicker, no
    window pulse and no taskbar flash, and receives no packet. On the target,
    the face blink fades in and out in under two seconds, never steals
    keyboard or mouse focus, the title and window geometry restore exactly,
    and nothing persists after the scene.
28. Visitation opt-out and platform matrix: on the target's client set
    `osScares.enabled=false` in `zapeg_runtime-client.toml` and confirm a
    rehearsal does absolutely nothing; re-enable and flip each sub-toggle
    (`facePopup`, `windowWrongness`, `taskbarFlash`) to confirm each beat is
    independently suppressed. Run once on each platform in the group
    (Windows primary; macOS/Linux must fail silent or behave — never error,
    never steal focus, never leave a changed title).
29. Discord bridge behavior: with `HERALDOR_WEBHOOK` unset, `discord whisper`
    fails closed and audits the refusal; with it set, one whisper posts one
    Turkish unease line as Heraldor, a second immediate whisper is held by
    the per-world cooldown, and the audit rows appear in `admin status`.
    Confirm the posted text never explains Heraldor.
30. Voice bridge behavior: `voice rehearse` from in-game enqueues exactly one
    rehearsal-only clip (visible in `admin status`), respects the rehearsal
    pacing gate, and never arms or advances the live third-victory event.

Use `/zapeg-lore servant cleanup` immediately if any targeting or drop invariant
fails. Keep the feature manual until this gate passes.
