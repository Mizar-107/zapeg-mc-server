# UPDATING — customizing the pack without hurting the world

The pack is meant to evolve (brief §8–9). This is the playbook for doing that with a live world. Golden rules: **snapshot first, one change at a time, server and client mod sets stay identical, never downgrade.**

## Change-safety matrix

| Change | World risk | Client action needed |
|---|---|---|
| KubeJS recipes/tweaks (`overrides/`) | **None** — hot-reloadable, no world data touched | None |
| FTB Quests edits (level-2 endgame policy) | None | None (synced from server) |
| Easy NPC guide preset/dialogue | None when stateless; delete the fixed NPC before purging its preset | None; dialogue is synced from the server entity |
| Mod config / `server.properties` / gamerules | None | None |
| Add a server-side util (Chunky, profilers) | None | None |
| Update Numen or ZapeG Citizens | Low–medium — snapshot first and test citizen save/stop/remove behavior | Rebuild and distribute the matching client patch before reconnecting |
| Update ZapeG Runtime | Low for visual-only builds; snapshot first because the network handshake is exact | Rebuild and distribute the exact matching client patch; rehearse every profile through the two-client privacy/render gate before live use |
| Update only the private Citizens brain | None to blocks/entities, but protocol-3 job state spans world `SavedData` + brain SQLite; back up and restore them as one pair | None only when the Forge/brain protocol remains compatible |
| Add the pinned Immersive Vehicles official trio | Low — no worldgen; existing chunks are unchanged. Removal becomes **high risk** after vehicles/items exist | Rebuild and distribute the same three exact jars before reconnecting |
| Add the experimental Nifty Ships core | Medium — unfinished hulls generate only in new chunks, and known unload/mooring defects require a copied-world test. Removal becomes **high risk** after ships, cargo/items or generated structures exist | Rebuild and distribute the same exact core jar before reconnecting |
| **Add a content mod** (e.g. Alex's Caves, Mowzie's later) | Low — new worldgen appears only in **newly generated chunks**; existing chunks unchanged. Fine, just explore outward for the new stuff | Same jar, same version, before reconnecting |
| Update a mod to a newer build | Low–medium — read its changelog for world-format notes | Match the version |
| Bump ATM9 pack version (1.1.1 → 1.1.x) | Medium — configs/scripts/quests churn; read the ATM changelog | Update pack version in launcher |
| **Remove a content mod** | **HIGH** — its items/blocks vanish from chests/world, machines break, dimensions may corrupt. Only acceptable pre-world or for truly-unused mods (§5 level 4: removing Draconic Evolution is safe only if nobody built DE) | Remove same jar |
| Swap/major-change worldgen mid-world | **HIGH** — chunk seams/borders. Avoid; new dimension resets are the workaround | — |
| Downgrade pack or mod versions | **Never** — world data doesn't roll back | — |

## Mandatory mod-add gate

Every new mod, content pack and addon must pass this gate before it becomes an
active ZapeG pin. This is fail-closed: if balance, duplication or compatibility
cannot be confirmed, record the evidence gap and keep the candidate deferred.
Do not add it to `extras/cf-mods.txt`, the client builder/locks or a production
deployment as a way to discover whether it works.

### Admission — before pinning

1. State the player need and compare it with ATM9 and ZapeG's existing features;
   reject needless duplicate systems or define a clear coexistence boundary.
2. Verify Minecraft 1.20.1, Forge 47.4.10 and Java 17 compatibility from the
   exact upstream file. Record its project/file ID, filename, side, license and
   complete dependency closure; CurseForge dependencies are not auto-resolved.
3. Check the ATM9 manifest, manual additions and jar metadata for an existing
   copy, duplicate mod ID, bundled library or incompatible version range.
4. Record the `BALANCE.md` audit: ores/materials, fluids/fuels, energy, recipes,
   loot/progression, mobs/spawns and worldgen/structure density. Prefer config or
   tag unification over adding another duplicate resource economy.
5. Audit interaction with the adjacent stack that the feature will touch,
   including mixins/configs, physics, rendering/shaders, Entity Culling,
   keybinds, storage/duplication, performance and network behavior.
