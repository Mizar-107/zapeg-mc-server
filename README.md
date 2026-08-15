# ZapeG — ATM9+ server

Self-hosted server for the custom pack: **ATM9 1.1.1 base + Ice and Fire, Citadel, Immersive Petroleum (+ Chunky server-side)**. Fully declarative — the container resolves the pack and every extra mod from pins at start; no manual jar handling. This README is the full reference; start with [HOSTING.md](HOSTING.md) if you're the operator. Decisions: [docs/atm9-modpack-project-brief.md](docs/atm9-modpack-project-brief.md) · change playbook: [UPDATING.md](UPDATING.md) · player install: [docs/PLAYER-SETUP-TR.md](docs/PLAYER-SETUP-TR.md).

## Version pins (verified 2026-08-15)

| Component | Version | Pin | Notes |
|---|---|---|---|
| ATM9 | 1.1.1 (2025-10-12) | CF file `7097953` | Pins **Forge 47.4.0** via its manifest; server files `7097957` (itzg wants the client file — it resolves the server pack itself) |
| Ice and Fire | 2.1.13-1.20.1-beta-5 | CF file `5633453` | Still the newest official 1.20.1 build; beta-5 fixed Citadel 2.6.x compat |
| Citadel | 2.6.3-1.20.1 (2026-01) | CF file `7476570` | I&F dep. Fallback if version-range error: 2.6.1 = `6002521` |
| Immersive Petroleum | 4.3.1-36b (2026-07) | CF file `8499079` | Forge build, actively maintained |
| Chunky | 1.3.146 | Modrinth (`MODRINTH_PROJECTS`) | No 1.20.1 Forge build exists on CurseForge |
| Alex's Caves | 2.0.2 (2024-10) | CF file `5848216` | Client+server; shares Citadel dep |
| Mowzie's Mobs | 1.8.2 (2026-03) | CF file `7815705` | Client+server; GeckoLib already in ATM9 |
| BlueMap | 5.3-forge-1.20 | Modrinth (`MODRINTH_PROJECTS`) | Server-only web map on `:8100`. Pinned to 5.3 — 5.12+ needs Java 21, we're on 17 |
| Discord Integration | 3.0.7.1 (2024-05) | CF file `5332465` | Server-only; token wired post-boot (HOSTING) |

Confirmed **already in ATM9 1.1.x** (435-mod list from the pack repo): Twilight Forest 4.3.2508 (dropped from our manual adds), Spark, FerriteCore, ModernFix, Embeddium/Oculus. Confirmed **not in pack**: the four above, Alex's Caves, Mowzie's Mobs.

## Quickstart

```bash
cp .env.example .env        # set RCON_PASSWORD; optionally WHITELIST/OPS, CF_API_KEY
docker compose up -d mc
docker compose logs -f mc   # first boot: ~1.1 GB pack + 4 mods download, Forge install — expect 5–15 min
```

Healthy = `[Server thread/INFO]: Done (…)! For help, type "help"`. The backup sidecar starts once `mc` reports healthy.

Whitelist/ops if not set via `.env`:

```bash
docker compose exec mc rcon-cli whitelist add <name>
docker compose exec mc rcon-cli op <name>
```

## First-session checklist (brief §9)

1. **Phase 1 — base boot:** quickstart above, then save the baseline mod list:
   `docker compose exec mc rcon-cli forge mods > docs/modlist-$(date +%F).txt` (create `docs/` first, or just redirect anywhere and commit it).
2. **Phase 2 — extras verification:** boot log must show the 4 extra mods loading. In a **throwaway world** confirm worldgen: dragon roosts/caves spawn (`/locate structure iceandfire:...` tab-completes), IP oil reservoirs (`/ie` … or just JEI the pumpjack). Then `scripts/snapshot.sh pre-real-world`, delete `data/world`, restart for the real world.
3. **Phase 3 — world prep:** `scripts/pregen.sh 6000` (5–8k per brief; hours of CPU, fine overnight). Set gamerules/difficulty to taste.
4. **Phase 4 — tuning:** `scripts/iceandfire-config-check.sh` → set dragon griefing low/none; endgame policy stays at level 1 (social rule), level-3 hooks ready in `overrides/kubejs/server_scripts/custom_endgame_nerfs.js` → `scripts/apply-overrides.sh`.
5. **Phase 5 — clients:** see below.
6. **Phase 6 — playtest matrix:** Create contraption, IE multiblock, Mekanism fission, MineColonies town hall, Ars spell, Ad Astra rocket, one Cataclysm boss, one dragon.

