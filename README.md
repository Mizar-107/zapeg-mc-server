# ZapeG — ATM9+ server

Self-hosted server for the custom pack: **ATM9 1.1.1 base + 19 additions** (15 client+server, 4 server-only). The container resolves the pack and additions at start; players receive one generated ZapeG patch instead of downloading jars individually. This README is the full reference; start with [HOSTING.md](HOSTING.md) if you're the operator. Decisions: [docs/atm9-modpack-project-brief.md](docs/atm9-modpack-project-brief.md) · change playbook: [UPDATING.md](UPDATING.md) · player install: [docs/PLAYER-SETUP-TR.md](docs/PLAYER-SETUP-TR.md).

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
| When Dungeons Arise | 2.1.58 | ATM9 manifest, CF file `4983862` | **Already in ATM9**; mega-dungeons, never add a second jar |
| Simply Swords | 1.56.0 | CF file `5639538` | Client+server; unique weapons |
| Better Combat | 1.9.0+1.20.1 | Modrinth pin | Client+server; melee overhaul (ATM9 already supplies its exact playerAnimator dependency) |
| playerAnimator | 1.0.2-rc1+1.20 | ATM9 manifest, CF file `4587214` | **Already in ATM9**; Better Combat dependency, never add a second jar |
| Valkyrien Skies | 2.4.11 | CF file `7906689` | Client+server physics engine; declares Forge ≥47.2 and optional Create ≥6.0.6 |
| Eureka | 1.6.3 | CF file `7979379` | Client+server ship/helm addon; requires VS ≥2.4.10. Kotlin for Forge already ships in ATM9 |
| Incendium | 5.3.1 | Modrinth pin | **Server-only**; nether overhaul (Stardust, pairs with pack's Terralith) |
| BlueMap | 5.3-forge-1.20 | Modrinth (`MODRINTH_PROJECTS`) | Server-only web map on `:8100`. Pinned to 5.3 — 5.12+ needs Java 21, we're on 17 |
| Discord Integration | 3.0.7.1 (2024-05) | CF file `5332465` | Server-only; token wired post-boot (HOSTING) |

Confirmed **already in ATM9 1.1.1** (435-mod manifest): When Dungeons Arise 2.1.58, playerAnimator 1.0.2-rc1+1.20, Twilight Forest 4.3.2508, Spark, FerriteCore, ModernFix, Embeddium/Oculus and Kotlin for Forge. The first two were removed from ZapeG's manual declarations after a real boot exposed the duplicate WDA mod ID. All 19 manual ZapeG additions are declared by exact CurseForge file IDs or the `MODRINTH_PROJECTS` list in `docker-compose.yml`.

## Quickstart

```bash
cp .env.example .env        # optional settings; default mc + backup has no required env value
docker compose up -d        # starts the default stack: mc + backup
docker compose logs -f mc   # first boot: pack + 19 additions + Forge install — expect 5–15+ min
```

Healthy = `[Server thread/INFO]: Done (…)! For help, type "help"`. The backup sidecar starts once `mc` reports healthy.

The server is offline-mode, has no whitelist by group decision, and grants
`Mizar__107` OP by default. Anyone can copy that name and become OP; the owner
explicitly accepts this risk. The host can still use the private internal console:

```bash
docker compose exec mc rcon-cli list
docker compose exec mc rcon-cli <command>
```

No RCON password setup is needed: Minecraft generates it inside `data/`, and
`rcon-cli` plus the backup/Heraldor sidecars read it there. Port `25575` is never
published. Only the optional metrics profile needs an explicit shared password.

## First-session checklist (brief §9)

1. **Phase 1 — base boot:** quickstart above, then save the baseline mod list:
   `docker compose exec mc rcon-cli forge mods > docs/modlist-$(date +%F).txt` (create `docs/` first, or just redirect anywhere and commit it).
2. **Phase 2 — extras verification:** boot log must show all **19 additions** resolving; compare against `extras/cf-mods.txt` and `MODRINTH_PROJECTS`. In a **throwaway world** confirm worldgen: dragon roosts/caves spawn (`/locate structure iceandfire:...` tab-completes), IP oil reservoirs (`/ie` … or JEI the pumpjack), the added content mods appear in `forge mods`, and a small Eureka ship can assemble, move, disassemble and survive a reconnect.
3. **Phase 3 — generated config pass, before the real world:** run `scripts/iceandfire-config-check.sh`; edit the surfaced config so Ice and Fire silver ore generation is **off** and dragon griefing is low/none, snapshot, then restart. Doing this after pregen would leave duplicate silver in every generated chunk. Endgame policy stays level 1 (social); level-3 hooks remain dormant.
4. **Phase 4 — seed audition + world prep:** audition 2–3 fresh worlds as described in HOSTING, let the group choose, set `WORLD_SEED`, snapshot, and only then reset for the real world. Apply gamerules and run `scripts/pregen.sh 6000` (hours of CPU, fine overnight).
5. **Phase 5 — clients:** see below.
6. **Phase 6 — playtest matrix:** Create contraption, IE multiblock, Mekanism fission, MineColonies town hall, Ars spell, Ad Astra rocket, one Cataclysm boss, one dragon.

## Clients (Phase 5)

Every player runs **ATM9 1.1.1 on Forge 47.4.10 + the same 15 client additions**. Chunky, BlueMap, Incendium and Discord Integration are server-only.

Do not ask players to download jars individually. The **pack maintainer**, once,
creates the builder source profile: install ATM9 1.1.1 in CurseForge, select Forge
47.4.10, add every client CurseForge entry in `extras/cf-mods.txt` (all except the
server-only Discord Integration entry) through the app so its exact file ID lands
in `minecraftinstance.json`, then place the exact Better Combat Modrinth jar in
`mods/`. Do not add WDA or playerAnimator: ATM9 supplies both. Launch that profile
once. Players never do this.

The reviewed 15-jar hash lock is tracked at `tools/client-extra-mods.lock`.
After the server's pins pass the throwaway-world test, build the profile-root patch:

```powershell
.\tools\Build-ClientZip.ps1 -PatchOnly
```

Only regenerate a lock with `-WriteInventoryLock` after an intentional pin
change, as part of the snapshot/test/review ritual; normal builds consume the
tracked lock and fail closed on any unexpected jar or hash.

Share `ZapeG-Kurulum-Yamasi-ATM9-1.1.1-<date>.zip`. Licensed players install ATM9 1.1.1, set the profile's modloader to Forge 47.4.10, open the profile folder and extract this one zip there. The patch contains `mods/`, the shader setting, PackMenu branding, `INSTALL-TR.txt` and a SHA-256 build manifest; it does not overwrite the player's `options.txt`. The builder requires the exact 15 pinned jar filenames and rejects missing, stale or duplicate versions.

For offline players, run the tool without `-PatchOnly`; it consumes the tracked,
reviewed `tools/client-mods.lock`. Exact filenames, CurseForge metadata IDs and
SHA-256 locks stop stale/modified jars and later unreviewed additions. The output
is an isolated Forge-profile **game-directory payload**, not a launcher or Forge
installer. Player-facing steps: [docs/PLAYER-SETUP-TR.md](docs/PLAYER-SETUP-TR.md).

## Backups

- **Automated:** sidecar tars `/data` daily (`BACKUP_INTERVAL=24h`), prunes after 14 days → `./backups/`. Jars/caches excluded — they re-resolve from pins; world + configs are the real state.
- **Manual (mandatory before ANY change):** `scripts/snapshot.sh <label>` → `./snapshots/`. Works hot (flushes saves via RCON) or cold; it briefly stops/restarts the automatic backup service to prevent overlapping save coordination. Avoid the daily archive window when practical.
- **Restore:** stop stack, extract the tarball over `data/`, start. Test one restore before go-live.

## Upgrades / changes — the ritual

1. `scripts/snapshot.sh pre-<change>`
2. Edit the pin (`CF_FILE_ID` for pack bump, `extras/cf-mods.txt` for mod bumps)
3. `docker compose up -d mc` (recreates, re-resolves)
4. Watch boot log; on failure: restore snapshot, revert pin
5. Ship matching client update **before** players reconnect — clients need the same 15 client+server additions; the four server-only additions never go in a client

## Troubleshooting

- **"requires Citadel between X and Y" at boot** (from Ice and Fire OR Alex's Caves) → swap the Citadel line in `extras/cf-mods.txt` to `citadel:6002521` (2.6.1 — satisfies both I&F beta-5 and AC 2.0.2), recreate. Note: the infamous I&F↔AC Citadel deadlock ([Citadel #215](https://github.com/AlexModGuy/Citadel/issues/215)) applies to I&F *beta-4*; beta-5 was released to fix exactly that.
- **CurseForge download throttling/failures** → set your own `CF_API_KEY` in `.env` (console.curseforge.com).
- **OOM / long GC pauses** → `MEMORY` stays ≤ 12G (more is worse on this pack); check host isn't overcommitted.
- **Slow ticks on exploration** → pregen wider (`scripts/pregen.sh 8000`); Spark is already in the pack: `/spark profiler start` before adding any "performance" mods.
- **Flight kicks** → already mitigated (`ALLOW_FLIGHT=true`, watchdog off, secure profile off).

## Layout

```
docker-compose.yml     mc (itzg AUTO_CURSEFORGE) + backup; optional service profiles
extras/cf-mods.txt     15 CurseForge additions pinned by file ID (14 client, 1 server-only)
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
