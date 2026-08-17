# Changelog

Format per entry: what changed · world risk · what players must do.

## Unreleased — target v0.9.0

Player- and server-owned LLM citizens plus the official Immersive Vehicles stack
and experimental Nifty Ships core. World risk: low for IV; Nifty adds unfinished
hulls only to new chunks. First citizen and vehicle/ship tests belong in a
disposable unclaimed world; removing either vehicle system after content or cargo
exists is high risk. Players: install the new 23-jar ZapeG patch before joining.

- Added Numen AI 0.1.1 (CurseForge file `8551640`) and the reviewed ZapeG Citizens 0.3.0 Forge jar to both the server and client inventory locks.
- Replaced ATM9's CC:Tweaked 1.113.1 with the required 1.116.1 on server, patch and offline payload; builders and rollout guides remove older CC/Citizens copies and verify a single exact jar for each mod ID.
- Added `/citizen spawn <name> <onlinePlayer>`, assignment-aware chat routing, all 32 server-executable Numen tools, per-citizen/per-actor memory, stop/remove safety and bounded whole-turn timeouts. Citizens can use Numen's movement, mining, building, crafting, storage, item-transfer, interaction and combat capabilities; only its two client-only tools remain unavailable to the server controller.
- Added true server-owned lore citizens: `/citizen spawn-server`, persistent persona/home, public no-tool player dialogue, OP-only physical tasks, restart wake-up, chunk tickets, death recovery and fail-closed identity checks. Server-owned bodies use a durable world principal rather than pretending to belong to a player.
- Added one private `citizen-brain` Compose service. A single host-owned Ollama key serves every citizen; players never run the service or receive the key.
- Added `docs/CITIZENS-HOST-SETUP.md` with secret creation, pinned brain build, startup, health checks, acceptance test, rollback and troubleshooting commands.
- The shared brain has no published host port, receives no Minecraft data/RCON/Docker socket, runs read-only without Linux capabilities and keeps SQLite state in its own named volume.
- The custom Citizens release jar is tracked in `overrides/mods/` and locked by SHA-256; the brain image builds from the public `zapeg-citizens` tag `v0.3.0`. The v0.3.0 jar and protocol-v2 brain must be deployed together.
- Removed the obsolete single-character log-tail chat prototype and its persona. Easy NPC remains for lore/quest characters; Heraldor remains an independent optional service.
- Added Immersive Vehicles 24.0.0 (CurseForge file `7926604`), MTS Official Pack V29 (`7933733`) and MTS Official Automobile Pack V3 (`7933540`) as an exact client+server dependency set. IV 24.0.0 is the native Forge 1.20.1 release that fixes the Ad Astra startup crash; broader community-pack expansion is deferred until the official baseline passes playtesting.
- Added an authoritative Entity Culling client default that render-whitelists IV's three builder entities; both patch and offline builds now require and verify that config. Operator/player guidance covers shader text visibility and the unsupported collision boundary with moving Eureka/VS ships and Create contraptions.
- Added a fail-closed admission/promotion gate for every future mod and addon: balance, duplicate content, dependency closure, compatibility, world/removal risk and multiplayer persistence must be reviewed before an active pin reaches players or production.
- Added Aleki's Nifty Ships core 1.0.14 (CurseForge file `5963449`) to both server and client under an explicit owner-approved experimental waiver. Its loader/dependency/economy checks pass, but unresolved upstream chunk-reload mooring, drift, anchor and rendering defects remain copied-world promotion gates. The official BOP addon crashes against ATM9's BOP 19.0.0.96 API, so core only is included; MuddyPatch, every-wood and Firma addons remain out. Generated artifacts include the upstream MIT notice omitted from the published jar.
- Rethemed MertOnal's existing minecart gift, welcome line and 5 km quest as a keepsake/farewell to the pre-car era; task IDs, progress criteria and rewards are unchanged.
- Added ZapeG Runtime 0.1.0 as a mandatory client/server owned mod for target-private, camera-aware story scenes. Its first `echo_01` profile renders no world entity: one selected client sees a malformed silhouette, chromatic afterimages and bounded HUD-edge faults, while direct gaze or hard expiry removes it. Any level-2 in-game OP, console or RCON Director can rehearse/trigger/cancel scenes through `/zapegscene`; command blocks and functions are excluded.
- Manual additions are now 27 total: 23 client+server and 4 server-only. The generated player patch contains exactly 23 reviewed additions.
- Production scope now includes online player-owned workers plus persistent server-owned lore characters. Ordinary mass enemies and boss mechanics should still use deterministic mob AI; the LLM citizen layer is best used for named characters, dialogue and high-level orders.
- Removed every `checkmark` from all three custom quest pages while preserving existing task IDs. Yol Haritası now requires a real first item/advancement; KubeJS verifies exact-name dragon/diamond/village/tame/fire/chest/minecart objectives; Wither, MineColonies, moon-return, Cataclysm and Chaos Guardian milestones are event-driven; subjective builds require an OP world inspection.
- Added `MertOnal`'s 5 km minecart quest, persistent tame/chest counters and a Turkish migration/test runbook. Group trophy items are claimable once per team. Enes's crossbow remains deliberately locked until his exact login is confirmed.
- Corrected the identity registry: the car-fan Mert previously keyed as `MubarekAbi` is actually `MertOnal`; the other rare Mert returns to the unconfirmed `Mert` placeholder. Salih's exact login is `SalihKarahan`, not the previously recorded `SalihKarahans`. Welcome/gift keys, quest ownership, rewards, offline UUID aliases and documentation now use the corrected identities.
- Added one-shot migrations so `MertOnal` and `SalihKarahan` receive their formerly missed named starter gifts if they already claimed the generic kit under the corrected login. Mert's two additional objectives are an OP-inspected habitable house and 64 distinct exact-actor ray placements that must still exist when counted. Added Emin Taha's OP-inspected public fountain plus separate owner-UUID dragon objectives for Emir and Salih; mounting an owned tamed Ice and Fire dragon also verifies the group milestone.
- Added five owner-tagged quest keepsakes: MertOnal's deed and minecart, Emin's fountain heart, Emir's dragon horn and Salih's dragon flute. KubeJS delivers each once, directly to the exact login, with owner/quest NBT instead of exposing it as a shared FTB Teams claim; a full inventory pauses and retries delivery instead of dropping the item.
- Pinned the metrics images, made Grafana localhost-only/non-anonymous by default, expanded retention to 400 days with a 10 GB cap, added confirmed UUID→login relabels and provisioned TPS/tick-time/entity/player-detail panels. Daily backups now exclude regenerable BlueMap tiles.
- Upgraded Heraldor to a persistent SQLite Director with global/per-player quiet periods, a rolling event budget, at-most-once side effects, world-tokened scoreboard high-water ingestion, a consistent online snapshot under `data/heraldor/`, and an explicit safe snapshot-restore command.
- Added OP-only `/zapeg-lore servant rehearse|awaken <player>` encounters for a target-bound, lootless, XP-less vanilla minion named `Heraldor'un Hizmetkârı`; rehearsals never advance the story, its hidden live tag—not its cosmetic name—authorizes kills, and the third legitimate live victory records one allowlisted audio event. Automatic minion spawning remains disabled.
- Added an opt-in, output-only Discord voice relay plus the first hash-pinned 23.6-second Opus clip (`servants_after_three_v1`). The isolated relay may reuse the existing DCI bot identity or use a dedicated bot; either way it uses a separate secret file, fixed live/test channels, no message intents, no RCON or Minecraft mount, self-deafened one-shot playback, immediate disconnect, short event expiry and terminal crash/no-audience handling so a stale scare can never replay later.
- Added a versioned Easy NPC **Muhtar v1** as a stateless router into the existing ZapeG quest-path cards. His eight quest buttons open real quest IDs for the interacting non-OP player and never modify progress, inventory, rewards or path state. A fixed entity UUID, repo-owned preset mirror, placement helper and Turkish rollback/removal runbook make the whole feature independently reversible. The personal Nemesis idea remains parked.
- Corrected the ZapeG bridge-card directions for ATM9 1.1.1: MineColonies, Immersive Engineering, The Aether and Ice and Fire do not have stock chapters in this exact pack, so their cards now point to the appropriate in-mod tutorial/guide or JEI instead of promising a nonexistent chapter.

