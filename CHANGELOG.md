# Changelog

Format per entry: what changed · world risk · what players must do.

## v0.2.0 — 2026-08-15

Identity + tuning layer. World risk: none (all server-side data/config). Players: nothing required.

- **Seri quest chapter** (`overrides/config/ftbquests/...`): Turkish "Yol Haritası" — welcome hub + 6 player-path quests + first-night survival guide, non-gating, links into ATM9's chapters; rewards incl. welcome backpack
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