6. Classify add-to-world and later-removal risk, define the snapshot/rollback
   boundary, and list the exact feature and regression tests needed to promote.

### Promotion — before players or production

1. Add exact declarative pins and client-builder entries; review the real jar's
   SHA-256 in both inventory locks. Sync counts, player docs, changelog and the
   continuity document.
2. Run static validation, then boot a copied/throwaway world with the complete
   server set. Join with both supported client paths and 2–3 clients when the
   feature is multiplayer-sensitive.
3. Exercise the candidate's core loop plus relevant adjacent mods. Include
   chunk unload/reload, restart/reconnect and persistence; check keybinds,
   rendering/shaders and any storage or damage boundary it introduces.
4. Watch Spark/TPS, RAM, client FPS and host network where applicable. Promote
   only when the recorded acceptance checks pass. A waiver must name the owner,
   rationale and unverified evidence; it is never implicit.

## The ritual (every change)

1. `scripts/snapshot.sh pre-<change>` on the host
2. Make the change in **this repo** (pin bump in `extras/cf-mods.txt` / `docker-compose.yml`, or files in `overrides/`) — never live-edit the server
3. Commit, tag if player-visible (`vX.Y.Z`), update `CHANGELOG.md`
4. Host: `git pull`. For an ordinary external pin, run
   `docker compose up -d --force-recreate mc`; for non-jar overrides only, use
   `scripts/apply-overrides.sh` (no restart). Owned jars under `overrides/mods/`
   are excluded from rsync: remove only the exact retired live filename required
   by its runbook, then force-recreate `mc`. Citizens always uses the full paired
   rollout in `docs/CITIZENS-HOST-SETUP.md`, not this generic shortcut.
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

For any Citizens change: quiesce or cancel active jobs, stop Minecraft before the
brain, snapshot the world, archive the stopped named brain volume under the same
pair ID, update all three pins deliberately, rebuild the client patch, and run the
spawn/job/status/stop/remove acceptance test from
`docs/CITIZENS-HOST-SETUP.md`. Its **Build and start** sequence is the authoritative
host deployment procedure and must be followed in full. Do not replace it with a
short `compose up`: the sequence stops the two state peers in order, takes the
paired backup, removes exact retired jars from persistent `data/mods/`, rebuilds
the pinned brain, and force-recreates the affected services so duplicate mod IDs
cannot survive an owned-jar version change.

Citizens 0.4.0 uses brain document protocol 3. Never mix its Forge jar with a
protocol-1/2 brain, and never restore only the Minecraft job ledger or only the
brain database. A one-sided restore is detected conservatively but can leave jobs
requiring operator repair or replacement.

## Runtime release discipline

ZapeG Runtime uses an exact Forge network protocol and is mandatory on both
client and server. Its owned jar under `overrides/mods/` and both client lock
entries must always have the same filename and SHA-256. Never replace only the
live copy in `data/mods/`.

For every Runtime change: snapshot first, rebuild the client patch, update the
server and every player together, then pass the target/observer two-client gate
in `docs/ZAPEG-RUNTIME-RUNBOOK.md`. Verify the target sees the apparition, the
observer receives no scene, direct gaze cancels it, timeout/lifecycle cleanup is
reliable, and shaders plus Entity Culling do not expose or break it. Do not arm a
live Director trigger until that gate passes.

## Immersive Vehicles rollout

Treat core `24.0.0`, MTS Official Pack `V29` and Official Automobile Pack `V3`
as one dependency set. Snapshot first, rebuild the 23-jar client patch, and use a
throwaway world before promotion. With 2–3 clients, create a vehicle from each
pack, fuel/drive it on normal terrain, unload its chunk, restart/reconnect and
verify persistence while watching Spark/TPS and host network use. Do not use IV
vehicles on moving Eureka/VS ships or Create contraptions; their collision systems
are not compatible. If vehicles disappear, verify the three `mts:builder_*` IDs
under Entity Culling's `entityWhitelist`.

The three CurseForge projects are all-rights-reserved. Keep generated client
artifacts private, never commit their jars, and verify author permission before
public redistribution. Do not add community packs until this baseline passes;
removing any chosen pack after its content enters the world is a destructive
content removal, not a routine rollback.

