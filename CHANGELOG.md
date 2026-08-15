# Changelog

Format per entry: what changed · world risk · what players must do.

## v0.5.0 — 2026-08-15

Metrics + scaffolds + compat verification. World risk: none. Players: nothing.

- **Metrics stack** (`--profile metrics`): dirien/minecraft-exporter (RCON + world stats, forge mode) → Prometheus (180d retention) → Grafana `:3000` (anonymous read-only), pre-provisioned "ZapeG — Sunucu" dashboard: online now/history, playtime hours, deaths, blocks mined, distance per player. TPS panel = one documented manual step (metric name varies by exporter version — `metrics/README.md`).
- **Per-player welcome lines** (`zapeg_welcome.js`): mechanism live with placeholder pools for the four players + default pool; keys must be exact Minecraft usernames.
- **tools/Build-ClientZip.ps1**: builds the Yol B (offline players) instance zip from Ertu's CurseForge profile — mods/config/kubejs only, no personal files.
- **Compat verification recorded**: IE `10.2.0-183` is the only 1.20.1 IE build and is exactly what ATM9 ships → IP 4.3.1-36b targets it by construction. The known I&F↔Alex's Caves Citadel deadlock (Citadel #215) applies to I&F beta-4 only; our beta-5 pin post-dates and fixes it. Citadel 2.6.1 fallback satisfies both mods if a range gate ever trips. Mowzie's 1.8.2's GeckoLib need is covered by the pack's 4.8.2.
- `.env.example`: `GRAFANA_PASSWORD`, `RCLONE_DEST`, `WORLD_SEED` documented.

## v0.4.0 — 2026-08-15

The presence-layer + pre-world content drop. World risk: none (pre-world — that's the point). Players: client jar list grows **3 → 5**.

- **Content (client+server): Alex's Caves 2.0.2** (`5848216`) + **Mowzie's Mobs 1.8.2** (`7815705`) — added now while there's no world and no installed clients to re-sync
- **BlueMap 5.3** (server-only, Modrinth pin — 5.12+ needs Java 21): live 3D web map on `:8100`, wire-up in HOSTING
- **Discord Integration 3.0.7.1** (`5332465`, server-only): chat/join/death bridge; bot token configured post-boot, never committed
- **"Kilometre Taşları" quest chapter**: 10 group milestones with named trophy-item rewards (Ender Dragon one auto-completes via advancement)
- **Stats scoreboards** (KubeJS): total deaths + deaths-to-dragons with chat broadcast — feeds the yearly ZapeG Ödülleri
- **Offsite backups**: opt-in rclone sidecar (`--profile offsite`, rclone.conf gitignored)
- **Seed flow**: `WORLD_SEED` env + audition protocol in HOSTING (Terralith+BoP make vanilla seed lists useless)
- **ROADMAP.md**: launch → lore era (needs group in-jokes) → Grafana → LLM NPC prototype (Mineflayer route)

## v0.3.1 — 2026-08-15

Progression stance + repo hygiene. World risk: none. Players: nothing.

- **Progression is fully natural again** — the v0.3.0 star recipe removals are reverted to commented/staged. No enforcement anywhere; the "no millions" rule stays social. Verified ids remain documented in `custom_endgame_nerfs.js` if the group ever changes its mind.
- `.gitattributes` added (LF enforced for scripts/configs, binaries marked) — safe to commit from Windows, deploy on Linux.

## v0.3.0 — 2026-08-15

Name, access, and the progression ceiling. World risk: none (pre-world). Players: pick your username once and report it for the whitelist.

- **Server is named ZapeG** — all "Seri" branding replaced (quest chapter, kit message, MOTD, logo, icon; recipe id now `zapeg:name_tag`, kit stage `zapeg_starter_kit`)
- **`ONLINE_MODE=false`** — every launcher can join, no Mojang auth. Whitelist stays the gate; username = identity (see HOSTING "Access model"). Locked before go-live.
- **Progression ceiling ACTIVE**: ATM Star (`allthetweaks:atm_star`) and Gregstar (`allthetweaks:greg_star`) recipes removed via KubeJS — verified against ATM9's own scripts. Everything below them untouched; star quest chapters remain as lore. Draconic chaos tier staged, pending playtest.
- **Player guide rewritten** (`docs/PLAYER-SETUP-TR.md` + styled `docs/zapeg-kurulum.html`): premium (CurseForge App) and offline-launcher paths
- Easter eggs for the four players: parked, design later (KubeJS per-player hooks make this trivial)

## v0.2.0 — 2026-08-15

Identity + tuning layer. World risk: none (all server-side data/config). Players: nothing required.

- **Custom quest chapter** (`overrides/config/ftbquests/...`): Turkish "Yol Haritası" — welcome hub + 6 player-path quests + first-night survival guide, non-gating, links into ATM9's chapters; rewards incl. welcome backpack (renamed to ZapeG in v0.3.0)
- **Starter kit + custom recipe** (KubeJS, server-side): first-join kit (bread/torch/warp stone) + welcome message; name tag now craftable (paper+string+iron — dragon naming)
- **Branding**: custom server icon (auto via overrides), colored Turkish MOTD; optional client PackMenu logo under `client/` (cosmetic, manual install)
- **Tuning defaults** (TUNING.md + `scripts/apply-gamerules.sh`): keepInventory false (Tombstone ships in pack), sleep% 10, no phantoms, mobGriefing on; group-vote items flagged
- Host flow: `apply-overrides.sh` + restart after first boot; `apply-gamerules.sh` once on the real world

## v0.1.0 — 2026-08-15

Initial release.

- Base: **ATM9 1.1.1** (CF file `7097953`, Forge 47.4.0, MC 1.20.1)
- Extras (server + client): Ice and Fire `2.1.13-1.20.1-beta-5`, Citadel `2.6.3-1.20.1`, Immersive Petroleum `1.20.1-4.3.1-36b`
- Server-only: Chunky 1.3.146 (Modrinth)
- Ops: 12G heap + Aikar flags, whitelist enforced, daily backups (14-day prune), snapshot/pregen/override scripts
- KubeJS endgame-nerf hooks staged but dormant (policy level 1)
- Players: fresh install per `docs/PLAYER-SETUP-TR.md`
