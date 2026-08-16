# ZapeG Roadmap

Not everything in v1 — each phase ships through the UPDATING.md ritual. World-risk notes per item.

## 🛠️ v0.8.1 (working tree) — one-patch onboarding + overlap audit

- Licensed-player path is now ATM9 1.1.1 + one profile-root `ZapeG-Kurulum-Yamasi` zip. No individual jar downloads and no second defaults zip.
- Client builder validates current/legacy structured ATM9/Forge metadata, fourteen CurseForge file IDs, all 15 exact filenames and reviewed SHA-256 locks; it preserves licensed players' personal settings. Offline payloads use a separate reviewed complete-mod inventory lock.
- Server/client loader override is Forge 47.4.10; offline output is accurately framed as an isolated Forge 47.4.10 game-directory payload.
- Valkyrien Skies 2.4.11 + Eureka 1.6.3 are the conservative physics-ship phase 1. Trackwork is a post-smoke-test candidate; Interactive/Clockwork wait on a deliberate Create-stack migration, not a blind drop-in.
- Env docs distinguish the default LLM-free stack from optional Muhtar/Heraldor profiles; Discord bot config and Heraldor webhook are separate mechanisms.
- `eminomi12` (Emin Taha) and `MubarekAbi` (Mert) now have exact-name welcome pools, first-login gifts and Muhtar dossiers; the live roster and slots are 10.
- `SalihKarahans` is now Salih's confirmed exact login key; his arson-history welcome pool, named flint-and-steel gift and Muhtar dossier are wired to it.
- A third FTB Quests page, **ZapeG**, contains eight independent personal-lore objectives for Emir, Emin Taha, Salih, Recep and Enes. No quest combines two requested conditions; Mert stays intentionally unassigned. The launch-safe first version uses honor-system checkmarks, with exact-name automation added only after runtime event checks.
- Stats correctness pass: dragon deaths use an explicit three-dragon allowlist; the exporter avoids Mojang lookup for offline identities and samples once per minute. Friendly UUID→name dashboard aliases wait for real post-boot player data.
- Redundant WDA/playerAnimator manual pins were removed after the first real boot: ATM9 1.1.1 already supplies WDA 2.1.58 and the exact playerAnimator dependency. Both features remain, but neither belongs in the 15-jar ZapeG patch.
- Offline access follows the owner's explicit trade-off: whitelist off and `Mizar__107` permanent OP, with nickname/OP spoofing knowingly accepted. Internal RCON stays enabled but its generated password no longer needs host configuration.
- LLM work is parked for launch: Muhtar's profile stays off; Heraldor uses its embedded line pools. Ollama remains only a future text-generation option.
- Post-add material/structure overlap audit is clean; watch-items remain night pressure and structure density (`BALANCE.md`).

## ✅ v0.8.0 (now) — content drop 2 + Heraldor awakens

- **Combat/exploration work** (all pre-world, verified 1.20.1 Forge): Aquamirae, Born in Chaos, Simply Swords and Better Combat were manual additions; Incendium is server-only. WDA and playerAnimator were initially declared here but v0.8.1 established that ATM9 already supplies both. Magic deliberately skipped — ATM9 already ships Eidolon, Forbidden & Arcanus, Mahou Tsukai and Ars Elemental.
- **Heraldor presence engine** (`--profile heraldor`): night-biased whispers only the target sees (+ cave sounds at their position), rare global lines, rarest Discord webhook posts. Staged: midnight shadow visits (self-despawning named vexes; `HERALDOR_EVENTS`). Muhtar refuses to speak his name. Optional LLM-generated lines (`HERALDOR_LLM`).

### Heraldor arc (the long game)

1. **Presence** (shipped) — whispers, sightings-by-sound, Discord intrusions. Nobody's told; let them figure it out.
2. **Lore era** — his ruins in the lore datapack; Born in Chaos mobs canonically become his forces; books hint at his name.
3. **Manifestation** — summonable boss fight: reskinned/custom-named elite (Cataclysm/Mowzie's base via summon NBT) → ultimately a real custom entity in the ZapeG mod.

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
- **Real login lines**: nine pools are live; only Enes, Yusuf, Ali and the other Mert still need exact Minecraft usernames.
- **Milestone gift items v2**: awarded live at the moment (KubeJS advancement hooks) instead of via quest claim.
- Playtest-driven trims (remove what nobody touches; Apotheosis/dragon/Mowzie's spawn tuning if needed).

## ✅ v0.7.0 (shipped scaffold; LLM parked for launch) — Muhtar is EMBODIED

Feasibility question settled. Three grades, first one shipped:

1. **Shipped scaffold — Easy NPC body + optional LLM brain**: Easy NPC (pinned, client+server) provides a real in-world entity — custom skin, name, poses, stays where placed, players see and walk up to him in the town square. The optional `npc/` brain only turns `muhtar` chat mentions into generated text via log→LLM→rcon; it is parked for launch. When enabled later, sound + particles fire **at the body's position** (`NPC_POS` in `.env`). Placement: HOSTING §Muhtar.
2. **Next (cheap)**: Easy NPC dialog hooks + follow mode — guided tours, "Muhtar seni gezdirsin".
3. **Endgame (SEPARATE PROJECT — decided)**: custom Forge mod `zapeg-mod` — LLM-driven walking/pathfinding, right-click dialogue, per-player memory; same entity tech later powers Heraldor's manifestation. This is its own repo + its own sessions (brief §8 Tier 2, MDK 1.20.1 + agent guardrails). The headless-modded-client+Baritone route stays documented as the fallback experiment if the mod route stalls.

Dead end, documented: bot-as-player (Mineflayer) can't pass Forge's ~440-mod handshake; a headless *modded* client + Baritone could, but it's a fragile 8GB-RAM contraption — the custom mod is the better road to a walking Muhtar.

## 🧊 Parked

- Weekly bounty board (KubeJS rotating objectives)
- Tablist polish / TPS in tab
- Shader recommendation doc for capable PCs (Complementary ships in pack options)
- ZapeG Ödülleri ceremony automation (scoreboard snapshot → yearly awards)