## v0.8.1 — 2026-08-16

Novice-proof client onboarding + operator clarity + pre-launch personalization. World risk: none (pre-world; KubeJS/access settings included). Players: licensed users now install ATM9 1.1.1 and extract **one** ZapeG patch into the profile root.

- `Build-ClientZip.ps1 -PatchOnly` produces `ZapeG-Kurulum-Yamasi-ATM9-1.1.1-<date>.zip` with all 15 client additions, the shader setting, PackMenu branding, an in-zip Turkish quick guide and SHA-256 manifest; it preserves personal `options.txt` settings.
- Builder parses current and legacy CurseForge metadata layouts for ATM9/Forge, checks addition file IDs when the app records them, requires all 15 exact filenames, and always requires reviewed SHA-256 locks for both patch and offline payload builds. Legacy `-ExtrasOnly` remains an alias.
- Server and clients now use Forge 47.4.10 over ATM9's 47.4.0 manifest pin; the three pulled Easy NPC/Aquamirae dependencies are included in the generated patch. Offline output is an isolated Forge 47.4.10 **game-directory payload**, not a launcher/Forge installer.
- Player Markdown/HTML guides use the one-zip path; the fifteen-jar table is technical fallback only and stale “3 jar” troubleshooting text is gone.
- `.env.example` and HOSTING now make the boundary explicit: default `mc + backup` uses no LLM; Muhtar is an optional LLM profile; Heraldor is LLM-free by default; normal Discord uses a bot config while Heraldor optionally uses a separate webhook. Heraldor timing/probability knobs are now actually passed through Compose.
- Conservative physics-ship phase 1 added: Valkyrien Skies 2.4.11 + Eureka 1.6.3. Trackwork stays behind a smoke test; Create: Interactive and Clockwork are deliberately omitted on ATM9's Create 6.0.6.
- Incendium's formerly floating Modrinth project reference is now pinned to 5.3.1.
- README/HOSTING mod counts and default-stack start command corrected: 19 additions total, and `docker compose up -d` starts both `mc` and `backup`.
- Removed redundant manual When Dungeons Arise 2.1.57 and playerAnimator declarations from the server/client patch: ATM9 1.1.1 already supplies WDA 2.1.58 (`4983862`) and the exact playerAnimator build (`4587214`). This preserves both features while preventing duplicate-mod-ID omissions; the client builder now defaults to the real CurseForge profile path and accepts the current metadata schema.
- Added reviewed patch/offline SHA-256 inventory locks. The patch lock contains exactly the 15 manual client additions; the full lock excludes an enabled CC:Tweaked 1.116.1 jar that was not in ATM9's manifest and duplicated the pack's `computercraft` mod ID.
- Heraldor's default probabilities were reduced to match the locked rare-ARG intent; its Discord roll remains independent of player presence.
- Heraldor shadow summons now encode the JSON custom name as a valid SNBT string even though the Turkish name contains an apostrophe.
- v0.8 overlap audit is recorded in `BALANCE.md`; no recipe/economy changes were required.
- Added exact-name personalization for `eminomi12` (Emin Taha) and `MertOnal` (Mert): per-login joke pools, named first-join gifts (`Hayvanat Bahçesi Ruhsatı` / `Araba Modu Gelene Kadar`) and Muhtar dossiers. Roster and server slots now reflect 10 players.
- Confirmed Salih's Minecraft name as `SalihKarahan`; his house-burning welcome pool, named flint-and-steel first-login gift and Muhtar dossier now use the exact login key.
- Added a third FTB Quests page titled **ZapeG** for personal lore assignments. Its eight initial objectives are eight independent quest nodes rather than bundled multi-condition tasks: Emir's Ender Dragon and 64-diamond goals; Emin Taha's village and ten-tame goals; Salih's controlled ignition and extinguishing drill; Recep's chest watch; and Enes's crossbow use. Mert deliberately has no filler quest. Initial completion is honor-system/manual until exact-name event automation is runtime-tested.
- Corrected statistics before launch: the dragon-death counter now accepts only Ice and Fire's fire/ice/lightning dragons, the exporter no longer attempts Mojang lookup for offline identities, and Prometheus/Grafana use a one-minute collection/refresh cadence. Upstream exposes offline UUID labels until post-boot friendly aliases are configured.
- Applied the owner's offline access decision: whitelist defaults off and `Mizar__107` defaults to permanent OP; nickname/OP spoofing is explicitly accepted and documented.
- Host-supplied RCON is no longer required for the default stack. Minecraft generates an internal password, live backup/Muhtar/Heraldor discover it through the shared data file, and port 25575 remains unpublished. Only the optional metrics exporter needs an explicit shared override.
- LLM usage is parked for launch: Muhtar remains an opt-in chat-only profile and Heraldor uses embedded text with `HERALDOR_LLM=false`; Ollama is a compatible future option, not a launch dependency.
- Manual snapshots now stop/restart the automatic backup sidecar to avoid save-state races, write through a disposable partial archive, and restore `save-on` through an EXIT trap even when archive/RCON steps fail.
- Fixed the chosen-seed reset protocol to recreate the Minecraft container, so an edited `WORLD_SEED` is actually injected before the real world is generated.
- Corrected the Discord bridge docs: DCI requires a bot token + channel ID and can create its own optional webhook; it cannot consume a supplied raw webhook URL. Heraldor's raw webhook remains separate.
- Replaced the pulled host-specific CPU pin with optional `MC_CPUSET`; blank safely uses all CPUs on a new host.

