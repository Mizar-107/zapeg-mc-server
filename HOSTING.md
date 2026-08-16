# HOSTING — day-0 guide for the server operator

You're hosting **ZapeG** — a private modded Minecraft server for 4–10 players: **All the Mods 9 v1.1.1 (Forge, MC 1.20.1) + 21 additions** (17 client+server, 4 server-only). The container downloads the pack and additions from this repo's declarations. Players never install jars one-by-one; Ertu generates one client patch. Full reference: [README.md](README.md). Decisions/background: [docs/atm9-modpack-project-brief.md](docs/atm9-modpack-project-brief.md).

## Requirements

- Linux host, Docker Engine 24+ with the compose plugin (`docker compose version` works)
- **16 GB+ RAM free** for this stack (12 GB heap + JVM/OS overhead) — 32 GB host ideal
- 4+ decent cores (worldgen/pregen is CPU-hungry), SSD strongly recommended
- CPU affinity is portable by default: `MC_CPUSET=` means all host CPUs. Set a range only after checking this machine's logical CPU topology and hardware health.
- ~40 GB disk (pack ~10 GB installed, world grows, 14 days of backups)
- **TCP 25565** open/forwarded to the host; give Ertu the public IP (or set up DDNS)

## What `.env` actually needs

For the default `mc + backup` stack:

| Variable | Status | Purpose |
|---|---|---|
| `RCON_PASSWORD` | **required** | Server scripts and backup sidecar |
| `ENABLE_WHITELIST` | safe default `true` | Set `false` only when port 25565 is network-gated by VPN/firewall allowlist |
| `WHITELIST` | required when enabled | Comma-separated fixed usernames; may instead be populated later with rcon |
| `OPS` | optional; keep blank | Permanent OP names are spoofable in offline-mode; use host-local rcon and deop afterward |
| `CF_API_KEY` | optional | Only needed if CurseForge downloads throttle |
| `WORLD_SEED` | leave empty initially | Set only after the seed audition, before creating the real world |
| `MC_CPUSET` | optional; blank | Host-specific Docker CPU affinity; never copy another host's topology blindly |

`RCON_PASSWORD` is **not** a player/server-list password. RCON is Minecraft's password-protected remote administration console; this stack uses it internally for backups, scripts, metrics and optional sidecars. Port `25575` is not published by Compose, but the shared secret must still be long and random. Generate it on the host and do not send the value back through chat:

```bash
openssl rand -hex 32
```

Forward the tracked `.env.example` file, not a filled secret file. The host copies it to `.env` and replaces values locally. Minimum LLM-free handoff:

```dotenv
# Host pastes the output of `openssl rand -hex 32` after the equals sign.
RCON_PASSWORD=
ENABLE_WHITELIST=true
WHITELIST=<exact_name_1>,<exact_name_2>
OPS=
WORLD_SEED=
MC_CPUSET=
CF_API_KEY=

HERALDOR_WEBHOOK=<new_Heraldor-only_webhook_or_blank>
HERALDOR_EVENTS=false
HERALDOR_LLM=false
HERALDOR_CHECK_INTERVAL=300
HERALDOR_P_WHISPER=0.002
HERALDOR_P_GLOBAL=0.0005
HERALDOR_P_DISCORD=0.0003
HERALDOR_P_SHADOWS=0.0002
```

If the host really restricts `25565` to the group with a VPN/Tailscale or a firewall IP allowlist, it may set `ENABLE_WHITELIST=false` and leave `WHITELIST=` empty. A hardened host, an unadvertised IP or a Discord invite alone is **not** that restriction. Never combine public offline-mode, no whitelist and a permanent `OPS=Mizar__107`: anyone can choose that username and inherit admin.

Profile-only values:

- `GRAFANA_PASSWORD` → `metrics`; set a long random value before enabling (the compose fallback is public/unsafe)
- `RCLONE_DEST` plus local `rclone.conf` → `offsite`
- `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`, `NPC_POS` → optional `npc` prototype
- `HERALDOR_WEBHOOK`, `HERALDOR_EVENTS`, `HERALDOR_LLM` and advanced `HERALDOR_CHECK_INTERVAL` / `HERALDOR_P_*` knobs → optional `heraldor`