## Aleki's Nifty Ships experimental inclusion (owner waiver)

Core `1.0.14` (`alekiNiftyShips-FORGE-1.20.1-1.0.14.jar`, CurseForge file
`5963449`) passes the static loader/dependency check: client+server, MIT, no
required library, Minecraft 1.20.1 and Forge 47.1.3+. It also adds no duplicate
ore, fluid or energy economy. The owner explicitly chose its age-of-sail gameplay
on 2026-08-17 and accepted an **experimental core-only waiver** for the evidence
gap below. The exact jar is pinned and hash-locked; the waiver does not call the
known defects fixed or waive the copied-world promotion test.

Open upstream reports against this exact line include mooring leads breaking or
disconnecting after chunk unload/reload even with Nifty as the only mod, ships
drifting/rubber-banding on return, anchors becoming unusable until relog and the
whole vessel disappearing at some camera angles. Its fixed entity ships are a
third physics stack beside Eureka/VS and Immersive Vehicles. ATM9 contains Biomes
O' Plenty `19.0.0.96`; the official Nifty BOP addon `1.0.4` targets the old
RegistryObject API and crashes against this version, so the active addition is
**core only**. MuddyPatch, every-wood and TerraFirmaCraft/Firma addons remain out.

Before promotion, use a copied world with 2–3 clients: build, load cargo, fire a
cannon, sail, anchor and dual-lead moor; travel 16+ chunks away, return, restart
and reconnect; repeat with Entity Culling and shaders on/off while watching
Spark, client FPS and network use. Never carry Nifty vessels on Eureka/VS ships,
Create contraptions or IV vehicles. Unfinished hulls generate only in new
beach/river chunks. If the test fails, remove the pin before live-world use;
removal after ships, cargo or generated structures exist is high risk.

## KubeJS fast path (zero-risk customization)

Recipe/tweak work never touches world data and doesn't even need a restart:

1. Edit `overrides/kubejs/server_scripts/*.js` (unique filenames — pack updates can't clobber them)
2. Host: `scripts/apply-overrides.sh`
3. In-game (OP): `/kubejs reload server_scripts`; debug with `/kubejs errors`
4. Verify item ids with `/kubejs hand` before writing recipes against them

This covers ~80% of "custom content" (brief §8). A real Forge mod is the escalation path only when KubeJS can't express it.
KubeJS `startup_scripts/` are outside this hot-reload path: Heraldor's Forge XP
drop hook requires a full Minecraft restart and must be checked with
`/kubejs errors` after boot.

Heraldor audio catalog/relay changes are also image changes, not KubeJS reloads.
Rebuild `heraldor-voice`, run `python heraldor_voice.py validate`, and rehearse
only in the fixed private test channel. Never enable live voice merely because a
new file exists; its manifest hash, expiry, no-audience behavior and one-shot
disconnect must pass `docs/HERALDOR-RUNBOOK.md` first.

## Easy NPC Muhtar fast path

Muhtar is intentionally separate from quest authority. Use the fixed UUID and
versioned preset flow in `docs/MUHTAR-QUEST-GUIDE-TR.md`; never use
`preset import_new`. A dialogue-only revision can be applied and re-imported
without restarting Minecraft. Quest chapter, KubeJS bridge or Easy NPC config
changes require a full restart. Apply v2 with
`scripts/muhtar-npc.sh apply v2 <X> <Y> <Z>`; v1 is the safe legacy-layout
rollback. For permanent removal use `scripts/muhtar-npc.sh remove` while his
chunk is loaded; `despawn` is not deletion and removing only the source preset
does not remove the live entity.

## Endgame policy state

Currently **level 1** (social rule) per brief §5. Level-3 hooks are staged (commented) in `overrides/kubejs/server_scripts/custom_endgame_nerfs.js`. Escalate one recipe at a time; level 2 (quest-chapter edits) is plain-data FTB Quests editing, world-safe.

## Version discipline

- `CHANGELOG.md` gets an entry for every tagged release — it doubles as the "what do players need to do" announcement source.
- Tags: `v0.x.y` while tuning, `v1.0.0` when the group calls it stable.
