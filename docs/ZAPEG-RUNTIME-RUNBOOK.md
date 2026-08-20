# ZapeG Runtime 0.2.0 — operator runbook

> **STALE — do not deploy from this page.** The current runtime is **0.4.0 /
> protocol 7** (14 profiles); server jar, tracked `overrides/mods` jar and
> both client artifacts must all carry the same build. The 0.2.0 file names
> and four-profile list below are history. Current operations:
> `docs/HERALDOR-RUNBOOK.md`.

ZapeG Runtime is a mandatory Forge 1.20.1 client/server mod for bounded,
target-private horror scenes. It is intentionally separate from ZapeG Citizens:
Citizens owns Numen bodies and dialogue, while Runtime owns synchronized effects
that need the selected player's real camera.

Runtime never spawns a Minecraft entity for these scenes. There is no hitbox,
AI, nameplate, tab-list entry, save data, loot, minimap marker or entity-tracking
packet. Only the selected client receives the scene packet.

## Profiles in 0.2.0

The wire IDs are fixed and allowlisted; arbitrary shader names, asset paths and
URLs are rejected.

| Profile | Wire ID | What the target sees | Normal hard limit |
|---|---:|---|---:|
| `echo_01` | 0 | Elongated dark figure, red/cyan separation and sparse edge faults | 10 s |
| `threshold_01` | 1 | Asymmetric partial figure that rapidly withdraws under direct gaze | 8 s |
| `motion_echo_01` | 2 | Distorted copy at the target's position/heading from about 0.6 s earlier | 11 s |
| `light_fault_01` | 3 | Spatially gated cold dimming, displaced light bands and a restrained halo | 7 s |

`threshold_01` is a deliberately partial render, not true doorway/cover
sampling. `motion_echo_01` keeps only a 32-sample position/heading ring in the
target client's memory and clears it at scene end. `light_fault_01` counts its
1.5-second gaze dwell only while the GUI effect is actually presented; F1 or a
cancelled GUI frame cannot falsely consume it.

## Release identity

- Jar: `zapeg-runtime-forge-1.20.1-0.2.0.jar`
- SHA-256: `F7DFB5DBE79A5497DB2B5FEA1DC25BBCA39B69308BFDD292737310AFE907872E`
- Minecraft: 1.20.1
- Forge: 47.4.10
- Network protocol: exact version `2`
- Distribution: mandatory on both client and server (`MATCH_VERSION`)

The owned jar is committed under `overrides/mods/`, included in both client
locks and copied by `Build-ClientZip.ps1`. Do not download or rename it by hand.
Mixed Runtime 0.1/0.2 clients are intentionally rejected during the handshake.

## Safe deployment order

1. Start from the intended clean release commit and create the normal
   pre-change snapshot.
2. Build the new client patch and validate its lock before touching production.
3. Distribute the patch and arrange a reconnect window with every player.
4. Stop Minecraft, apply the tracked non-jar overrides, remove the exact old
   Runtime 0.1 live copy, and recreate Minecraft so the tracked 0.2 jar is
   installed. The deploy paths are additive and do not purge old owned jars.
5. Verify exactly one Runtime jar exists on the host and each patched client.

```bash
scripts/snapshot.sh pre-zapeg-runtime-0.2.0
ls overrides/mods/zapeg-runtime-forge-1.20.1-0.2.0.jar
sha256sum overrides/mods/zapeg-runtime-forge-1.20.1-0.2.0.jar
docker compose stop mc
./scripts/apply-overrides.sh
find data/mods -maxdepth 1 -type f -name 'zapeg-runtime-forge-1.20.1-*.jar' -print
rm -f -- data/mods/zapeg-runtime-forge-1.20.1-0.1.0.jar
docker compose up -d --force-recreate mc
docker compose logs --tail=200 mc
test "$(find data/mods -maxdepth 1 -type f -name 'zapeg-runtime-forge-1.20.1-*.jar' | wc -l)" -eq 1
test -f data/mods/zapeg-runtime-forge-1.20.1-0.2.0.jar
sha256sum data/mods/zapeg-runtime-forge-1.20.1-0.2.0.jar
```

The boot log must identify `zapeg_runtime` without a missing-side or protocol
error. Through authenticated RCON, `/zapegscene status` must return `active=0`.

Rollback requires stopping Minecraft, returning to the prior release and
explicitly removing the newer `data/mods/zapeg-runtime-forge-1.20.1-*.jar`
before reapplying the old overrides; `apply-overrides.sh` is additive. Players
must return to the matching old patch before reconnecting.

