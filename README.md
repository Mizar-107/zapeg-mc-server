# ZapeG — ATM9+ server

Self-hosted server for the custom pack: **ATM9 1.1.1 base + 21 additions** (17 client+server, 4 server-only). The container resolves the pack and additions at start; players receive one generated ZapeG patch instead of downloading jars individually. This README is the full reference; start with [HOSTING.md](HOSTING.md) if you're the operator. Decisions: [docs/atm9-modpack-project-brief.md](docs/atm9-modpack-project-brief.md) · change playbook: [UPDATING.md](UPDATING.md) · player install: [docs/PLAYER-SETUP-TR.md](docs/PLAYER-SETUP-TR.md).

## Version pins (verified 2026-08-16)

| Component | Version | Pin | Notes |
|---|---|---|---|
| ATM9 | 1.1.1 (2025-10-12) | CF file `7097953` | Manifest pins Forge 47.4.0; ZapeG overrides the server and clients to **Forge 47.4.10** for current additions. Server file `7097957`; itzg wants the client file and resolves the server pack itself |
| Ice and Fire | 2.1.13-1.20.1-beta-5 | CF file `5633453` | Still the newest official 1.20.1 build; beta-5 fixed Citadel 2.6.x compat |
| Citadel | 2.6.3-1.20.1 (2026-01) | CF file `7476570` | I&F dep. Fallback if version-range error: 2.6.1 = `6002521` |
| Immersive Petroleum | 4.3.1-36b (2026-07) | CF file `8499079` | Forge build, actively maintained |
| Chunky | 1.3.146 | Modrinth (`MODRINTH_PROJECTS`) | No 1.20.1 Forge build exists on CurseForge |
| Alex's Caves | 2.0.2 (2024-10) | CF file `5848216` | Client+server; shares Citadel dep |
| Mowzie's Mobs | 1.8.2 (2026-03) | CF file `7815705` | Client+server; GeckoLib already in ATM9 |
| Easy NPC | 7.7.7 (2026-08) | CF file `8644040` | Client+server; Muhtar's physical body |
| Aquamirae | 7.1.10 (2026-08) | CF file `8558369` | Client+server; ocean horror + Cornelia boss |
| Born in Chaos | 1.7.5 (2026-04) | CF file `7917933` | Client+server; night horror mobs ("Heraldor'un orduları") |
| When Dungeons Arise | 2.1.57 (final 1.20.1) | CF file `4798432` | Client+server; mega-dungeons |
| Simply Swords | 1.56.0 | CF file `5639538` | Client+server; unique weapons |
| Better Combat | 1.9.0+1.20.1 | Modrinth pin | Client+server; melee overhaul (needs playerAnimator; cloth-config already in pack) |
| playerAnimator | 1.0.2-rc1+1.20 | Modrinth pin | Client+server; Better Combat dep |
| Valkyrien Skies | 2.4.11 | CF file `7906689` | Client+server physics engine; declares Forge ≥47.2 and optional Create ≥6.0.6 |
| Eureka | 1.6.3 | CF file `7979379` | Client+server ship/helm addon; requires VS ≥2.4.10. Kotlin for Forge already ships in ATM9 |
| Incendium | 5.3.1 | Modrinth pin | **Server-only**; nether overhaul (Stardust, pairs with pack's Terralith) |
| BlueMap | 5.3-forge-1.20 | Modrinth (`MODRINTH_PROJECTS`) | Server-only web map on `:8100`. Pinned to 5.3 — 5.12+ needs Java 21, we're on 17 |
| Discord Integration | 3.0.7.1 (2024-05) | CF file `5332465` | Server-only; token wired post-boot (HOSTING) |

Confirmed **already in ATM9 1.1.x** (435-mod list/manifest): Twilight Forest 4.3.2508 (dropped from our manual adds), Spark, FerriteCore, ModernFix, Embeddium/Oculus and Kotlin for Forge. All 21 ZapeG additions are declared by exact CurseForge file IDs or the `MODRINTH_PROJECTS` list in `docker-compose.yml`.

## Quickstart

```bash
cp .env.example .env        # generate RCON_PASSWORD; keep whitelist on unless 25565 is network-gated
docker compose up -d        # starts the default stack: mc + backup
docker compose logs -f mc   # first boot: pack + 21 additions + Forge install — expect 5–15+ min
```

Healthy = `[Server thread/INFO]: Done (…)! For help, type "help"`. The backup sidecar starts once `mc` reports healthy.

Whitelist and temporary admin access from the host:

```bash
docker compose exec mc rcon-cli whitelist add <name>
docker compose exec mc rcon-cli op <name>
# do the admin task, then remove spoofable persistent OP access:
docker compose exec mc rcon-cli deop <name>
```

## First-session checklist (brief §9)

1. **Phase 1 — base boot:** quickstart above, then save the baseline mod list:
   `docker compose exec mc rcon-cli forge mods > docs/modlist-$(date +%F).txt` (create `docs/` first, or just redirect anywhere and commit it).
2. **Phase 2 — extras verification:** boot log must show all **21 additions** resolving; compare against `extras/cf-mods.txt` and `MODRINTH_PROJECTS`. In a **throwaway world** confirm worldgen: dragon roosts/caves spawn (`/locate structure iceandfire:...` tab-completes), IP oil reservoirs (`/ie` … or JEI the pumpjack), the added content mods appear in `forge mods`, and a small Eureka ship can assemble, move, disassemble and survive a reconnect.
3. **Phase 3 — seed audition + world prep:** audition 2–3 fresh worlds as described in HOSTING, let the group choose, set `WORLD_SEED`, snapshot, and only then reset for the real world. Apply gamerules and run `scripts/pregen.sh 6000` (hours of CPU, fine overnight).
4. **Phase 4 — tuning:** `scripts/iceandfire-config-check.sh` → set dragon griefing low/none; endgame policy stays at level 1 (social rule), level-3 hooks ready in `overrides/kubejs/server_scripts/custom_endgame_nerfs.js` → `scripts/apply-overrides.sh`.
5. **Phase 5 — clients:** see below.
6. **Phase 6 — playtest matrix:** Create contraption, IE multiblock, Mekanism fission, MineColonies town hall, Ars spell, Ad Astra rocket, one Cataclysm boss, one dragon.

## Clients (Phase 5)

Every player runs **ATM9 1.1.1 on Forge 47.4.10 + the same 17 client additions**. Chunky, BlueMap, Incendium and Discord Integration are server-only.

Do not ask players to download jars individually. On the first verified build, create and review the 17-jar hash lock, commit it, then build the profile-root patch:

```powershell
.\tools\Build-ClientZip.ps1 -PatchOnly -WriteInventoryLock
# review tools/client-extra-mods.lock, then add it to the repo
.\tools\Build-ClientZip.ps1 -PatchOnly
```

Share `ZapeG-Kurulum-Yamasi-ATM9-1.1.1-<date>.zip`. Licensed players install ATM9 1.1.1, set the profile's modloader to Forge 47.4.10, open the profile folder and extract this one zip there. The patch contains `mods/`, the shader setting, PackMenu branding, `INSTALL-TR.txt` and a SHA-256 build manifest; it does not overwrite the player's `options.txt`. The builder requires the exact 17 pinned jar filenames and rejects missing, stale or duplicate versions.

For offline players, first run `Build-ClientZip.ps1 -WriteInventoryLock`, inspect `tools/client-mods.lock` for personal/server-only jars, and commit the reviewed lock; then run the tool without `-PatchOnly`. Exact filenames, CurseForge metadata IDs and SHA-256 locks stop stale/modified jars and later unreviewed additions. The output is an isolated Forge-profile **game-directory payload**, not a launcher or Forge installer. Player-facing steps: [docs/PLAYER-SETUP-TR.md](docs/PLAYER-SETUP-TR.md).

## Backups

- **Automated:** sidecar tars `/data` daily (`BACKUP_INTERVAL=24h`), prunes after 14 days → `./backups/`. Jars/caches excluded — they re-resolve from pins; world + configs are the real state.
- **Manual (mandatory before ANY change):** `scripts/snapshot.sh <label>` → `./snapshots/`. Works hot (flushes saves via rcon) or cold.
- **Restore:** stop stack, extract the tarball over `data/`, start. Test one restore before go-live.

## Upgrades / changes — the ritual

1. `scripts/snapshot.sh pre-<change>`
2. Edit the pin (`CF_FILE_ID` for pack bump, `extras/cf-mods.txt` for mod bumps)
3. `docker compose up -d mc` (recreates, re-resolves)
4. Watch boot log; on failure: restore snapshot, revert pin
5. Ship matching client update **before** players reconnect — clients need the same 17 client+server additions; the four server-only additions never go in a client

## Troubleshooting

- **"requires Citadel between X and Y" at boot** (from Ice and Fire OR Alex's Caves) → swap the Citadel line in `extras/cf-mods.txt` to `citadel:6002521` (2.6.1 — satisfies both I&F beta-5 and AC 2.0.2), recreate. Note: the infamous I&F↔AC Citadel deadlock ([Citadel #215](https://github.com/AlexModGuy/Citadel/issues/215)) applies to I&F *beta-4*; beta-5 was released to fix exactly that.
- **CurseForge download throttling/failures** → set your own `CF_API_KEY` in `.env` (console.curseforge.com).
- **OOM / long GC pauses** → `MEMORY` stays ≤ 12G (more is worse on this pack); check host isn't overcommitted.
- **Slow ticks on exploration** → pregen wider (`scripts/pregen.sh 8000`); Spark is already in the pack: `/spark profiler start` before adding any "performance" mods.
- **Flight kicks** → already mitigated (`ALLOW_FLIGHT=true`, watchdog off, secure profile off).

## Layout

```
docker-compose.yml     mc (itzg AUTO_CURSEFORGE) + backup; optional service profiles
extras/cf-mods.txt     16 CurseForge additions pinned by file ID (15 client, 1 server-only)
overrides/             mirrors data/ — quest chapters, kubejs scripts, server icon
scripts/               snapshot.sh · pregen.sh · apply-overrides.sh · apply-gamerules.sh · iceandfire-config-check.sh
metrics/               opt-in Grafana/Prometheus stack (--profile metrics) — see metrics/README.md
tools/                 Build-ClientZip.ps1 (single licensed-player patch + offline payload)
HOSTING.md             day-0 guide for the operator
UPDATING.md            change-safety matrix + release ritual
ROADMAP.md             phased plan (launch → lore era → LLM NPCs)
TUNING.md              gamerule/config decisions (defaults + group votes)
CHANGELOG.md           per-release notes (doubles as player announcements)
docs/                  project brief · PLAYER-SETUP-TR (oyuncu kurulumu)
client/                optional client branding (PackMenu logo) — cosmetic
data/ backups/ snapshots/   runtime state (gitignored)
```
