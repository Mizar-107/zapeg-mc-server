# ZapeG — ATM9+ server

Self-hosted server for the custom pack: **ATM9 1.1.1 base + 26 additions** (22 client+server, 4 server-only). The server resolves the external pins and installs the reviewed ZapeG Citizens build; players receive one generated ZapeG patch instead of downloading jars individually. This README is the full reference; start with [HOSTING.md](HOSTING.md) if you're the operator. Decisions: [docs/atm9-modpack-project-brief.md](docs/atm9-modpack-project-brief.md) · change playbook: [UPDATING.md](UPDATING.md) · player install: [docs/PLAYER-SETUP-TR.md](docs/PLAYER-SETUP-TR.md) · reversible Muhtar guide: [docs/MUHTAR-QUEST-GUIDE-TR.md](docs/MUHTAR-QUEST-GUIDE-TR.md).

## Version pins (verified 2026-08-17)

| Component | Version | Pin | Notes |
|---|---|---|---|
| ATM9 | 1.1.1 (2025-10-12) | CF file `7097953` | Manifest pins Forge 47.4.0; ZapeG overrides the server and clients to **Forge 47.4.10** for current additions. Server file `7097957`; itzg wants the client file and resolves the server pack itself |
| Ice and Fire | 2.1.13-1.20.1-beta-5 | CF file `5633453` | Still the newest official 1.20.1 build; beta-5 fixed Citadel 2.6.x compat |
| Citadel | 2.6.3-1.20.1 (2026-01) | CF file `7476570` | I&F dep. Fallback if version-range error: 2.6.1 = `6002521` |
| Immersive Petroleum | 4.3.1-36b (2026-07) | CF file `8499079` | Forge build, actively maintained |
| Immersive Vehicles | 24.0.0 (2026-04) | CF file `7926604` | Client+server core; this release fixes the Ad Astra startup crash. Requires Forge ≥47.1.47; ZapeG's 47.4.10 satisfies it |
| MTS Official Pack | V29 (2026-04) | CF file `7933733` | Client+server official cars, trucks, planes, helicopters and tanks; requires Immersive Vehicles |
| MTS Official Automobile Pack | V3 (2026-04) | CF file `7933540` | Client+server official car-focused addon; requires both Immersive Vehicles and MTS Official Pack V29 |
| Aleki's Nifty Ships | 1.0.14 (2024-12) | CF file `5963449` | Client+server MIT core, owner-approved as experimental age-of-sail content. Known unload/mooring/render defects remain a promotion gate; the incompatible official BOP addon is deliberately excluded |
| Chunky | 1.3.146 | Modrinth (`MODRINTH_PROJECTS`) | No 1.20.1 Forge build exists on CurseForge |
| Alex's Caves | 2.0.2 (2024-10) | CF file `5848216` | Client+server; shares Citadel dep |
| Mowzie's Mobs | 1.8.2 (2026-03) | CF file `7815705` | Client+server; GeckoLib already in ATM9 |
| Easy NPC | 7.7.7 (2026-08) | CF file `8644040` | Client+server; retained for lore and quest NPCs |
| Aquamirae | 7.1.10 (2026-08) | CF file `8558369` | Client+server; ocean horror + Cornelia boss |
| Born in Chaos | 1.7.5 (2026-04) | CF file `7917933` | Client+server; night horror mobs ("Heraldor'un orduları") |
| When Dungeons Arise | 2.1.58 | ATM9 manifest, CF file `4983862` | **Already in ATM9**; mega-dungeons, never add a second jar |
| Simply Swords | 1.56.0 | CF file `5639538` | Client+server; unique weapons |
| Better Combat | 1.9.0+1.20.1 | Modrinth pin | Client+server; melee overhaul (ATM9 already supplies its exact playerAnimator dependency) |
| playerAnimator | 1.0.2-rc1+1.20 | ATM9 manifest, CF file `4587214` | **Already in ATM9**; Better Combat dependency, never add a second jar |
| Valkyrien Skies | 2.4.11 | CF file `7906689` | Client+server physics engine; declares Forge ≥47.2 and optional Create ≥6.0.6 |
| Eureka | 1.6.3 | CF file `7979379` | Client+server ship/helm addon; requires VS ≥2.4.10. Kotlin for Forge already ships in ATM9 |
| Numen AI | 0.1.1 | CF file `8551640` | Client+server; managed citizen body and tool engine; embeds its matching Numen API |
| CC:Tweaked | 1.116.1 | Modrinth pin | Client+server re-pin; ATM9's CurseForge resolution does not reliably provide the version required by the Numen/Advanced Peripherals integration |
| ZapeG Citizens | 0.3.0 | owned jar + reviewed SHA-256 lock | Client+server controller for player-owned workers and persistent server-owned lore citizens; all 32 server-executable Numen tools enabled; installed from `overrides/mods`, not represented as CurseForge content |
| Incendium | 5.3.1 | Modrinth pin | **Server-only**; nether overhaul (Stardust, pairs with pack's Terralith) |
| BlueMap | 5.3-forge-1.20 | Modrinth (`MODRINTH_PROJECTS`) | Server-only web map on `:8100`. Pinned to 5.3 — 5.12+ needs Java 21, we're on 17 |
| Discord Integration | 3.0.7.1 (2024-05) | CF file `5332465` | Server-only; token wired post-boot (HOSTING) |

Confirmed **already in ATM9 1.1.1** (435-mod manifest): When Dungeons Arise 2.1.58, playerAnimator 1.0.2-rc1+1.20, Twilight Forest 4.3.2508, Spark, FerriteCore, ModernFix, Embeddium/Oculus and Kotlin for Forge. The first two were removed from ZapeG's manual declarations after a real boot exposed the duplicate WDA mod ID. The 25 external ZapeG additions are pinned by exact CurseForge file IDs, `MODRINTH_PROJECTS`, or the reviewed CC:Tweaked override and SHA-256 inventory locks; ZapeG Citizens is the twenty-sixth, owned addition and is likewise verified by exact filename plus SHA-256 locks.

## Quickstart

```bash
cp .env.example .env        # optional settings; default mc + backup has no required env value
docker compose up -d        # starts the default stack: mc + backup
docker compose logs -f mc   # first boot: pack + 26 additions + Forge install — expect 5–15+ min
```

Healthy = `[Server thread/INFO]: Done (…)! For help, type "help"`. The backup sidecar starts once `mc` reports healthy.

The commands above load the Citizens Forge mods but deliberately leave their
shared LLM controller disabled. For the planned launch, the host must complete
[the one-time Citizens setup](docs/CITIZENS-HOST-SETUP.md) and start the
`citizens` profile before players are invited. One host-side Ollama key serves
all player- and server-owned citizens; no key or separate app is distributed to players.

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
2. **Phase 2 — extras verification:** boot log must show all **26 additions** loading; compare external downloads against `extras/cf-mods.txt` and `MODRINTH_PROJECTS`, then confirm the owned `zapeg-citizens` jar from `overrides/mods`. In a **throwaway world** confirm worldgen: dragon roosts/caves spawn (`/locate structure iceandfire:...` tab-completes), IP oil reservoirs (`/ie` … or JEI the pumpjack), and the added content mods appear in `forge mods`. Spawn one vehicle from each official MTS pack; fuel and drive them over normal terrain, unload/reload the chunk, restart, reconnect and confirm they persist. Separately assemble/move/disassemble a small Eureka ship. Build and cargo-test one Nifty sloop, anchor and dual-lead moor it, travel 16+ chunks away, return, restart and reconnect; repeat with Entity Culling and shaders on/off. Never place one vehicle/ship physics system on another.
3. **Phase 3 — custom layer + generated config pass, before the real world:** apply `scripts/apply-overrides.sh`, restart, and verify the three custom quest pages (**ZapeG — Yol Haritası**, **ZapeG — Kilometre Taşları**, **ZapeG**). Achievement tasks must have no clickable checkmark; run the two-client checks in `docs/QUEST-VALIDATION-TR.md`. Place the tracked, stateless Muhtar only after choosing his town-square coordinates, then run the non-OP button matrix in `docs/MUHTAR-QUEST-GUIDE-TR.md`; deleting him never alters quest progress. Then run `scripts/iceandfire-config-check.sh`; edit the surfaced config so Ice and Fire silver ore generation is **off** and dragon griefing is low/none, snapshot, then restart. Doing this after pregen would leave duplicate silver in every generated chunk. Endgame policy stays level 1 (social); level-3 hooks remain dormant.
4. **Phase 4 — seed audition + world prep:** audition 2–3 fresh worlds as described in HOSTING, let the group choose, set `WORLD_SEED`, snapshot, and only then reset for the real world. Apply gamerules and run `scripts/pregen.sh 6000` (hours of CPU, fine overnight).
5. **Phase 5 — clients:** see below.
6. **Phase 6 — playtest matrix:** Create contraption, IE multiblock, Mekanism fission, MineColonies town hall, Ars spell, Ad Astra rocket, one vehicle from each official MTS pack, one Nifty sloop persistence cycle, one Cataclysm boss, one dragon.

## Clients (Phase 5)

Every player runs **ATM9 1.1.1 on Forge 47.4.10 + the same 22 client additions**. Chunky, BlueMap, Incendium and Discord Integration are server-only.

Do not ask players to download jars individually. The **pack maintainer**, once,
creates the builder source profile: install ATM9 1.1.1 in CurseForge, select Forge
47.4.10, add every client CurseForge entry in `extras/cf-mods.txt` (all except the
server-only Discord Integration entry) through the app so its exact file ID lands
in `minecraftinstance.json`, then place the exact Better Combat and CC:Tweaked
1.116.1 Modrinth jars in `mods/`. Remove ATM9's older CC:Tweaked copy; do not add
WDA or playerAnimator because ATM9 supplies both. Launch that profile
once. Players never do this.

The reviewed 22-jar hash lock is tracked at `tools/client-extra-mods.lock`; it includes the repo-owned ZapeG Citizens jar without pretending that jar came from CurseForge.
After the server's pins pass the throwaway-world test, build the profile-root patch:

```powershell
.\tools\Build-ClientZip.ps1 -PatchOnly
```

Only regenerate a lock with `-WriteInventoryLock` after an intentional pin
change, as part of the snapshot/test/review ritual; normal builds consume the
tracked lock and fail closed on any unexpected jar or hash.

Share `ZapeG-Kurulum-Yamasi-ATM9-1.1.1-<date>.zip` privately. Licensed players install ATM9 1.1.1, set the profile's modloader to Forge 47.4.10, open the profile folder, remove the old CC:Tweaked and Citizens jar families as instructed in `INSTALL-TR.txt`, and extract this one zip there. The patch contains `mods/`, the shader and Entity Culling compatibility settings, PackMenu branding, `INSTALL-TR.txt` and a SHA-256 build manifest; it does not overwrite the player's `options.txt`. The builder requires the exact 22 pinned jar filenames and rejects missing, stale or duplicate versions. Nifty Ships is MIT; because its published jar omits the notice file, generated builds include the author's official text at `licenses/alekiships-LICENSE.txt`. Immersive Vehicles and its official packs are all-rights-reserved CurseForge projects: prefer source installation through CurseForge, keep generated artifacts private, never commit their jars, and obtain author permission before any public redistribution.

For offline players, run the tool without `-PatchOnly`; it consumes the tracked,
reviewed `tools/client-mods.lock`. Exact filenames, CurseForge metadata IDs and
SHA-256 locks stop stale/modified jars and later unreviewed additions. The output
is an isolated Forge-profile **game-directory payload**, not a launcher or Forge
installer. Player-facing steps: [docs/PLAYER-SETUP-TR.md](docs/PLAYER-SETUP-TR.md).

## Backups

- **Automated:** sidecar tars `/data` daily (`BACKUP_INTERVAL=24h`), prunes after 14 days → `./backups/`. Jars/caches excluded — they re-resolve from pins; world + configs are the real state.
- **Manual (mandatory before ANY change):** `scripts/snapshot.sh <label>` → `./snapshots/`. Works hot (flushes saves via RCON) or cold; it briefly stops/restarts the automatic backup service to prevent overlapping save coordination. Avoid the daily archive window when practical.
- **Restore:** stop the stack (including optional profiles), extract the tarball
  over `data/`, and keep both Heraldor services stopped. If the archive contains
  `data/heraldor/backup/heraldor.sqlite3`, promote that consistent copy with
  `docker compose --profile heraldor run --rm --no-deps heraldor python heraldor.py admin restore-snapshot`
  before starting the Director or voice profile; then start the required services. See
  [the Heraldor runbook](docs/HERALDOR-RUNBOOK.md#restore-from-a-normal-server-archive).
  Test one complete restore before go-live.

## Upgrades / changes — the ritual

1. `scripts/snapshot.sh pre-<change>`
2. Edit the pin (`CF_FILE_ID` for pack bump, `extras/cf-mods.txt` for mod bumps)
3. `docker compose up -d mc` (recreates, re-resolves)
4. Watch boot log; on failure: restore snapshot, revert pin
5. Ship matching client update **before** players reconnect — clients need the same 22 client+server additions; the four server-only additions never go in a client

## Troubleshooting

- **"requires Citadel between X and Y" at boot** (from Ice and Fire OR Alex's Caves) → swap the Citadel line in `extras/cf-mods.txt` to `citadel:6002521` (2.6.1 — satisfies both I&F beta-5 and AC 2.0.2), recreate. Note: the infamous I&F↔AC Citadel deadlock ([Citadel #215](https://github.com/AlexModGuy/Citadel/issues/215)) applies to I&F *beta-4*; beta-5 was released to fix exactly that.
- **CurseForge download throttling/failures** → set your own `CF_API_KEY` in `.env` (console.curseforge.com).
- **OOM / long GC pauses** → `MEMORY` stays ≤ 12G (more is worse on this pack); check host isn't overcommitted.
- **Slow ticks on exploration** → pregen wider (`scripts/pregen.sh 8000`); Spark is already in the pack: `/spark profiler start` before adding any "performance" mods.
- **Flight kicks** → already mitigated (`ALLOW_FLIGHT=true`, watchdog off, secure profile off).
- **IV vehicle disappears while nearby** → reapply the current patch and confirm `config/entityculling.json` lists `mts:builder_existing`, `mts:builder_rendering` and `mts:builder_seat` under `entityWhitelist`.
- **IV dashboard/fuel text is invisible with shaders** → open the in-game IV config (`P`) and set Rendering → `LightsTransp=true`; toggling shaders with **K** is the quickest diagnosis.
- **IV vehicle falls through/misbehaves on a ship or contraption** → move it to normal terrain. Collision with moving Eureka/VS ships and Create contraptions is not supported reliably upstream.
- **Nifty sloop drifts, loses mooring/anchor interaction or disappears** → this core is explicitly experimental and those 1.0.14 unload/render defects are known upstream. Relog, compare Entity Culling and shaders on/off, record coordinates, and keep irreplaceable cargo off the ship until the copied-world persistence gate passes. Never carry it on Eureka/VS, Create or IV moving constructs.

## Layout

```
docker-compose.yml     mc (itzg AUTO_CURSEFORGE) + backup; optional service profiles
extras/cf-mods.txt     20 CurseForge additions pinned by file ID (19 client, 1 server-only)
overrides/             mirrors data/ — quest chapters, kubejs scripts, server icon, owned Citizens jar
scripts/               snapshot.sh · pregen.sh · apply-overrides.sh · apply-gamerules.sh · muhtar-npc.sh · iceandfire-config-check.sh
metrics/               opt-in Grafana/Prometheus stack (--profile metrics) — see metrics/README.md
tools/                 Build-ClientZip.ps1 (single licensed-player patch + offline payload)
HOSTING.md             day-0 guide for the operator
UPDATING.md            change-safety matrix + release ritual
ROADMAP.md             phased plan (launch → lore era → LLM NPCs)
TUNING.md              gamerule/config decisions (defaults + group votes)
CHANGELOG.md           per-release notes (doubles as player announcements)
docs/                  project brief · PLAYER-SETUP-TR (oyuncu kurulumu)
client/                client defaults/branding plus required third-party license notices
data/ backups/ snapshots/   runtime state (gitignored)
```
