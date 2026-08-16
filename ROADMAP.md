# ZapeG Roadmap

Not everything in v1 — each phase ships through the UPDATING.md ritual. World-risk notes per item.

## 🛠️ v0.8.1 (working tree) — one-patch onboarding + overlap audit

- Licensed-player path is now ATM9 1.1.1 + one profile-root `ZapeG-Kurulum-Yamasi` zip. No individual jar downloads and no second defaults zip.
- Client builder validates structured ATM9/Forge metadata, fifteen CurseForge file IDs, all 17 exact filenames and reviewed SHA-256 locks; it preserves licensed players' personal settings. Offline payloads use a separate reviewed complete-mod inventory lock.
- Server/client loader override is Forge 47.4.10; offline output is accurately framed as an isolated Forge 47.4.10 game-directory payload.
- Valkyrien Skies 2.4.11 + Eureka 1.6.3 are the conservative physics-ship phase 1. Trackwork is a post-smoke-test candidate; Interactive/Clockwork wait on a deliberate Create-stack migration, not a blind drop-in.
- Env docs distinguish the default LLM-free stack from optional Muhtar/Heraldor profiles; Discord bot config and Heraldor webhook are separate mechanisms.
- `eminomi12` and `MubarekAbi` now have exact-name welcome pools, first-login gifts and Muhtar dossiers; the live roster and slots are 10.
- Offline access defaults are explicit: whitelist on, permanent OP empty, internal RCON required. Whitelist can be disabled only when a VPN/firewall gates `25565`.
- Post-add material/structure overlap audit is clean; watch-items remain night pressure and structure density (`BALANCE.md`).

## ✅ v0.8.0 (now) — content drop 2 + Heraldor awakens

- **Combat/exploration adds** (all pre-world, verified 1.20.1 Forge): Aquamirae, Born in Chaos, When Dungeons Arise, Simply Swords, Better Combat (+playerAnimator dep), Incendium (server-only nether overhaul). Magic deliberately skipped — ATM9 already ships Eidolon, Forbidden & Arcanus, Mahou Tsukai, Ars Elemental. Client jars now **12**; v0.8.1 wraps them with defaults/branding into one profile-root patch.
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
- **Login-lines mechanism shipped** (`zapeg_welcome.js`) with nine personal pools: four exact usernames plus five temporary real-name keys
- **Build-ClientZip.ps1** — builds both the one-zip licensed patch (`-PatchOnly`) and offline game-directory payload

## v0.5.x — the lore era (first weeks)

- **Lore datapack**: hand-built structures seeded in unexplored territory — "ZapeG Araştırma Tesisi" ruins, Turkish lore books referencing group history. New-chunks-only = world-safe. **Blocked on: in-jokes/lore input from the group.**
- **Real login lines**: nine pools are live; only Enes/Salih/Yusuf/Ali/Mert still need exact Minecraft usernames.
- **Milestone gift items v2**: awarded live at the moment (KubeJS advancement hooks) instead of via quest claim.
- Playtest-driven trims (remove what nobody touches; Apotheosis/dragon/Mowzie's spawn tuning if needed).

## ✅ v0.7.0 (now) — Muhtar is EMBODIED (verdict: possible, LLM stays)

Feasibility question settled. Three grades, first one shipped:

1. **Shipped — Easy NPC body + LLM brain**: Easy NPC (pinned, client+server) provides a real in-world entity — custom skin, name, poses, stays where placed, players see and walk up to him in the town square. The `npc/` brain (log→LLM→rcon) speaks as him; when he answers, sound + particles fire **at the body's position** (`NPC_POS` in `.env`). Placement: HOSTING §Muhtar.
2. **Next (cheap)**: Easy NPC dialog hooks + follow mode — guided tours, "Muhtar seni gezdirsin".
3. **Endgame (SEPARATE PROJECT — decided)**: custom Forge mod `zapeg-mod` — LLM-driven walking/pathfinding, right-click dialogue, per-player memory; same entity tech later powers Heraldor's manifestation. This is its own repo + its own sessions (brief §8 Tier 2, MDK 1.20.1 + agent guardrails). The headless-modded-client+Baritone route stays documented as the fallback experiment if the mod route stalls.

Dead end, documented: bot-as-player (Mineflayer) can't pass Forge's ~440-mod handshake; a headless *modded* client + Baritone could, but it's a fragile 8GB-RAM contraption — the custom mod is the better road to a walking Muhtar.

## 🧊 Parked

- Weekly bounty board (KubeJS rotating objectives)
- Tablist polish / TPS in tab
- Shader recommendation doc for capable PCs (Complementary ships in pack options)
- ZapeG Ödülleri ceremony automation (scoreboard snapshot → yearly awards)
