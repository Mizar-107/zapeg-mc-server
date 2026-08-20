# HOSTING — day-0 guide for the server operator

You're hosting **ZapeG** — a private modded Minecraft server for 4–10 players: **All the Mods 9 v1.1.1 (Forge, MC 1.20.1) + 27 additions** (23 client+server, 4 server-only). The container resolves the external pins and installs the reviewed ZapeG Citizens and Runtime jars from this repo. Players never install jars one-by-one; Ertu generates one client patch. Full reference: [README.md](README.md). Citizens launch setup: [docs/CITIZENS-HOST-SETUP.md](docs/CITIZENS-HOST-SETUP.md). Private-scene setup: [docs/ZAPEG-RUNTIME-RUNBOOK.md](docs/ZAPEG-RUNTIME-RUNBOOK.md). Decisions/background: [docs/atm9-modpack-project-brief.md](docs/atm9-modpack-project-brief.md).

## Requirements

- Linux host, Docker Engine 24+ and **Docker Compose v2.17+** (`docker compose version`)
- **16 GB+ RAM free** for this stack (12 GB heap + JVM/OS overhead) — 32 GB host ideal
- 4+ decent cores (worldgen/pregen is CPU-hungry), SSD strongly recommended
- CPU affinity is portable by default: `MC_CPUSET=` means all host CPUs. Set a range only after checking this machine's logical CPU topology and hardware health.
- **150 GB free recommended** for a 6000-radius pregen, BlueMap tiles and 14 daily
  archives. Measure after pregen; world/map size varies and 40 GB is not enough headroom.
- `git`, `rsync` and standard Linux tools (`tar`, `sed`, `curl`); `rsync` is required
  by `scripts/apply-overrides.sh`
- **TCP 25565** open/forwarded to the host; give Ertu the public IP (or set up DDNS)

## What `.env` actually needs

For the default `mc + backup` stack:

| Variable | Status | Purpose |
|---|---|---|
| `RCON_PASSWORD` | optional; normally unset | Minecraft generates it internally; set only before enabling `metrics` |
| `ENABLE_WHITELIST` | optional; default `false` | The group chose open access; `true` restores an allowlist |
| `WHITELIST` | optional | Used only when the whitelist is enabled |
| `OPS` | optional; default `Mizar__107` | Permanent offline-mode admin; the accepted spoofing trade-off is below |
| `CF_API_KEY` | optional | Only needed if CurseForge downloads throttle |
| `WORLD_SEED` | leave empty initially | Set only after the seed audition, before creating the real world |
| `MC_CPUSET` | optional; blank | Host-specific Docker CPU affinity; never copy another host's topology blindly |

There are **no required `.env` values for the default `mc + backup` stack**.
RCON is not a player/server-list password; it is Minecraft's private command
channel. The server generates a random secret into `data/.rcon-cli.env`, and the
backup service plus `docker compose exec mc rcon-cli` discover it automatically.
Port `25575` is only on the Docker network and is not published. Keep RCON enabled:
live backups use it to flush/pause saves, while Heraldor uses it for player/time
queries, messages, sounds and shadow events. A truly RCON-free setup would require
cold backups with Minecraft stopped and would disable Heraldor/metrics.

Forward the tracked `.env.example` file, not a filled secret file. The host copies it to `.env` and replaces values locally. Recommended launch handoff (including optional Heraldor settings):

```dotenv
# Optional metrics-only override; normally leave this commented out.
# RCON_PASSWORD=<openssl-rand-hex-32-output>
ENABLE_WHITELIST=false
WHITELIST=
OPS=Mizar__107
WORLD_SEED=
MC_CPUSET=
CF_API_KEY=

# Keep blank unless a real Heraldor-only webhook has been created on the host.
HERALDOR_WEBHOOK=
HERALDOR_EVENTS=false
HERALDOR_CHECK_INTERVAL=300
HERALDOR_MINION_POLL_INTERVAL=10
HERALDOR_P_WHISPER=0.002
HERALDOR_P_GLOBAL=0.0005
HERALDOR_P_DISCORD=0.0003
HERALDOR_P_SHADOWS=0.0002
HERALDOR_VOICE_ENABLED=false
HERALDOR_DISCORD_GUILD_ID=
HERALDOR_DISCORD_VOICE_CHANNEL_ID=
HERALDOR_DISCORD_TEST_VOICE_CHANNEL_ID=
HERALDOR_DISCORD_SHARED_BOT=true
```

