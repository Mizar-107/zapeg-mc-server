# ZapeG Roadmap

Not everything in v1 — each phase ships through the UPDATING.md ritual. World-risk notes per item.

## 🛠️ v0.9.0 (working tree) — ZapeG Citizens + official vehicle stack

- **Real workers, not a named mascot**: an OP can run `/citizen spawn <name> <onlinePlayer>` to create multiple chat-commanded citizens, each logically assigned to a player.
- Numen AI 0.1.1 supplies the player-like body and 32 server-executable world tools. ZapeG Citizens 0.4.0 adds assignment/authorization, protocol-3 durable planning, persisted checkpoints and action evidence, restart-safe cancellation/recovery, operator controls, and a closed workflow loader for storage, building, mining and combat.
- One private `citizen-brain` container on the host serves every citizen through one shared Ollama key. Players receive the required Forge components in the generated patch and never receive a provider key.
- The generated player patch grows from 15 to **23** exact client additions. Numen is pinned to CurseForge file `8551640`, CC:Tweaked 1.116.1 is re-pinned from Modrinth, both owned ZapeG jars are tracked by SHA-256, and every vehicle jar is exact-pinned and hash-locked.
- Conversation memory stays private per citizen and commanding actor in SQLite. Long physical jobs additionally persist their plan, compact checkpoint, recent evidence and idempotent request journal; the matching Minecraft world `SavedData` ledger remains final authority over one world action at a time. The model can request registered Numen tools or one of four packaged workflows, but never arbitrary commands, RCON, paths or client-only tools.
- Complex work now survives provider delays, owner/body absence and coordinated restarts under default 128-action, 192-model-call and three-active-hour budgets. Unknown mutating outcomes force a read-only observation before another mutation, and completion requires cited successful evidence plus post-mutation verification.
- True server-owned lore citizens now use a durable world principal, persistent persona/home, public dialogue, operator-only durable physical jobs, restart wake-up and delayed death recovery. Dialogue remains available while the body performs an operator job; they are not faked under a player's identity.
- Common enemies and bosses remain deterministic mobs/state machines. LLMs may eventually choose high-level intent or dialogue, but should not drive every combat tick.
- The obsolete single-character, log-tail chat prototype is removed. Easy NPC remains available for non-worker lore/quest characters; Heraldor remains an independent optional presence service.
- **Quest authority pass:** every custom quest checkmark is replaced by a real item/advancement/server criterion. Exact-name inventory/stat/advancement checks cover the initial roster; subjective builds require OP inspection. `MertOnal` owns the 5 km minecart and house quests; Emin has a town fountain; Emir and Salih each have an owned-dragon quest; Enes's crossbow task is active for `Thekingim`. Four named items are delivered directly to their exact owners. See `docs/QUEST-VALIDATION-TR.md`.
- **Live metrics pass:** exporter/Prometheus/Grafana images are pinned; Grafana is localhost-only and non-anonymous by default; retention is 400d/10GB; the provisioned dashboard includes TPS, tick time, entities and player drill-down. BlueMap cache is excluded from daily archives.
- **Muhtar v2 mod consultant + real guide chapters:** the town-square Easy NPC now compares core ATM9 paths and every player-facing ZapeG addition, gives prerequisites/first steps/common traps, and only then offers an optional quest handoff. Ten curated added-mod chapters own the actual progression. A permission-0 fixed-route bridge closes the NPC menu before opening FTB Quests; no broad command allowlist remains. Muhtar still owns no rewards, scores, path locks or progress, and the fixed UUID/versioned presets keep v1 rollback and permanent deletion explicit. The personal Nemesis remains a later experiment.
- **Immersive Vehicles baseline:** core 24.0.0 + MTS Official Pack V29 + Official Automobile Pack V3 bring the native Forge 1.20.1 official vehicle set. Entity Culling compatibility is shipped in the patch; community packs wait until persistence, client FPS, TPS/network use and normal-terrain driving pass a multiplayer smoke test. IV vehicles and moving Eureka/VS/Create constructs remain separate physics systems.
- **Nifty Ships experimental core:** the owner chose core 1.0.14 (`5963449`) for its fixed-hull age-of-sail/cannon loop after reviewing its clean material economy and known chunk-reload/mooring, drift, anchor and rendering defects. It is exact-pinned on both sides under an explicit waiver, but copied-world multiplayer persistence still gates promotion. The official BOP addon crashes against ATM9's BOP 19.0.0.96 API; MuddyPatch, every-wood and Firma addons are not included.
- **Heraldor Director v2:** SQLite-backed pacing prevents clustered random events and persists a one-shot story ledger. Permission-level-2 players and RCON can control monotonic campaign phases, pause/resume, phase-gated private visual events and cancellation through the fail-closed `/zapeg-lore director` mailbox. An OP-only rehearsal summons one target-bound, no-loot/no-XP vanilla servant named `Heraldor'un Hizmetkârı`; the third legitimate victory emits a typed request for an opt-in, self-deafened Discord voice cameo. The first hash-pinned clip and isolated relay are built; host two-client rendering and private live-Discord acceptance still gate activation.
- **Heraldor horror slice (runtime 0.3 / protocol 4):** five new target-private profiles — `sky_mark_01` (impossible moon/eyes only the target renders), `false_passage_01` (render-only doorway that collapses on approach, with a ~30 s encore beat), `chroma_break_01` (photosensitivity-safe corrupted-recording overlay), `near_miss_01` (a figure crossing just behind the target, never in the crosshair) and `whisper_steps_01` (the target's own footsteps replayed ~10 s late from behind). Every scene now opens with a client-local ambience-dip prelude and runs a hard-capped camera-unease layer (sub-degree jitter, brief shake pulses, slow micro-roll). Director-side, an opt-in scheduler clusters scenes into nights of activity followed by days of silence; coarse 32-block stalking memory places scenes near places the target visits (purged on world change); rare grave echoes answer old deaths near their site; and a servant victory makes that player's next scene `footsteps_01`. Combat/manifestation fights remain later work.

## ✅ v0.8.1 — one-patch onboarding + overlap audit

- Licensed-player path is now ATM9 1.1.1 + one profile-root `ZapeG-Kurulum-Yamasi` zip. No individual jar downloads and no second defaults zip.
- Client builder validates current/legacy structured ATM9/Forge metadata, checks CurseForge file IDs when recorded by the app, and always enforces all 15 exact filenames plus reviewed SHA-256 locks; it preserves licensed players' personal settings. Offline payloads use a separate reviewed complete-mod inventory lock.
- Server/client loader override is Forge 47.4.10; offline output is accurately framed as an isolated Forge 47.4.10 game-directory payload.
- Valkyrien Skies 2.4.11 + Eureka 1.6.3 are the conservative physics-ship phase 1. Trackwork is a post-smoke-test candidate; Interactive/Clockwork wait on a deliberate Create-stack migration, not a blind drop-in.
- Env docs distinguish the default stack from optional service profiles; Discord bot config and Heraldor webhook are separate mechanisms.
- `eminomi12` (Emin Taha), `MertOnal` (the car-fan Mert) and `Thekingim` (Enes) have exact-name welcome pools and first-login gifts; the other Mert remains an unconfirmed real-name key. The live roster and slots are 10.
- `SalihKarahan` is Salih's confirmed exact login key; his arson-history welcome pool and named flint-and-steel gift are wired to it.
- A third FTB Quests page, **ZapeG**, began with eight independent personal-lore objectives. The current working tree replaces their honor-system checkmarks with server authority and expands the page to 13 nodes, including `MertOnal`'s two-node quest line.
- Stats correctness pass: dragon deaths use an explicit three-dragon allowlist; the exporter avoids Mojang lookup for offline identities and samples once per minute. Friendly UUID→name dashboard aliases wait for real post-boot player data.
- Redundant WDA/playerAnimator manual pins were removed after the first real boot: ATM9 1.1.1 already supplies WDA 2.1.58 and the exact playerAnimator dependency. Both features remain, but neither belongs in the 15-jar ZapeG patch.
- Offline access follows the owner's explicit trade-off: whitelist off and `Mizar__107` permanent OP, with nickname/OP spoofing knowingly accepted. Internal RCON stays enabled but its generated password no longer needs host configuration.
- The old chat-only LLM prototype was parked here and is superseded by v0.9.0's Citizens architecture. Heraldor continues to use its embedded line pools by default.
- Post-add material/structure overlap audit is clean; watch-items remain night pressure and structure density (`BALANCE.md`).

## ✅ v0.8.0 (now) — content drop 2 + Heraldor awakens

- **Combat/exploration work** (all pre-world, verified 1.20.1 Forge): Aquamirae, Born in Chaos, Simply Swords and Better Combat were manual additions; Incendium is server-only. WDA and playerAnimator were initially declared here but v0.8.1 established that ATM9 already supplies both. Magic deliberately skipped — ATM9 already ships Eidolon, Forbidden & Arcanus, Mahou Tsukai and Ars Elemental.
- **Heraldor presence engine** (`--profile heraldor`): night-biased whispers only the target sees (+ cave sounds at their position), rare global lines, rarest Discord webhook posts, and the authored 5-chapter campaign (`npc/campaign-heraldor.yml`, driven by `/zapeg-lore story`). Staged: midnight shadow visits (self-despawning named vexes; `HERALDOR_EVENTS`). No LLM.

### Heraldor arc (the long game)

1. **Presence** (shipped) — whispers, sightings-by-sound, Discord intrusions, the original peripheral `echo_01` and the partial `threshold_01` silhouette, now joined by `sky_mark_01` and `whisper_steps_01`.
2. **Servants** (shipped, manually gated) — deterministic tagged minions, the delayed-player `motion_echo_01`, `near_miss_01`, the collapsing `false_passage_01`, and sparse victory-triggered, allowlisted Discord audio. It stays manually triggered until copied-world and private-channel acceptance pass.
3. **Manifestation** (visual slice shipped, manually gated) — `light_fault_01` adds an impossible camera-bound lighting failure and `chroma_break_01` a bounded corrupted-recording overlay, without changing blocks or exposing a scene to observers. Runtime 0.3's eleven profiles and the Director bridge require coordinated client update and two-client/shader acceptance before live use.
4. **Confrontation** — fight guards/echoes with deterministic mechanics. Heraldor remains unresolved unless a one-time narrative finale justifies a custom entity; never turn him into a farmable boss.

## ✅ v0.4.0 (now) — pre-world content + presence layer

Pre-world is the free window: no world to break, no clients to re-sync.

- Content drop: **Alex's Caves** + **Mowzie's Mobs** (client+server, pinned)
- **BlueMap** live 3D web map (server-only, :8100)
- **Discord bridge** (server-only; host wires the bot token post-boot)
- **Kilometre Taşları** quest chapter — group milestones with named trophy rewards
- Stats scoreboards (deaths, deaths-to-dragon) + death broadcast
- Offsite backup sidecar (opt-in `--profile offsite`)
- Seed audition protocol (HOSTING) — pick the seed against the real modstack

## 🚀 Launch (host, day 0–1)

Boot → seed audition → real world → gamerules → pregen → build the licensed patch + offline payload → clients → play. First playtest feedback decides everything below.

## ✅ v0.5.0 (now) — metrics + scaffolds

- **Grafana stack shipped** (`--profile metrics`): minecraft-exporter + Prometheus (180d) + Grafana `:3000`, pre-provisioned dashboard (online, playtime, deaths, blocks, distance) → yearly **ZapeG Ödülleri** reads straight off it
- **Login-lines mechanism shipped** (`zapeg_welcome.js`) with nine personal pools: six exact usernames plus three temporary real-name keys
- **Build-ClientZip.ps1** — builds both the one-zip licensed patch (`-PatchOnly`) and offline game-directory payload

## v0.5.x — the lore era (first weeks)

- **Lore datapack**: hand-built structures seeded in unexplored territory — "ZapeG Araştırma Tesisi" ruins, Turkish lore books referencing group history. New-chunks-only = world-safe. **Blocked on: in-jokes/lore input from the group.**
- **Real login lines**: nine pools are live; Yusuf, Ali and the other Mert still need exact Minecraft usernames.
- **Milestone gift items v2**: awarded live at the moment (KubeJS advancement hooks) instead of via quest claim.
- Playtest-driven trims (remove what nobody touches; Apotheosis/dragon/Mowzie's spawn tuning if needed).

## ⚠️ v0.7.0 historical prototype — superseded

This phase tested Easy NPC plus a log-tail chat bridge around one preselected
character. That premise was not the actual requirement and the prototype could
not execute gameplay tasks. v0.9.0 removes it in favor of multiple assignable
Numen-backed workers and a shared server-side brain. Easy NPC remains for static
lore/quest use only.

The Mineflayer route also remains rejected for this pack: a vanilla-protocol bot
does not complete the roughly 440-mod Forge handshake. A full modded headless
client would add another fragile Minecraft runtime and substantial memory cost.

## 🧊 Parked

- Weekly bounty board (KubeJS rotating objectives)
- Tablist polish / TPS in tab
- Shader recommendation doc for capable PCs (Complementary ships in pack options)
- ZapeG Ödülleri ceremony automation (scoreboard snapshot → yearly awards)