The default stack does **not** call an LLM. Normal Minecraft↔Discord bridging is also not configured through `.env`; it uses the generated mod config described below.

## Deploy (~30 min, mostly download)

```bash
git clone <REPO_URL> zapeg-mc-server && cd zapeg-mc-server
cp .env.example .env
# edit .env: generate RCON_PASSWORD locally; fill WHITELIST while it is enabled
docker compose up -d        # default stack = mc + backup
docker compose logs -f mc     # first boot: ~1.1 GB download + Forge install, 5–15 min
```

Ready when the log shows `Done (…)! For help, type "help"`. The backup sidecar starts automatically once `mc` is healthy.

Then apply the repo's custom layer (quest chapters, kubejs scripts, server icon) and restart:

```bash
scripts/apply-overrides.sh && docker compose restart mc
```

## One-time service wiring (after first boot)

**BlueMap** (live web map on `:8100`): edit `data/config/bluemap/core.conf` → `accept-download: true`, then restart. Map renders as chunks generate (pregen fills it fast). Put it behind your reverse proxy / VPN — don't expose 8100 raw.

**Discord bridge**: create a bot in the [Discord Developer Portal](https://discord.com/developers/applications), enable the intents required by the [official DCI quick setup](https://erdbeerbaerlp.de/projects/discord-integration/quick-setup), then invite it with `bot` + `applications.commands` scopes. Restrict send/read, manage-webhook and documented manage-channel permissions to one normal-chat channel where possible. Start Minecraft once, stop it, then modify these keys inside the **existing** sections of `data/config/Discord-Integration.toml` (do not append duplicate TOML section headers):

```toml
[general]
botToken = "<host-local bot token>"
botChannel = "<normal chat channel ID>"

[commands]
enabled = false

[webhook]
enable = true
webhookName = "ZAPEG_MC_BRIDGE"
```

The bridge does **not** accept an existing webhook URL: bot token + channel ID are mandatory, and optional webhook mode makes the bot create/manage its own webhook. Restart and test one message in each direction. Keep Discord commands disabled unless role IDs are deliberately locked down; the official setup warns that commands can kick players or stop the server. The token lives in gitignored `data/`, but `data/` is included in backups/snapshots — protect backup and offsite access like credentials. See the [DCI feature wiki](https://wiki.erdbeerbaerlp.de/dcintegration:root) and [webhook FAQ](https://wiki.erdbeerbaerlp.de/dcintegration:faq).

**Offsite backups** (optional but recommended): drop an `rclone.conf` next to the compose file (gitignored), set `RCLONE_DEST` in `.env` (e.g. `b2:zapeg-backups/world`), then `docker compose --profile offsite up -d`.

**LLM matrix**: the default stack never uses these values. The `npc` profile needs `LLM_BASE_URL`, `LLM_MODEL` and normally `LLM_API_KEY`. Heraldor with `HERALDOR_LLM=false` uses none of them; with `HERALDOR_LLM=true` it needs the same endpoint/model and normally the key. A key may be blank only for an explicitly configured compatible local endpoint that accepts keyless calls.

**Muhtar NPC prototype** (optional; not part of the default stack): once the town exists, an OP places the body with Easy NPC, writes `NPC_POS="x y z"` into `.env`, then runs `docker compose --profile npc up -d --build`. Leave this profile off if the LLM prototype is not wanted.

**Heraldor** (optional, LLM-free by default): `docker compose --profile heraldor up -d --build`. Embedded lines work with `HERALDOR_LLM=false`; `LLM_*` is ignored. Only if Discord posts are wanted, create a **separate Heraldor-only webhook**, put its new URL directly in host `.env` as `HERALDOR_WEBHOOK`, and never commit/share it. Blank means no Discord posts. The deliberately rare defaults are exposed as `HERALDOR_CHECK_INTERVAL` and `HERALDOR_P_*`; test before changing them, especially the player-independent Discord roll. `HERALDOR_EVENTS=true` additionally enables staged midnight shadow visits. Do NOT explain Heraldor to the players.

## Verify all 21 additions loaded (once, after first boot)

```bash
ls data/mods | grep -icE 'iceandfire|citadel|immersivepetroleum|alexscaves|mowziesmobs|easy_npc|aquamirae|fragmentum|born_in_chaos|dungeonsarise|simplyswords|valkyrienskies|eureka|bettercombat|player-animation|chunky|bluemap|incendium|dcintegration'   # expect 21
```

Also save `docker compose exec mc rcon-cli forge mods` and compare it with `extras/cf-mods.txt` plus `MODRINTH_PROJECTS` in `docker-compose.yml`. A four-mod check is obsolete.

If boot fails with **"Mod IceandFire requires Citadel between …"** → in `extras/cf-mods.txt` swap the citadel line to `citadel:6002521`, then `docker compose up -d mc`. Tell Ertu.

## Access model — offline-mode, read once

`ONLINE_MODE=false` is **deliberate**: players join from any launcher, no Mojang auth. Consequences:

- Minecraft cannot prove who owns a username. Whitelist limits the names that may enter, but an attacker can still copy an allowed name; combine it with a firewall allowlist or VPN whenever possible.
- Keep `ENABLE_WHITELIST=true` if `25565` is internet-reachable. Disable it only behind a real network-level gate, and keep `OPS` empty either way.
- For administration, run `docker compose exec mc rcon-cli op <name>` from the host only when needed, then `deop <name>`. RCON port `25575` is internal and is not published.
- Player identity = username (offline UUID is derived from it). A player who changes their name is a *new* player: fresh inventory, lost claims. Tell players to pick a name once.
- Usernames in the whitelist and personal lore keys must match exactly.
- Do **not** flip online-mode later without coordinating with Ertu — switching modes mid-world changes every UUID and orphans inventories/claims.

## World protocol (agreed in the brief — please follow)

1. **First world is a throwaway** for verification: join once (ask Ertu), confirm dragon roosts exist (`/locate structure` tab-completes `iceandfire:` entries), Immersive Petroleum loaded, then assemble/move/disassemble a small Eureka ship and reconnect once. Do not enable VS's experimental air-pocket/connectivity system.
2. **Seed audition** (pack uses Terralith + Biomes O' Plenty — vanilla seed lists don't apply, so we pick empirically): with `WORLD_SEED` empty, each fresh world is a random candidate. Check spawn on foot + BlueMap, screenshot for the group, then `docker compose stop mc && rm -rf data/world && docker compose start mc` for the next candidate. 2–3 rounds; when the group picks, note the seed (shown in BlueMap / `/seed`) and set `WORLD_SEED` in `.env`.
3. Reset for the real world:
   ```bash
   docker compose stop mc
   scripts/snapshot.sh pre-real-world
   rm -rf data/world
   docker compose start mc
   ```
4. On the real world, apply the agreed gamerules (once): `scripts/apply-gamerules.sh` (values: [TUNING.md](TUNING.md))
5. Pregen the real world (run overnight; heavy CPU is expected):
   ```bash
   scripts/pregen.sh 6000
   ```

## Rules of operation

- **Before ANY change** (mod/config/pack version): `scripts/snapshot.sh <label>` → `./snapshots/`
- **Updates arrive via git** — never edit pins locally:
  ```bash
  git pull && scripts/snapshot.sh pre-update && docker compose up -d mc
  ```
- Backups: automatic daily tar of world+configs → `./backups/`, pruned after 14 days. **Test one restore** in week 1 (stop stack, extract tarball over `data/`, start).
- Console: `docker compose exec mc rcon-cli` (e.g. `whitelist add <name>`, `op <name>`).
- Performance complaints: pack ships Spark — `rcon-cli spark profiler start` / `stop`; send results to Ertu. Don't add mods to "fix" performance.

## Don'ts

- Don't exceed `MEMORY: 12G` — GC degrades above that on this pack.
- Don't update the ATM9 version or any mod yourself — that's coordinated with client updates. Players need the same 17 client+server additions; Chunky, BlueMap, Incendium and Discord Integration stay server-only.
- Don't delete `snapshots/` or `backups/` to free space without checking with Ertu.
