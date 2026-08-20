# Heraldor — one-page runbook

Private operator feature. Never explain Heraldor, the commands, tags,
counters or triggers to players.

**How it works now.** One OP surface: the `/zapeg-lore` command tree
(level-2 in-game OP or exact RCON; console and command blocks fail closed).
The Python Director (`npc/heraldor.py` + `heraldor_director.py`) validates
every queued request against SQLite (`data/heraldor/`) and dispatches
`/zapegscene` on the matching ZapeG Runtime (**0.4.0, protocol 7** — server
jar and every client must run the same build or nothing renders). The story
is the 5-chapter campaign file `npc/campaign-heraldor.yml`
(`heraldor_campaign.py`): chapters of beats — scene / whisper / global /
discord / servant_wave / wait — driven manually or autonomously.

```text
/zapeg-lore story status|start|next|rehearse|reset   # the campaign, step by step
/zapeg-lore story auto on|off                        # autonomous: clustered nights, then silence
/zapeg-lore story goto <1-5>
/zapeg-lore rehearse <profile> <player>              # practice; zero state writes
/zapeg-lore trigger <profile> <player>               # LIVE one-off; raises campaign tier
/zapeg-lore servant rehearse|awaken <player> / servant cleanup
/zapeg-lore cancel | discord whisper | voice rehearse
```

`story next` fires the current beat and advances; `story rehearse` previews
it (scenes rehearse for real, text beats echo to you only). Waits advance on
real hours, in-game nights, servant victories (3rd victory still arms the
one-shot voice clip) or `story next`. Live scene triggers work even before
`story start`. The colossus climbs one stage per delivered live trigger;
`story reset` clears campaign, tier, colossus and aftermath memory for the
world. Optional extras: `HERALDOR_EVENTS` (shadow vexes),
`HERALDOR_SCENE_SCHEDULER` (random idle scenes), the parked voice relay
(`HERALDOR_VOICE_ENABLED=false` until its private-channel rehearsal passes —
see `docs/history/` for its full setup).

## GO checklist (copied world first, then live)

1. Versions match: `overrides/mods/zapeg-runtime-forge-1.20.1-<v>.jar` ==
   runtime release == the jar inside both client artifacts (protocol 7).
2. Deploy: `scripts/snapshot.sh pre-heraldor && ./scripts/apply-overrides.sh
   && docker compose restart mc && docker compose --profile heraldor up -d --build heraldor`.
3. `/kubejs errors` empty; boot log loads `zapeg_runtime`; a non-OP cannot
   see `/zapeg-lore`.
4. `python heraldor.py admin campaign-validate` prints 5 chapters;
   `admin status` shows your world token.
5. `/zapeg-lore rehearse echo <you>` renders (target sees it, a second
   player sees nothing, packets stay target-only).
6. `/zapeg-lore trigger echo <you>` answers `scene dispatched`, and
   `story status` now shows tier `presence`.
7. `/zapeg-lore servant rehearse <you>`: spawns, only hurts the target,
   drops nothing, cleans up on logout/death/distance/timeout.
8. `story start`, then `story next` through chapter 1; `story rehearse`
   moves nothing (`story status` unchanged).
9. `story auto on`: beats fire at night, cluster, then stay silent ≥ the
   configured silence window; nothing fires two nights in a row after a cluster.
10. Restart Minecraft + Director: `story status`, tier and colossus stage
    survive; a replayed command answers "already delivered" without re-firing.
11. Visitation/colossus finale only after per-player `osScares` opt-outs are
    respected and the two-client privacy spot-check (5) passed on this build.
12. Normal backup ran once and `admin restore-snapshot` restores it cleanly.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| Client can't join; log shows `zapeg_runtime` rejection | Client jar version != server jar. Rebuild/distribute matching artifacts; never mix protocols. |
| `/zapeg-lore` replies "does not accept this command source" | Sent from console/command block. Use in-game OP or RCON. |
| Reply says "queued" but nothing happens | Director container down or mailbox stuck. `docker compose --profile heraldor logs heraldor`; inspect `/data get storage zapeg:heraldor control_request`, clear only that exact path. |
| `runtime rejected request: Unknown scene profile` | Server runtime jar older than the Director expects (needs 0.4.0/protocol 7). |
| `no valid loaded scene anchor` | Target in a cramped/unloaded spot; move to open ground and retry. |
| Scene delivered but target saw nothing | Client-side runtime missing/old, or scene resolved instantly (gaze). Rehearse again while looking away. |
| Whispers/ambient never fire | World still `dormant`: run `story start` (or one live trigger), check `story status`. |
| `story next` says "beat is not ready" | Named target offline or no last victim yet; wait or `story goto`. |
| Autonomous beats never fire | `story auto on`? Night? Cluster silence window still open? `story status` shows the wait. |
| Discord beats fail | `HERALDOR_WEBHOOK` unset (fail-closed) or per-world cooldown (`HERALDOR_DISCORD_MANUAL_GAP_SECONDS`). |
| Servant kill not counted | Rehearsal servants never count; killer must be a real player (Numen excluded); check `/scoreboard players get #total zapeg_hsvc`. |
| Campaign refuses to load | `admin campaign-validate` prints the exact line; the daemon runs with the story disabled until fixed. |

## History

The full v2-era acceptance ledger (30 items), the voice-relay setup and the
phase-tree docs live in git history of this file
(`git log -- docs/HERALDOR-RUNBOOK.md`, last full version before this page)
plus `zapeg-current-state.md` §6. The old `/zapeg-lore director` tree,
`pause/resume`, `phase_start/phase_advance` and `colossus_reset` are gone —
`story` replaces all of them; old SQLite pause rows are ignored after the
schema-3 migration.
