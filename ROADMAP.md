# ZapeG Roadmap

Not everything in v1 — each phase ships through the UPDATING.md ritual. World-risk notes per item.

## 🛠️ v0.9.0 (working tree) — ZapeG Citizens + official vehicle stack

- **Real workers, not a named mascot**: an OP can run `/citizen spawn <name> <onlinePlayer>` to create multiple chat-commanded citizens, each logically assigned to a player.
- Numen AI 0.1.1 supplies the player-like body and tool engine. ZapeG Citizens 0.3.0 owns assignment, authorization, prompt routing, timeouts and lifecycle safety, and exposes all 32 server-executable Numen tools for movement, mining, building, crafting, storage, item transfer, interaction and combat.
- One private `citizen-brain` container on the host serves every citizen through one shared Ollama key. Players receive the required Forge components in the generated patch and never receive a provider key.
- The generated player patch grows from 15 to **21** exact client additions. Numen is pinned to CurseForge file `8551640`, CC:Tweaked 1.116.1 is re-pinned from Modrinth, the owned Citizens jar is tracked by SHA-256, and every vehicle jar is exact-pinned and hash-locked.
- Memory stays private per citizen and commanding actor in SQLite. The Minecraft server remains final authority: the model can request every registered server-executable Numen tool, but never arbitrary commands, RCON or client-only tools.
- True server-owned lore citizens now use a durable world principal, persistent persona/home, public dialogue, operator-only physical tasks, restart wake-up and delayed death recovery. They are not faked under a player's identity.
- Common enemies and bosses remain deterministic mobs/state machines. LLMs may eventually choose high-level intent or dialogue, but should not drive every combat tick.
- The obsolete single-character, log-tail chat prototype is removed. Easy NPC remains available for non-worker lore/quest characters; Heraldor remains an independent optional presence service.
- **Quest authority pass:** every custom quest checkmark is replaced by a real item/advancement/server criterion. Exact-name inventory/stat/advancement checks cover the initial roster; subjective builds require OP inspection. `MertOnal` owns the 5 km minecart, house and exploit-resistant 64-ray quests; Emin has a town fountain; Emir and Salih each have an owned-dragon quest. Five named items are delivered directly to their exact owners. See `docs/QUEST-VALIDATION-TR.md`.
- **Live metrics pass:** exporter/Prometheus/Grafana images are pinned; Grafana is localhost-only and non-anonymous by default; retention is 400d/10GB; the provisioned dashboard includes TPS, tick time, entities and player drill-down. BlueMap cache is excluded from daily archives.
- **Muhtar v1 quest router:** one stateless Easy NPC in the town square opens the existing ZapeG path cards for non-OP players. It owns no rewards, scores, path locks or quest progress; a fixed entity UUID plus versioned presets make update, rollback and permanent deletion explicit. Specialist mentors and the personal Nemesis remain later experiments.
- **Immersive Vehicles baseline:** core 24.0.0 + MTS Official Pack V29 + Official Automobile Pack V3 bring the native Forge 1.20.1 official vehicle set. Entity Culling compatibility is shipped in the patch; community packs wait until persistence, client FPS, TPS/network use and normal-terrain driving pass a multiplayer smoke test. IV vehicles and moving Eureka/VS/Create constructs remain separate physics systems.
- **Heraldor Director v2:** SQLite-backed pacing prevents clustered random events and persists a one-shot story ledger. An OP-only KubeJS rehearsal summons one target-bound, no-loot/no-XP vanilla servant named `Heraldor'un Hizmetkârı`; the third legitimate victory records a typed future-audio request without playing it.

## ✅ v0.8.1 — one-patch onboarding + overlap audit