The owner deliberately chose public offline-mode, no whitelist and permanent
`OPS=Mizar__107`, and accepts that anyone who reaches `25565` can choose that name
and inherit full admin. This is not authentication. If that trade-off changes,
set `ENABLE_WHITELIST=true`, populate `WHITELIST`, clear `OPS`, recreate `mc`, and
remove any persisted OP entry with host-local `rcon-cli deop Mizar__107`.

Profile-only values:

- `CITIZENS_BRAIN_URL` + `CITIZENS_BRAIN_TOKEN` → shared Citizens controller;
  keep the Ollama key only in `secrets/citizens_ollama_api_key.txt` and follow
  [the dedicated setup guide](docs/CITIZENS-HOST-SETUP.md)
- `RCON_PASSWORD` + `GRAFANA_PASSWORD` → `metrics`; generate two different
  shell-safe values, leave Grafana on `127.0.0.1` with anonymous access off,
  then follow [the metrics runbook](metrics/README.md)
- `RCLONE_DEST` plus local `rclone.conf` → `offsite`
- `HERALDOR_WEBHOOK`, `HERALDOR_EVENTS` and advanced `HERALDOR_CHECK_INTERVAL` / `HERALDOR_MINION_POLL_INTERVAL` / `HERALDOR_P_*` knobs → optional `heraldor`
- `HERALDOR_VOICE_ENABLED`, fixed Discord guild/voice-channel IDs and the relay token file → optional `heraldor-voice`; keep disabled until private rehearsal passes

The default stack does **not** call an LLM. Normal Minecraft↔Discord bridging is also not configured through `.env`; it uses the generated mod config described below.

## Deploy (~30 min, mostly download)

```bash
git clone <REPO_URL> zapeg-mc-server && cd zapeg-mc-server
cp .env.example .env
# edit only wanted options; the default stack needs no secret or player list
docker compose up -d        # default stack = mc + backup
docker compose logs -f mc     # first boot: ~1.1 GB download + Forge install, 5–15 min
```

Ready when the log shows `Done (…)! For help, type "help"`. The backup sidecar starts automatically once `mc` is healthy.

For the intended launch with player- and server-owned LLM citizens, do the one-time secret
setup and use the `citizens` profile instead of stopping here:
[docs/CITIZENS-HOST-SETUP.md](docs/CITIZENS-HOST-SETUP.md). One shared Ollama
key serves every citizen; players never receive it and never run a sidecar.

Then apply the repo's custom layer (quest chapters, kubejs scripts, server icon) and restart:

```bash
scripts/apply-overrides.sh && docker compose restart mc
```

Open the FTB Quests book and verify the three original custom pages plus all ten
added-mod guides load. The new chapters cover Ice and Fire, Immersive Petroleum,
Alex's Caves, Aquamirae, Mowzie's Mobs, Born in Chaos, Simply Swords/Better
Combat, vehicles/ships, Citizens and Incendium. Measurable tasks use real item
or advancement evidence; exact checks, migration/reset commands and the few
honestly manual milestones are in
[docs/QUEST-VALIDATION-TR.md](docs/QUEST-VALIDATION-TR.md).

The custom layer also ships a dormant, versioned Muhtar v2 consultant. After
choosing his overworld town-square coordinates, follow
[the Muhtar runbook](docs/MUHTAR-QUEST-GUIDE-TR.md): snapshot, apply overrides,
restart once for the FTB chapters and fixed `zapeg-guide` bridge, then run
`bash scripts/muhtar-npc.sh apply v2 <X> <Y> <Z>`. Test every branch and repeat
the same quest open/close cycle three times as a non-OP. Muhtar explains mod
choices before the optional handoff; removing him cannot reset or complete a
quest. The older v1 layout remains an independently importable rollback.

