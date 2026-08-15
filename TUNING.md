# TUNING — server behavior decisions

My defaults below are encoded in the repo (compose env / `scripts/apply-gamerules.sh` / post-boot config steps). Items marked **[vote]** deserve a group decision — veto before go-live, everything is changeable later without world damage.

## Gamerules (applied via `scripts/apply-gamerules.sh` after real-world creation)

| Rule | Default | Why | |
|---|---|---|---|
| `keepInventory` | **false** | Pack ships **Corail Tombstone** — death drops go into a grave you walk back to. Real stakes, zero item-loss rage. | **[vote]** |
| `playersSleepingPercentage` | **10** | One sleeper skips the night for up to 8 online. No "herkes yatağa" çığlıkları. | |
| `doInsomnia` | **false** | No phantoms. Nobody has ever voted for phantoms. | |
| `mobGriefing` | **true** | Creeper holes are content; FTB Chunks claims already block explosions on claimed land — claim your base (M). | **[vote]** |
| `doFireTick` | **true** | Fire spreads (dragons!). Claimed chunks are protected; build with stone near roost country. | |
| `pvp` (server.properties) | **true** | Friendly duels; whitelist-only server, griefing isn't a threat model. | **[vote]** |

## Access model (locked pre-world)

| Setting | Value | Why / trade-off |
|---|---|---|
| `ONLINE_MODE` | **false** | Friends on mixed launchers (not everyone has a Microsoft account) must all join. Risk: usernames are spoofable offline → mitigated by enforced whitelist + IP shared only in the group. **Locked before go-live**: flipping it later regenerates every player UUID (inventories/claims orphaned). |

## World & team decisions

| Decision | Default | Notes | |
|---|---|---|---|
| `WORLD_SEED` | empty until audition | Terralith + BoP ship in ATM9 → published vanilla seeds are meaningless. Pick via the audition protocol (HOSTING §World protocol), then lock in `.env` **before** the real world. | |
| FTB Teams | **one shared party** | Milestone chapter assumes shared progress: everyone joins one party (`/ftbteams party create zapeg`, invite all). Quest completions + trophies then fire for the whole group. Alternative: solo teams, milestones become per-person. | **[vote]** |

## Already set in `docker-compose.yml`

| Setting | Value | Note |
|---|---|---|
| `DIFFICULTY` | normal | **[vote]** — hard makes Cataclysm/dragons nastier; normal fits "efor gerektirmesin" |
| `VIEW_DISTANCE` / `SIMULATION_DISTANCE` | 7 / 6 | Server sanity (brief §6); clients can render further locally |
| `SPAWN_PROTECTION` | 0 | Spawn is buildable; claims are the protection layer |
| whitelist | enforced | Usernames via `.env` or rcon |

## Post-first-boot config passes (need the mod's config files to exist)

| Target | Decision | How |
|---|---|---|
| **Ice and Fire griefing** | Dragon griefing → **low/none** (wild dragons must not delete cities); roost spawn rate: leave default for playtest 1 | `scripts/iceandfire-config-check.sh` surfaces the keys → edit → snapshot → restart |
| **Ice and Fire spawn rates** | Default until first playtest; if the overworld feels like a war zone, halve roost/lair gen | same |
| **Apotheosis** | Defaults for playtest 1 (ATM already tunes it); revisit boss-spawn frequency only if surface bosses annoy | `data/config/apotheosis/` |
| **Surface/mob density** | I&F + Mowzie's + Cataclysm + Apotheosis all add spawns — compatible, but combined surface pressure is a playtest question. If the overworld feels like a war zone, halve I&F roost gen and Mowzie's spawn rates first | their configs under `data/config/` |
| **Endgame ceiling** | Level 1 (social) — active. Level 3 KubeJS hooks staged, dormant | brief §5 |

## Deliberately NOT touched

- No extra performance mods (ModernFix/FerriteCore/Spark ship with the pack; profile before adding anything — README §Troubleshooting).
- No recipe changes beyond the name-tag QoL recipe (`zapeg_starter.js`). Progression is fully natural — endgame hooks exist (`custom_endgame_nerfs.js`) but everything in them is commented out.
- Mob spawn rates, ore gen, loot tables: stock ATM9 until a playtest says otherwise.

## Change discipline

Gamerule/config flips are world-safe (UPDATING.md matrix, row 3) — but still: snapshot, change, note it in CHANGELOG so nobody wonders why phantoms vanished.