- Licensed-player path is now ATM9 1.1.1 + one profile-root `ZapeG-Kurulum-Yamasi` zip. No individual jar downloads and no second defaults zip.
- Client builder validates current/legacy structured ATM9/Forge metadata, checks CurseForge file IDs when recorded by the app, and always enforces all 15 exact filenames plus reviewed SHA-256 locks; it preserves licensed players' personal settings. Offline payloads use a separate reviewed complete-mod inventory lock.
- Server/client loader override is Forge 47.4.10; offline output is accurately framed as an isolated Forge 47.4.10 game-directory payload.
- Valkyrien Skies 2.4.11 + Eureka 1.6.3 are the conservative physics-ship phase 1. Trackwork is a post-smoke-test candidate; Interactive/Clockwork wait on a deliberate Create-stack migration, not a blind drop-in.
- Env docs distinguish the default stack from optional service profiles; Discord bot config and Heraldor webhook are separate mechanisms.
- `eminomi12` (Emin Taha) and `MertOnal` (the car-fan Mert) have exact-name welcome pools and first-login gifts; the other Mert remains an unconfirmed real-name key. The live roster and slots are 10.
- `SalihKarahan` is Salih's confirmed exact login key; his arson-history welcome pool and named flint-and-steel gift are wired to it.
- A third FTB Quests page, **ZapeG**, began with eight independent personal-lore objectives. The current working tree replaces their honor-system checkmarks with server authority and expands the page to 14 nodes, including `MertOnal`'s three-node quest line.
- Stats correctness pass: dragon deaths use an explicit three-dragon allowlist; the exporter avoids Mojang lookup for offline identities and samples once per minute. Friendly UUID→name dashboard aliases wait for real post-boot player data.
- Redundant WDA/playerAnimator manual pins were removed after the first real boot: ATM9 1.1.1 already supplies WDA 2.1.58 and the exact playerAnimator dependency. Both features remain, but neither belongs in the 15-jar ZapeG patch.
- Offline access follows the owner's explicit trade-off: whitelist off and `Mizar__107` permanent OP, with nickname/OP spoofing knowingly accepted. Internal RCON stays enabled but its generated password no longer needs host configuration.
- The old chat-only LLM prototype was parked here and is superseded by v0.9.0's Citizens architecture. Heraldor continues to use its embedded line pools by default.
- Post-add material/structure overlap audit is clean; watch-items remain night pressure and structure density (`BALANCE.md`).

## ✅ v0.8.0 (now) — content drop 2 + Heraldor awakens

- **Combat/exploration work** (all pre-world, verified 1.20.1 Forge): Aquamirae, Born in Chaos, Simply Swords and Better Combat were manual additions; Incendium is server-only. WDA and playerAnimator were initially declared here but v0.8.1 established that ATM9 already supplies both. Magic deliberately skipped — ATM9 already ships Eidolon, Forbidden & Arcanus, Mahou Tsukai and Ars Elemental.
- **Heraldor presence engine** (`--profile heraldor`): night-biased whispers only the target sees (+ cave sounds at their position), rare global lines, rarest Discord webhook posts. Staged: midnight shadow visits (self-despawning named vexes; `HERALDOR_EVENTS`). Optional LLM-generated lines (`HERALDOR_LLM`).

### Heraldor arc (the long game)

1. **Presence** (shipped) — whispers, sightings-by-sound, Discord intrusions. Nobody's told; let them figure it out.
2. **Servants** (first rehearsal built) — deterministic tagged minions, sparse victory-triggered responses and later output-only Discord audio.
3. **Manifestation** — a fleeting, gaze-aware, target-private apparition only after the mystery earns a coordinated client update.
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
- **Login-lines mechanism shipped** (`zapeg_welcome.js`) with nine personal pools: five exact usernames plus four temporary real-name keys
- **Build-ClientZip.ps1** — builds both the one-zip licensed patch (`-PatchOnly`) and offline game-directory payload

## v0.5.x — the lore era (first weeks)

- **Lore datapack**: hand-built structures seeded in unexplored territory — "ZapeG Araştırma Tesisi" ruins, Turkish lore books referencing group history. New-chunks-only = world-safe. **Blocked on: in-jokes/lore input from the group.**
- **Real login lines**: nine pools are live; Enes, Yusuf, Ali and the other Mert still need exact Minecraft usernames.
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
