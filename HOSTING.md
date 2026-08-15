# HOSTING — day-0 guide for the server operator

You're hosting **ZapeG** — a private modded Minecraft server for 4–8 players: **All the Mods 9 v1.1.1 (Forge, MC 1.20.1) + 4 pinned extra mods**. Everything is declarative — the container downloads the pack and mods itself from the pins in this repo. You never handle jars manually. Full reference: [README.md](README.md). Decisions/background: [docs/atm9-modpack-project-brief.md](docs/atm9-modpack-project-brief.md).

## Requirements

- Linux host, Docker Engine 24+ with the compose plugin (`docker compose version` works)
- **16 GB+ RAM free** for this stack (12 GB heap + JVM/OS overhead) — 32 GB host ideal
- 4+ decent cores (worldgen/pregen is CPU-hungry), SSD strongly recommended
- ~40 GB disk (pack ~10 GB installed, world grows, 14 days of backups)
- **TCP 25565** open/forwarded to the host; give Ertu the public IP (or set up DDNS)

## Deploy (~30 min, mostly download)

```bash
git clone <REPO_URL> seri-atm9-server && cd seri-atm9-server
cp .env.example .env
# edit .env: RCON_PASSWORD=<long random>; WHITELIST/OPS = comma-separated usernames from Ertu
docker compose up -d mc
docker compose logs -f mc     # first boot: ~1.1 GB download + Forge install, 5–15 min
```

Ready when the log shows `Done (…)! For help, type "help"`. The backup sidecar starts automatically once `mc` is healthy.

Then apply the repo's custom layer (quest chapter, starter-kit script, server icon) and restart:

```bash
scripts/apply-overrides.sh && docker compose restart mc
```

## Verify the 4 extra mods loaded (once, after first boot)

```bash
ls data/mods | grep -icE 'iceandfire|citadel|immersivepetroleum|chunky'   # expect 4
```

If boot fails with **"Mod IceandFire requires Citadel between …"** → in `extras/cf-mods.txt` swap the citadel line to `citadel:6002521`, then `docker compose up -d mc`. Tell Ertu.

## Access model — offline-mode, read once

`ONLINE_MODE=false` is **deliberate**: players join from any launcher, no Mojang auth. Consequences:

- The **whitelist is the only gate** — keep it enforced, and don't post the IP anywhere public.
- Player identity = username (offline UUID is derived from it). A player who changes their name is a *new* player: fresh inventory, lost claims. Tell players to pick a name once.
- Usernames on the whitelist must match exactly.
- Do **not** flip online-mode later without coordinating with Ertu — switching modes mid-world changes every UUID and orphans inventories/claims.

## World protocol (agreed in the brief — please follow)

1. **First world is a throwaway** for verification: join once (ask Ertu), confirm dragon roosts exist (`/locate structure` tab-completes `iceandfire:` entries) and Immersive Petroleum loaded.
2. Reset for the real world:
   ```bash
   docker compose stop mc
   scripts/snapshot.sh pre-real-world
   rm -rf data/world
   docker compose start mc
   ```
3. On the real world, apply the agreed gamerules (once): `scripts/apply-gamerules.sh` (values: [TUNING.md](TUNING.md))
4. Pregen the real world (run overnight; heavy CPU is expected):
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
- Don't update the ATM9 version or any mod yourself — that's coordinated with client updates (players must match the server mod set exactly).
- Don't delete `snapshots/` or `backups/` to free space without checking with Ertu.
