# Changelog

Format per entry: what changed · world risk · what players must do.

## Unreleased — target v0.8.1

Novice-proof client onboarding + operator clarity + pre-launch personalization. World risk: none (pre-world; KubeJS/access settings included). Players: licensed users now install ATM9 1.1.1 and extract **one** ZapeG patch into the profile root.

- `Build-ClientZip.ps1 -PatchOnly` produces `ZapeG-Kurulum-Yamasi-ATM9-1.1.1-<date>.zip` with all 17 client additions, the shader setting, PackMenu branding, an in-zip Turkish quick guide and SHA-256 manifest; it preserves personal `options.txt` settings.
- Builder parses the source CurseForge metadata for ATM9/Forge plus the fifteen CurseForge addition file IDs, requires all 17 exact filenames, and requires reviewed SHA-256 locks for both patch and offline payload builds. Legacy `-ExtrasOnly` remains an alias.
- Server and clients now use Forge 47.4.10 over ATM9's 47.4.0 manifest pin; the three pulled Easy NPC/Aquamirae dependencies are included in the generated patch. Offline output is an isolated Forge 47.4.10 **game-directory payload**, not a launcher/Forge installer.
- Player Markdown/HTML guides use the one-zip path; the seventeen-jar table is technical fallback only and stale “3 jar” troubleshooting text is gone.
- `.env.example` and HOSTING now make the boundary explicit: default `mc + backup` uses no LLM; Muhtar is an optional LLM profile; Heraldor is LLM-free by default; normal Discord uses a bot config while Heraldor optionally uses a separate webhook. Heraldor timing/probability knobs are now actually passed through Compose.
- Conservative physics-ship phase 1 added: Valkyrien Skies 2.4.11 + Eureka 1.6.3. Trackwork stays behind a smoke test; Create: Interactive and Clockwork are deliberately omitted on ATM9's Create 6.0.6.
- Incendium's formerly floating Modrinth project reference is now pinned to 5.3.1.
- README/HOSTING mod counts and default-stack start command corrected: 21 additions total, and `docker compose up -d` starts both `mc` and `backup`.
- Heraldor's default probabilities were reduced to match the locked rare-ARG intent; its Discord roll remains independent of player presence.
- Heraldor shadow summons now encode the JSON custom name as a valid SNBT string even though the Turkish name contains an apostrophe.
- v0.8 overlap audit is recorded in `BALANCE.md`; no recipe/economy changes were required.
- Added exact-name personalization for `eminomi12` (Emin Taha) and `MubarekAbi` (Mert): per-login joke pools, named first-join gifts (`Hayvanat Bahçesi Ruhsatı` / `Araba Modu Gelene Kadar`) and Muhtar dossiers. Roster and server slots now reflect 10 players.
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