## Clients (Phase 5)

Every player runs **ATM9 1.1.1 + the same 3 content jars** (Ice and Fire `5633453`, Citadel `7476570`, Immersive Petroleum `8499079`). Chunky is server-side only — clients skip it.

Interim (day 1): install ATM9 1.1.1 via CurseForge app, drop the 3 jars into the profile's `mods/`. Proper path: CurseForge profile export **with overrides**, or a packwiz repo (git-friendly, agent-maintainable) — planned as its own step.

## Backups

- **Automated:** sidecar tars `/data` daily (`BACKUP_INTERVAL=24h`), prunes after 14 days → `./backups/`. Jars/caches excluded — they re-resolve from pins; world + configs are the real state.
- **Manual (mandatory before ANY change):** `scripts/snapshot.sh <label>` → `./snapshots/`. Works hot (flushes saves via rcon) or cold.
- **Restore:** stop stack, extract the tarball over `data/`, start. Test one restore before go-live.

## Upgrades / changes — the ritual

1. `scripts/snapshot.sh pre-<change>`
2. Edit the pin (`CF_FILE_ID` for pack bump, `extras/cf-mods.txt` for mod bumps)
3. `docker compose up -d mc` (recreates, re-resolves)
4. Watch boot log; on failure: restore snapshot, revert pin
5. Ship matching client update **before** players reconnect — mod sets must stay identical

## Troubleshooting

- **"requires Citadel between X and Y" at boot** (from Ice and Fire OR Alex's Caves) → swap the Citadel line in `extras/cf-mods.txt` to `citadel:6002521` (2.6.1 — satisfies both I&F beta-5 and AC 2.0.2), recreate. Note: the infamous I&F↔AC Citadel deadlock ([Citadel #215](https://github.com/AlexModGuy/Citadel/issues/215)) applies to I&F *beta-4*; beta-5 was released to fix exactly that.
- **CurseForge download throttling/failures** → set your own `CF_API_KEY` in `.env` (console.curseforge.com).
- **OOM / long GC pauses** → `MEMORY` stays ≤ 12G (more is worse on this pack); check host isn't overcommitted.
- **Slow ticks on exploration** → pregen wider (`scripts/pregen.sh 8000`); Spark is already in the pack: `/spark profiler start` before adding any "performance" mods.
- **Flight kicks** → already mitigated (`ALLOW_FLIGHT=true`, watchdog off, secure profile off).

## Layout

```
docker-compose.yml     mc (itzg AUTO_CURSEFORGE, pinned) + backup sidecar
extras/cf-mods.txt     the 3 extra CurseForge mods, pinned by file ID
overrides/             mirrors data/ — quest chapters, kubejs scripts, server icon
scripts/               snapshot.sh · pregen.sh · apply-overrides.sh · apply-gamerules.sh · iceandfire-config-check.sh
metrics/               opt-in Grafana/Prometheus stack (--profile metrics) — see metrics/README.md
tools/                 Build-ClientZip.ps1 (Ertu-side: builds the Yol B instance zip)
HOSTING.md             day-0 guide for the operator
UPDATING.md            change-safety matrix + release ritual
ROADMAP.md             phased plan (launch → lore era → LLM NPCs)
TUNING.md              gamerule/config decisions (defaults + group votes)
CHANGELOG.md           per-release notes (doubles as player announcements)
docs/                  project brief · PLAYER-SETUP-TR (oyuncu kurulumu)
client/                optional client branding (PackMenu logo) — cosmetic
data/ backups/ snapshots/   runtime state (gitignored)
```
