# ZapeG Roadmap

Not everything in v1 — each phase ships through the UPDATING.md ritual. World-risk notes per item.

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

Boot → seed audition → real world → gamerules → pregen → clients → **instance zip for offline players** → play. First playtest feedback decides everything below.

## ✅ v0.5.0 (now) — metrics + scaffolds

- **Grafana stack shipped** (`--profile metrics`): minecraft-exporter + Prometheus (180d) + Grafana `:3000`, pre-provisioned dashboard (online, playtime, deaths, blocks, distance) → yearly **ZapeG Ödülleri** reads straight off it
- **Login-lines mechanism shipped** (`zapeg_welcome.js`) with placeholder pools — swap in real jokes + exact usernames
- **Build-ClientZip.ps1** — one command turns Ertu's CurseForge profile into the Yol B instance zip

## v0.5.x — the lore era (first weeks)

- **Lore datapack**: hand-built structures seeded in unexplored territory — "ZapeG Araştırma Tesisi" ruins, Turkish lore books referencing group history. New-chunks-only = world-safe. **Blocked on: in-jokes/lore input from the group.**
- **Real login lines**: mechanism is live; still blocked on the jokes + Minecraft usernames.
- **Milestone gift items v2**: awarded live at the moment (KubeJS advancement hooks) instead of via quest claim.
- Playtest-driven trims (remove what nobody touches; Apotheosis/dragon/Mowzie's spawn tuning if needed).

## v0.6 — LLM NPCs (near future, experimental)

Goal: characters in the world you can actually talk to.

- **Route A (recommended start)**: offline-mode makes bot *players* trivial — a **Mineflayer** container joins as a whitelisted account (e.g. "Muhtar"), LLM loop drives Turkish chat + persona; mineflayer-pathfinder for walking/following; lives in the town hall, answers pack/quest questions, spreads rumors about dungeon locations.
- Guardrails: rate limit + daily token budget, no OP, chat-only tools first (no inventory/griefing verbs), kill-switch in compose.
- **Route B (later)**: in-world mod route (custom entities with dialogue UI) — real Forge mod territory, brief §8 Tier 2.
- Prototype scope: ONE NPC, chat-only, measure cost/fun before scaling.

## 🧊 Parked

- Weekly bounty board (KubeJS rotating objectives)
- Tablist polish / TPS in tab
- Shader recommendation doc for capable PCs (Complementary ships in pack options)
- ZapeG Ödülleri ceremony automation (scoreboard snapshot → yearly awards)
