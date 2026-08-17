# ZapeG Runtime 0.1.0 — operator runbook

ZapeG Runtime is a mandatory Forge 1.20.1 client/server mod for bounded,
target-private story scenes. It is intentionally separate from ZapeG Citizens:
Citizens owns Numen bodies and dialogue, while Runtime owns synchronized visual
effects that require the selected player's real camera.

Version 0.1.0 contains one neutral profile, `echo_01`. The client renders an
elongated humanoid silhouette, low-alpha cyan/red afterimages and sparse HUD-edge
faults. It is not a Minecraft entity: there is no hitbox, AI, nameplate, tab-list
entry, save data, loot, minimap marker or entity-tracking packet. Nearby players
receive no scene packet.

## Release identity

- Jar: `zapeg-runtime-forge-1.20.1-0.1.0.jar`
- SHA-256: `A284A2A56BDD7C249B2699CF526497CDC7AB440A0D90DC4A2AC2DAF6793C395D`
- Minecraft: 1.20.1
- Forge: 47.4.10
- Network protocol: exact version `1`
- Distribution: mandatory on both client and server (`MATCH_VERSION`)

The owned jar is committed under `overrides/mods/`, included in both client
locks and copied by `Build-ClientZip.ps1`. Do not download or rename a jar by
hand.

## Safe deployment order

This update changes the Forge handshake. A client without the exact Runtime jar
cannot join a server that has it, and the reverse is also true.

1. Start from the intended clean release commit and create the normal pre-change
   snapshot.
2. Build the new client patch and validate its lock before touching production.
3. Distribute the patch and arrange a reconnect window with all players.
4. Stop Minecraft, apply the tracked overrides, and restart it.
5. Verify exactly one Runtime jar exists on the host and in a patched client.

```bash
scripts/snapshot.sh pre-zapeg-runtime-0.1.0
ls overrides/mods/zapeg-runtime-forge-1.20.1-0.1.0.jar
sha256sum overrides/mods/zapeg-runtime-forge-1.20.1-0.1.0.jar
docker compose stop mc
./scripts/apply-overrides.sh
docker compose up -d mc
docker compose logs --tail=200 mc
```

The boot log must identify `zapeg_runtime` without a missing-side or protocol
error. From host console/RCON, `/zapegscene status` must return `active=0`.

Rollback requires stopping Minecraft, returning to the prior release and
explicitly removing `data/mods/zapeg-runtime-forge-1.20.1-*.jar` if the old
release predates Runtime; `apply-overrides.sh` is additive. Players must also
return to the matching old patch before reconnecting.

## OP/Director commands

Commands are visible to permission-level-2 in-game operators and to the host
console/RCON used by the Director. Command blocks and functions are excluded.
Every dispatch is logged with operator source, target, event UUID and result.

```text
/zapegscene status
/zapegscene rehearse <online-player>
/zapegscene rehearse <online-player> echo_01
/zapegscene trigger <online-player> <event-uuid> echo_01
/zapegscene cancel-all
```

- `rehearse` creates a fresh temporary UUID and never consumes the live replay
  ledger. Any OP can use it for a manual scene.
- `trigger` is the live/Director form. Its caller supplies a stable UUID; a
  consumed UUID cannot be used again after a normal world save/restart.
- `cancel-all` removes the one active scene. Version 0.1 deliberately allows at
  most one global scene, preventing operators and automation from stacking
  effects.
- `status` is compact enough for RCON parsing and never broadcasts to players.

Campaign phase state remains owned by the persistent Heraldor Director, not by
the rendering mod. A later bridge will let high-level `/heraldor phase ...`
commands enqueue a validated Director request; it will ultimately invoke the
same low-level `trigger` command with an idempotent event UUID. Do not represent
campaign phases with ad-hoc scoreboards in the meantime.

## Two-client acceptance gate

Use a copied world or disposable test server, one OP and two patched clients.
Place the selected player near open, solid ground with already-loaded chunks.

1. Keep both players close enough that an ordinary entity would be visible to
   both. Run `/zapegscene rehearse Target echo_01`.
2. Target must see the peripheral silhouette and restrained screen-edge faults;
   the observer must see neither. The observer's client log/network inspection
   should contain no spawn packet for that event.
3. Have Target slowly look directly at the figure. Roughly 175 ms of continuous
   camera gaze, with clear block line of sight, must make it disappear.
4. Repeat without looking. It must disappear by the ten-second client TTL.
5. Repeat and test operator cancellation, logout, death and dimension change.
   Every path must leave `active=0` and no artifact after reconnect/restart.
6. Repeat in first- and third-person, then with the pack's normal
   Embeddium/Oculus/Entity Culling stack and shaders both on and off. Record any
   depth, transparency or HUD-scaling defect before promotion.
7. Run a live command once with a generated UUID, save/restart, then verify the
   same UUID is rejected as consumed. The Heraldor SQLite event/outbox ledger
   remains the canonical crash/retry barrier for automated story events.

Do not enable a random or campaign-driven apparition until this gate passes.

## Boundaries for future releases

Runtime 0.1 is visual horror only. It cannot damage, collide, block movement or
be attacked. Planned reality-distortion profiles may add motion echoes,
doorway-peeking silhouettes, wrong fog/light, sky marks and render-only false
passages. Any future combatant must instead be a server-authoritative custom
entity with shared hitboxes, damage, phase state and cleanup; private visual
clones may decorate that encounter but never decide damage.
