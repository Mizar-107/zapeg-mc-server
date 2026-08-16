# UPDATING — customizing the pack without hurting the world

The pack is meant to evolve (brief §8–9). This is the playbook for doing that with a live world. Golden rules: **snapshot first, one change at a time, server and client mod sets stay identical, never downgrade.**

## Change-safety matrix

| Change | World risk | Client action needed |
|---|---|---|
| KubeJS recipes/tweaks (`overrides/`) | **None** — hot-reloadable, no world data touched | None |
| FTB Quests edits (level-2 endgame policy) | None | None (synced from server) |
| Mod config / `server.properties` / gamerules | None | None |
| Add a server-side util (Chunky, profilers) | None | None |
| Update Numen or ZapeG Citizens | Low–medium — snapshot first and test citizen save/stop/remove behavior | Rebuild and distribute the matching client patch before reconnecting |
| Update only the private Citizens brain | None to world data; SQLite/protocol migration still needs backup + compatibility review | None when the Forge protocol remains compatible |
| **Add a content mod** (e.g. Alex's Caves, Mowzie's later) | Low — new worldgen appears only in **newly generated chunks**; existing chunks unchanged. Fine, just explore outward for the new stuff | Same jar, same version, before reconnecting |
| Update a mod to a newer build | Low–medium — read its changelog for world-format notes | Match the version |
| Bump ATM9 pack version (1.1.1 → 1.1.x) | Medium — configs/scripts/quests churn; read the ATM changelog | Update pack version in launcher |
| **Remove a content mod** | **HIGH** — its items/blocks vanish from chests/world, machines break, dimensions may corrupt. Only acceptable pre-world or for truly-unused mods (§5 level 4: removing Draconic Evolution is safe only if nobody built DE) | Remove same jar |
| Swap/major-change worldgen mid-world | **HIGH** — chunk seams/borders. Avoid; new dimension resets are the workaround | — |
| Downgrade pack or mod versions | **Never** — world data doesn't roll back | — |

## The ritual (every change)

1. `scripts/snapshot.sh pre-<change>` on the host
2. Make the change in **this repo** (pin bump in `extras/cf-mods.txt` / `docker-compose.yml`, or files in `overrides/`) — never live-edit the server
3. Commit, tag if player-visible (`vX.Y.Z`), update `CHANGELOG.md`
4. Host: `git pull && docker compose up -d mc`; for non-jar overrides only:
   `scripts/apply-overrides.sh` (no restart). Owned jars under `overrides/mods/`
   are excluded from rsync and require recreating/restarting `mc` through Compose.
5. Watch boot log; broken → restore snapshot, revert commit
6. If anything client-side changed, announce to players **before** they reconnect (guide: `docs/PLAYER-SETUP-TR.md` §Güncellemeler)

## Citizens release discipline

Numen, the owned Forge jar and the private brain are one reviewed compatibility
set even though they arrive through three mechanisms:

- Numen is pinned by CurseForge file ID in `extras/cf-mods.txt` and by exact
  filename/SHA-256 in both client inventory locks.
- ZapeG Citizens is copied into `overrides/mods/`, marked binary, and locked by
  exact filename/SHA-256. Never replace it directly in `data/mods/`.
- `citizen-brain` builds from an immutable public Git tag in
  `docker-compose.yml`. Never point production Compose at a moving branch.

For any Citizens change: snapshot the world, back up the named brain volume,
update all three pins deliberately, rebuild the client patch, and run the
spawn/chat/stop/remove acceptance test from
`docs/CITIZENS-HOST-SETUP.md`. The host deploy command is:

```bash
docker compose --profile citizens build --pull citizen-brain
docker compose --profile citizens up -d mc backup citizen-brain
```

## KubeJS fast path (zero-risk customization)

Recipe/tweak work never touches world data and doesn't even need a restart:

1. Edit `overrides/kubejs/server_scripts/*.js` (unique filenames — pack updates can't clobber them)
2. Host: `scripts/apply-overrides.sh`
3. In-game (OP): `/kubejs reload server_scripts`; debug with `/kubejs errors`
4. Verify item ids with `/kubejs hand` before writing recipes against them

This covers ~80% of "custom content" (brief §8). A real Forge mod is the escalation path only when KubeJS can't express it.

## Endgame policy state

Currently **level 1** (social rule) per brief §5. Level-3 hooks are staged (commented) in `overrides/kubejs/server_scripts/custom_endgame_nerfs.js`. Escalate one recipe at a time; level 2 (quest-chapter edits) is plain-data FTB Quests editing, world-safe.

## Version discipline

- `CHANGELOG.md` gets an entry for every tagged release — it doubles as the "what do players need to do" announcement source.
- Tags: `v0.x.y` while tuning, `v1.0.0` when the group calls it stable.