## v0.8.0 — 2026-08-15

Content drop 2 + Heraldor. World risk: none (pre-world). Players: jar list **6 → 12** — use `zapeg-extra-mods.zip` (one extract) instead of per-file downloads.

- **Added (client+server)**: Aquamirae 7.1.10 (`8558369`), Born in Chaos 1.7.5 (`7917933`), When Dungeons Arise 2.1.57 (`4798432`), Simply Swords 1.56.0 (`5639538`), Better Combat 1.9.0 + playerAnimator 1.0.2-rc1 (Modrinth pins; cloth-config already in pack)
- **Added (server-only)**: Incendium 5.3.1 (Modrinth) — nether overhaul by the Terralith authors
- **Not added, on purpose**: magic mods (ATM9 already ships Eidolon Repraised, Forbidden & Arcanus, Mahou Tsukai, Ars Elemental — saturated); BOMD (no Forge 1.20.1); Epic Fight (compat risk at 440+ mods); From the Fog (conflicts with our own entity's lore)
- **Heraldor** (`npc/heraldor.py`, `--profile heraldor`): night-biased private whispers + creepy sounds, rare global lines, rarest Discord webhook posts; staged midnight shadow visits (`HERALDOR_EVENTS`, default off; self-despawning vexes, no grief); optional LLM lines. Muhtar now refuses to discuss him.
- `Build-ClientZip.ps1 -ExtrasOnly` → `zapeg-extra-mods-<date>.zip` for Yol A players

## v0.7.0 — 2026-08-15

Shaders-by-default + embodied Muhtar. World risk: none (pre-world). Players: jar list **5 → 6** (Easy NPC) + one tiny defaults zip.

- **Default visuals**: ATM9 already bundles Oculus/Embeddium + Complementary shaderpacks — `client/defaults/` (options.txt + oculus.properties) turns **Complementary Unbound ON by default**. Yol A: extract `zapeg-client-defaults.zip` into the profile (guide step added; K toggles, MakeUp-UltraFast as fallback). Yol B: `Build-ClientZip.ps1` now bundles shaderpacks + defaults and auto-detects the actual shaderpack filename.
- **Easy NPC 7.7.7** (`8644040`, client+server): Muhtar's physical body — placed in the town square post-launch, coordinates go into `NPC_POS`; the brain now fires villager sound + particles at the body when he speaks. Feasibility verdict recorded in ROADMAP (bot-as-player = dead end; custom Forge mod = the walking-Muhtar endgame).
- Guides updated: 6 jars, defaults step, Muhtar intro line.

## v0.6.0 — 2026-08-15

Balance pass, personalization, Muhtar NPC, server IP. World risk: none. Players: nothing (IP now in the guides).

- **Balance review** (`BALANCE.md`): silver triple-duplication (ATO+Thermal+I&F) → 1:1 conversion bridge shipped (`zapeg_balance.js`) + post-boot action: I&F silver ORE gen off, sapphire stays. PNC↔IP dual oil = coexists by design. AC materials self-contained. AC nuke removal staged (commented).
- **Personal layer live** (`zapeg_welcome.js`, `zapeg_starter.js`): real welcome pools + named first-join gifts — kralxlarge/Emir (Acele Etme Pusulası), Mizar__107/Recep (Admin Sopası), Enes (Jetpack Ruhu — Iron Jetpacks confirmed in pack), Salih (Çakmağı — Ev Yakmak Yasak), Yusuf/Ali/Mert (pasta). Enes/Salih/Yusuf/Ali/Mert keyed by real name until nicks arrive.
- **Muhtar LLM NPC prototype** (`npc/`, `--profile npc`): log→LLM→tellraw chat-bridge with Turkish persona + player dossier; cooldown/daily-cap guardrails; OpenAI-compatible endpoint via `.env`. (Mineflayer route rejected: vanilla protocol can't pass Forge's modlist handshake on this pack.)
- **Server IP `81.213.77.41`** baked into both player guides.

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