## One-time service wiring (after first boot)

**BlueMap** (live web map on `:8100`): edit `data/config/bluemap/core.conf` → `accept-download: true`, then restart. Map renders as chunks generate (pregen fills it fast). Put it behind your reverse proxy / VPN — don't expose 8100 raw.

**Discord bridge**: ZapeG's chosen two-way Minecraft↔Discord bridge always
requires a bot. DCI's `[webhook] enable=true` does not replace it; it only lets
that bot create/manage an outbound appearance webhook for player names/avatars.
Create the bot in the [Discord Developer Portal](https://discord.com/developers/applications), enable the intents required by the [official DCI quick setup](https://erdbeerbaerlp.de/projects/discord-integration/quick-setup), then invite it with `bot` + `applications.commands` scopes. Restrict send/read, manage-webhook and documented manage-channel permissions to one normal-chat channel where possible. Start Minecraft once, stop it, then modify these keys inside the **existing** sections of `data/config/Discord-Integration.toml` (do not append duplicate TOML section headers):

```toml
[general]
botToken = "<host-local bot token>"
botChannel = "<normal chat channel ID>"
allowWebhookMessages = false

[commands]
enabled = false

[webhook]
enable = true
webhookName = "ZAPEG_MC_BRIDGE"
```

The bridge does **not** accept an existing webhook URL: bot token + channel ID are mandatory, and optional webhook mode makes the bot create/manage its own webhook. `allowWebhookMessages=false` prevents bot-managed/Heraldor webhook posts from looping back into Minecraft. Restart and test one message in each direction. Keep Discord commands disabled unless role IDs are deliberately locked down; the official setup warns that commands can kick players or stop the server. The token lives in gitignored `data/`, but `data/` is included in backups/snapshots — protect backup and offsite access like credentials. See the [DCI feature wiki](https://wiki.erdbeerbaerlp.de/dcintegration:root), [webhook FAQ](https://wiki.erdbeerbaerlp.de/dcintegration:faq) and [duplicate-message fix](https://wiki.erdbeerbaerlp.de/dcintegration:common-issues).

**Offsite backups** (optional but recommended): drop an `rclone.conf` next to the compose file (gitignored), set `RCLONE_DEST` in `.env` (e.g. `b2:zapeg-backups/world`), then `docker compose --profile offsite up -d`.

**ZapeG Citizens** (intended launch profile): Numen and ZapeG Citizens are already
loaded as normal client+server Forge mods. The host additionally runs one private
`citizen-brain` container with the shared Ollama key; it is not installed by
players. Follow [the Citizens host guide](docs/CITIZENS-HOST-SETUP.md) exactly,
including its protocol-3 durable-job acceptance test and paired world/brain backup,
before distributing the pack. Citizens 0.4.0 persists multi-step physical work
across restarts under bounded action/model/time budgets; player chat and OP job
controls are documented in that guide. The old chat-only prototype has been removed.

Heraldor uses built-in Turkish line pools plus the authored campaign file
(`npc/campaign-heraldor.yml`) and calls no LLM; timing, targeting, sounds and
events are all deterministic. The old `HERALDOR_LLM`/`LLM_*` knobs are gone.

**Heraldor** (optional, LLM-free): enable it only after `mc` has
completed its first boot, then run `docker compose --profile heraldor up -d --build`.
Only if Discord posts are wanted, create a **separate Heraldor-only webhook**, put its new URL directly in host `.env` as `HERALDOR_WEBHOOK`, and never commit/share it. Blank means no Discord posts. The deliberately rare defaults are exposed as `HERALDOR_CHECK_INTERVAL` and `HERALDOR_P_*`; test before changing them, especially the player-independent Discord roll. `HERALDOR_EVENTS=true` additionally enables staged midnight shadow visits. Director state lives under `data/heraldor/`; its `backup/heraldor.sqlite3` is an online-consistent SQLite snapshot included by the normal backup. Do NOT explain Heraldor to the players.

The first servant is a manual rehearsal, not a random spawn. After applying the
tracked KubeJS overrides and restarting, an OP can use
`/zapeg-lore servant rehearse <player>` and `/zapeg-lore servant cleanup`. The
lootless, XP-less wither skeleton is displayed as `Heraldor'un Hizmetkârı`, can
damage only its selected real player, and expires after 120 seconds. Three
explicit live `/zapeg-lore servant awaken <player>` victories create one durable
story event; rehearsal victories never advance it. Inspect state with
`docker compose --profile heraldor exec heraldor python heraldor.py admin status`.

Runtime 0.2 scenes are also manual until their two-client gate passes. Every
world begins with the Director at `dormant`; a level-2 player or authenticated
RCON can use `/zapeg-lore director status`, the phase/pause controls, and the
allowlisted `event rehearse|trigger apparition ...` subtree documented in the
[Runtime runbook](docs/ZAPEG-RUNTIME-RUNBOOK.md). The high-level command queues
one short-lived request and never means “already executed”; raw `/zapegscene`
remains a low-level effects-only test that does not alter campaign state.

The optional `heraldor-voice` sidecar now maps the allowlisted clip ID
`servants_after_three_v1` to the supplied hash-pinned audio. It is a separate,
self-deafened, output-only relay process that can join only fixed voice channels,
plays once only when a non-deafened human is already present, and immediately disconnects.
It receives no RCON, Minecraft data, webhook, LLM key or Docker socket. On this
single-guild deployment, the relay may reuse the existing DCI bot identity:
copy the same token into `secrets/heraldor_discord_bot_token.txt`, set
`HERALDOR_DISCORD_SHARED_BOT=true`, and do not mount or parse
`Discord-Integration.toml`. Discord supports multiple
Gateway sessions for an application; DCI remains the chat session and the
relay owns voice only. Never run another voice controller for that bot in the
same guild. A dedicated bot remains the stronger isolation option because a
relay-token leak would also expose DCI's broader chat permissions, while token
rotation or account failure can break both systems. Existing
`suppressed_no_sink` rows never replay. Follow
[the Heraldor runbook](docs/HERALDOR-RUNBOOK.md) before enabling it. Discord
voice needs outbound HTTPS/WebSocket and UDP return traffic; no inbound Docker
port should be published for the relay.

Each Minecraft world receives a hidden random Heraldor token. Replacing a
throwaway world starts an independent servant-victory stream instead of making
the new score look like a regression. After restoring a normal server archive,
keep Heraldor stopped and promote its consistent SQLite snapshot using the
restore command in the runbook before starting the service.

## Verify all 27 additions loaded (once, after first boot)

```bash
ls data/mods | grep -icE 'iceandfire|citadel|immersivepetroleum|Immersive Vehicles|MTS Official Pack|OAmP|alekiNiftyShips|alexscaves|mowziesmobs|easy_npc|aquamirae|fragmentum|born_in_chaos|simplyswords|valkyrienskies|eureka|numen|cc-tweaked|zapeg-citizens|zapeg-runtime|bettercombat|chunky|bluemap|incendium|dcintegration'   # expect 27
test -f data/mods/DungeonsArise-1.20.x-2.1.58-release.jar && test -f data/mods/player-animation-lib-forge-1.0.2-rc1+1.20.jar   # ATM9 base, not additions
```

Also save `docker compose exec mc rcon-cli forge mods` and compare it with `extras/cf-mods.txt` plus `MODRINTH_PROJECTS` in `docker-compose.yml`. A four-mod check is obsolete.

If boot fails with **"Mod IceandFire requires Citadel between …"** → in `extras/cf-mods.txt` swap the citadel line to `citadel:6002521`, then `docker compose up -d mc`. Tell Ertu.

## Access model — offline-mode, read once

`ONLINE_MODE=false` is **deliberate**: players join from any launcher, no Mojang auth. Consequences:

- Minecraft cannot prove who owns a username. The group knowingly leaves the
  whitelist off; anyone who can reach `25565` may join.
- `Mizar__107` is permanent OP by owner decision. Anyone can copy that exact name
  and gain OP; this risk has been explicitly accepted, not technically mitigated.
- For administration, the host may run `docker compose exec mc rcon-cli <command>`.
  It needs no supplied password because the in-container helper reads the generated
  credential. RCON port `25575` is internal and is not published.
- Player identity = username (offline UUID is derived from it). A player who changes their name is a *new* player: fresh inventory, lost claims. Tell players to pick a name once.
- Usernames in personal lore keys must match exactly.
- Do **not** flip online-mode later without coordinating with Ertu — switching modes mid-world changes every UUID and orphans inventories/claims.

## World protocol (agreed in the brief — please follow)

1. **First world is a throwaway** for verification: join once (ask Ertu), confirm dragon roosts exist (`/locate structure` tab-completes `iceandfire:` entries) and Immersive Petroleum loaded. Spawn one vehicle from MTS Official Pack and one from the Official Automobile Pack; fuel and drive them over normal terrain, unload/reload their chunk, restart, reconnect and confirm both persist. Separately assemble/move/disassemble a small Eureka ship. Build and cargo-test a Nifty sloop, anchor and dual-lead moor it, travel 16+ chunks away, return, restart and reconnect; repeat with Entity Culling and shaders on/off. Test with 2–3 clients while watching Spark/TPS, FPS and host network use. Never stack Nifty, IV, Eureka/VS or Create vehicle physics, and do not enable VS's experimental air-pocket/connectivity system.
2. **Generated config pass, before any real-world chunks exist:** run
   `scripts/iceandfire-config-check.sh`, edit the surfaced live config, set Ice and
   Fire silver ore generation **off** and dragon griefing low/none, then snapshot
   and restart `mc`. Recheck the throwaway world. These settings persist when
   `data/world` is reset; changing silver after pregen would be too late.
3. **Seed audition** (pack uses Terralith + Biomes O' Plenty — vanilla seed lists don't apply, so we pick empirically): with `WORLD_SEED` empty, each fresh world is a random candidate. Check spawn on foot + BlueMap, screenshot for the group, then stop `backup` and `mc`, remove only `data/world`, and run `docker compose up -d --force-recreate` for the next candidate. 2–3 rounds; when the group picks, note the seed (shown in BlueMap / `/seed`) and set `WORLD_SEED` in `.env`.
4. Reset for the real world:
   ```bash
   docker compose stop backup mc
   scripts/snapshot.sh pre-real-world
   rm -rf data/world
   docker compose up -d --force-recreate
   ```
5. On the real world, apply the agreed gamerules (once): `scripts/apply-gamerules.sh` (values: [TUNING.md](TUNING.md))
6. Pregen the real world (run overnight; heavy CPU is expected):
   ```bash
   scripts/pregen.sh 6000
   ```

## Rules of operation

- **Before ANY change** (mod/config/pack version): `scripts/snapshot.sh <label>` → `./snapshots/`
- **Updates arrive via git** — never edit pins locally:
  ```bash
  git pull && scripts/snapshot.sh pre-update && docker compose up -d mc
  ```
- Backups: automatic daily tar of world+configs → `./backups/`, pruned after 14 days.
  Before inviting players, let one real automatic archive finish and perform a
  cold restore drill with the stack stopped; verify ownership and world startup.
  Monitor disk usage after pregen. Offsite `rclone sync` mirrors local deletion,
  so enable bucket versioning/immutability if it must survive local pruning.
- Console: `docker compose exec mc rcon-cli` (the generated internal password is discovered automatically).
- Performance complaints: pack ships Spark — `rcon-cli spark profiler start` / `stop`; send results to Ertu. Don't add mods to "fix" performance.

## Don'ts

- Don't exceed `MEMORY: 12G` — GC degrades above that on this pack.
- Don't update the ATM9 version or any mod yourself — that's coordinated with client updates. Players need the same 23 client+server additions; Chunky, BlueMap, Incendium and Discord Integration stay server-only.
- Don't delete `snapshots/` or `backups/` to free space without checking with Ertu.