## Low-level Runtime commands

Permission-level-2 in-game operators and authenticated RCON may use:

```text
/zapegscene status
/zapegscene rehearse <online-player> [profile]
/zapegscene trigger <online-player> <event-uuid> <profile>
/zapegscene cancel-all
```

- `rehearse` generates a temporary UUID and does not consume the live replay
  ledger.
- `trigger` is the effects-only live form. A consumed UUID cannot be reused
  after a normal world save/restart.
- `cancel-all` removes the one active scene. Runtime 0.2 deliberately permits
  only one global scene, so operators cannot stack effects.
- These commands never mutate the Heraldor phase or pause state. Command blocks,
  functions and their `execute as <op>` redirects are excluded.

## High-level Heraldor Director commands

Use these for actual campaign control. They queue one expiring, world-bound
request; the persistent Python/SQLite Director validates and records it before
calling Runtime with an idempotent UUID.

```text
/zapeg-lore director status
/zapeg-lore director phase start presence
/zapeg-lore director phase start servants
/zapeg-lore director phase start manifestation
/zapeg-lore director phase advance
/zapeg-lore director pause
/zapeg-lore director resume
/zapeg-lore director cancel

/zapeg-lore director event rehearse apparition echo <player>
/zapeg-lore director event rehearse apparition threshold <player>
/zapeg-lore director event rehearse apparition motion-echo <player>
/zapeg-lore director event rehearse apparition light-fault <player>

/zapeg-lore director event trigger apparition echo <player>
/zapeg-lore director event trigger apparition threshold <player>
/zapeg-lore director event trigger apparition motion-echo <player>
/zapeg-lore director event trigger apparition light-fault <player>
```

Every world begins at `dormant`. `echo` and `threshold` require `presence`,
`motion-echo` requires `servants`, and `light-fault` requires
`manifestation`. Phases only move forward. Pause suppresses ambient rolls and
new live scenes but still permits rehearsals and cancellation. The immediate
reply is **queued**; inspect `director status` for the terminal result. The
high-level subtree accepts a real level-2 player or exact RCON source and rejects
command blocks/functions, including `execute as <op>` redirects. See
`docs/HERALDOR-RUNBOOK.md` for mailbox recovery,
Discord voice and servant-threshold behavior.

## Two-client acceptance gate

Use a copied world or disposable server, one OP and two matching 0.2 clients.
Keep both players close enough that an ordinary entity would be visible to both.

1. Start `presence`, then rehearse `echo` and `threshold` for Target. Target
   must see each effect; Observer must receive/render nothing.
2. Slowly look directly at each figure. It must withdraw after its bounded gaze
   dwell. Repeat without looking and verify hard timeout cleanup.
3. Start `servants`, walk continuously and rehearse `motion-echo`. It must warm
   up, then follow Target's past position/heading rather than the server anchor.
   Repeat indoors and in a cave.
4. Start `manifestation` and rehearse `light-fault`. Test in open terrain and
   indoors. With F1 enabled, it must not draw or report visible/gaze; after F1 is
   disabled, it may present normally and remain readable before withdrawing.
5. Exercise low-level cancel, Director cancel, pause/resume, logout, death and
   dimension change. Every path must leave `active=0` and no artifact after
   reconnect/restart.
6. Repeat all profiles in first- and third-person with Embeddium, Oculus, Entity
   Culling and the supported shader configurations: shaders off,
   Complementary Unbound on, and MakeUp fallback. Also test F3+T, shader toggle,
   window resize and a moving vehicle/ship case.
7. Watch both client logs for GL/vertex-format errors and compare frame time.
   Observer must have no scene packet, model, overlay or acknowledgement.
8. Trigger one live UUID, save/restart, then verify the same UUID is rejected.
   Interrupt one Director attempt after its SQLite claim and confirm it becomes
   terminal `ambiguous` rather than replaying.

Do not arm campaign-driven scenes until this gate passes on the host's actual
ATM9 copy. A successful unit/build check is not a substitute for two clients and
the real rendering stack.

## Combat boundary

Runtime 0.2 is visual horror only. It cannot damage, collide, block movement or
be attacked. The next combat slice should introduce a server-authoritative
guardian/servant with shared hitboxes, damage and deterministic phases; private
Runtime effects may decorate that fight but never decide damage. Heraldor
himself should remain a later, one-time manifestation rather than a farmable
repeat boss.
