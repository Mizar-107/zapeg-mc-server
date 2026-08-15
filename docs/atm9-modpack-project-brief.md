# Custom Modpack Project Brief — ATM9 Base

> Context for a coding agent. This project builds a self-hosted Minecraft modpack for a private friend group by **trimming and extending ATM9 (All the Mods 9)**. All decisions below were made deliberately — don't relitigate them without a flag.

---

## 1. Goal & Audience

- Private multiplayer server, **4–8 players**, self-hosted by the owner (a DevOps engineer — hardware is NOT a bottleneck, Docker/automation welcome).
- Pack should be **broad and long-lasting**: technology, magic, boss fights, exploration, space, decoration/city-building — "a path to follow for every type of player."
- A **quest book as a loose guide** is desired (not gating, just direction).

### Original requirements (Turkish, verbatim)

> 1) Gelişmek için inanılmaz efor gerekmemeli
> 2) Oyun sonuna doğru böyle milyonlara doğru scale olmak istemiyorum pek
> 3) Herkese göre birşey olsun, kendimiz host edeceğiz. Kapsamlı ve nispeten uzun olsun. Teknoloji, büyü, boss-fightlar olsun.
> Olsa iyi olur: uzay, ejderha, keşif, silahlar. Sunucu çığrından çıkmasın, hepimiz istediğimiz ipin ucunu kovalayabilelim. Mümkün olduğunca güncel ve customize edebilelim gerekirse. Dekor modları, şehir yapabilelim.

### Interpreted constraints (locked)

| # | Constraint | Implementation decision |
|---|---|---|
| 1 | Progression must not require insane effort | No expert packs. Kitchen-sink base, no recipe overhaul. |
| 2 | No endgame scaling into millions/billions | Treat ATM Star / "Gregstar" as non-goals; tune or remove worst offenders (see §5). |
| 3 | Something for everyone, server stays sane | Broad pack + performance discipline (§6). |
| 4 | Nice-to-haves: space, dragons, exploration, weapons | Ad Astra (in pack), Ice and Fire (manual add), fantasy weapons sufficient — no gun mods needed. |
| 5 | City building: decor → automation → citizens (depth tiers) | Macaw's/Supplementaries (in pack), Create (in pack), MineColonies (in pack). |
| 6 | Magic: cool/unique stuff, no hard preference | Ars Nouveau, Iron's Spells, Botania, Occultism etc. (all in pack). |
| 7 | Boss fights wanted; dragons themselves optional | Cataclysm + Aether + Apotheosis (in pack); Ice and Fire added anyway per #4. |
| 8 | Prefer easiest path; build-up liked for customizability but trim-down wins on compat | **Trim-down from ATM9.** |
| 9 | Owner is confident vibecoding; may write a custom mod later | KubeJS first (ships with ATM9), real Forge mod only if needed (§8). |

---

## 2. Locked Technical Decisions

| Decision | Value | Rationale |
|---|---|---|
| Minecraft version | **1.20.1** | Deepest mature mod catalog; everything on the wishlist has official 1.20.1 builds. On 1.21.1, Ice and Fire exists only as an unofficial Community Edition fork. |
| Loader | **Forge 1.20.1** (pack pins Forge 47.3.29) | Follows ATM9. Note: some 1.20.1 jars are marked "NeoForge" on CurseForge but run on Forge 1.20.1 (NeoForge 1.20.1 was Forge-compatible). |
| Base pack | **ATM9** (latest release; v1.1.1, Oct 2025 at time of research) | ~432 mods, 12.6M downloads, actively maintained, FTB Quests book included, KubeJS included. |
| Strategy | Trim + extend, not build-up | Compatibility and integration already solved by the ATM team. |
| Java | **Java 17** (server and client) | Required by MC 1.20.1 Forge. |

Rejected alternatives: ATM10 (1.21.1 — Ice and Fire only unofficial), expert packs / GTNH-style (violates constraints 1–2), adventure-only packs like Better MC / Prominence II (would require bolting on all tech — more compat risk).

---

## 3. What ATM9 Already Ships (do not re-add)

Verified against the pack's changelog/mod lists at time of research:

| Requirement | Covered by |
|---|---|
| Space | Ad Astra + Ad Astra Giselle Addon |
| Nuclear reactors | Mekanism (+ Generators: fission/fusion), Extreme Reactors 2 |
| Citizens / colony sim | MineColonies + StyleColonies |
| Automation / factory | Create (+ Steam 'n' Rails, Create: New Age, Create Crafts & Additions), Immersive Engineering, PneumaticCraft, Industrial Foregoing, Thermal series, Powah, RFTools, Integrated Dynamics/Tunnels, Railcraft Reborn |
| Magic | Ars Nouveau, Iron's Spells 'n Spellbooks, Botania, Occultism, Blood Magic, Theurgy, EvilCraft, Apotheosis |
| Bosses | L_Ender's Cataclysm (pack-tuned by ATM team), The Aether, Apotheosis bosses, Draconic Evolution chaos guardian |
| Exploration | ChoiceTheorem's Overhauled Villages (CTOV), Dungeon Crawl, Stargate Journey, Ad Astra planets |
| Decoration | Macaw's suite, Supplementaries, Amendments, Absent by Design |
| Food/farming | Farmer's Delight, Croptopia, Cooking for Blockheads, Mystical Agriculture |
| QoL/infra | Sophisticated Storage/Backpacks, Waystones, Traveler's Backpacks, JEI, Jade, FTB Chunks/Teams/Quests, ModernFix, Spark (verify), KubeJS |
| Cool/unique | CC:Tweaked + Advanced Peripherals (Lua-programmable computers), Hostile Neural Networks, Alchemistry, UtilitiX |

---

## 4. Manual Additions (the whole point of the custom build)

Add to **both server and every client** — mod sets must be identical.

### Required

1. **Ice and Fire** — `iceandfire-2.1.13-1.20.1-beta-5.jar` (official Forge 1.20.1 build, Aug 2024) + dependency **Citadel** (latest 1.20.1 build).
   - Not in ATM9 because it was still beta when the pack finalized; community reports confirm it works when dropped into ATM9 (dragons spawn in the overworld normally).
   - **Back up the world before first boot with it.** It's a beta — expect quirks.
   - Config tuning (`iceandfire-common.toml` / cfg): set **dragon griefing to low/none** so wild dragons don't level player cities; consider lowering dragon spawn rate and "dragon roar" griefing.
2. **Immersive Petroleum** — latest 1.20.1 Forge build (oil extraction/processing addon for Immersive Engineering; IE itself is already in the pack).

### Optional (evaluate after first playtest)

- **Twilight Forest** — structured boss-progression dimension (verify not already shipped; if absent, it's a clean add).
- **Mowzie's Mobs** — high-quality boss creatures.
- **Alex's Caves** — 5 cave biomes with own bosses + a literal nuke item; shares Citadel dep with Ice and Fire.
- **Handcrafted / FramedBlocks / Chipped / Rechiseled** — extra decor if the shipped set feels thin (check what's already in first).
- **Chunky** — world pregeneration (add if not shipped).
- Server-side only candidates: **Spark** (profiler), **FerriteCore** (RAM), **Krypton** (network) — add only if missing; ATM9 already ships ModernFix.

---

## 5. Endgame Scaling Policy ("no millions" rule)

The big-number content in ATM9 is all optional endgame: **ATM Star**, **"Gregstar"** (GTCEu is shipped as an optional dare), **Draconic Evolution** (billion-RF tier), **Mystical Agriculture** (infinite resources).

Implement in escalating order — stop at the lowest level the group is happy with:

1. **Social rule (default):** quest book used as per-mod guide; final Star/Gregstar chapters simply not pursued. Zero work.
2. **Quest edit:** delete or rewrite the endgame chapters (FTB Quests files are plain data — editable directly or in-game with OP perms).
3. **KubeJS tuning:** nerf/remove specific recipes. ATM9 ships KubeJS and the ATM team itself adds custom recipes with it (e.g., the Micro Universe Orb), so `kubejs/server_scripts/` is the sanctioned hook. Example pattern:

   ```js
   // kubejs/server_scripts/endgame_nerfs.js
   ServerEvents.recipes(event => {
     event.remove({ output: 'draconicevolution:chaos_shard' }) // example only
   })
   ```
4. **Nuclear option:** remove Draconic Evolution entirely (nothing else depends on it).

---

## 6. Server Configuration

| Setting | Value | Notes |
|---|---|---|
| Heap | **10–12 GB** | ATM team guidance: 8–12 GB; **do not exceed ~12 GB** (GC behavior degrades). |
| JVM | Java 17, G1GC with standard Minecraft flags (Aikar's flags fine) | |
| `view-distance` | 6–8 | Simulation distance 6 or lower. |
| Pregen | Chunky: pregenerate ~5–8k block radius of spawn before opening | Prevents exploration lag spikes. |
| Profiling | Spark on standby; investigate before adding more "performance" mods | |
| Backups | Daily automated + pre-any-mod-change manual snapshot | Non-negotiable given Ice and Fire beta. |
| Deployment | Docker preferred: `itzg/minecraft-server` supports CurseForge packs (AUTO_CURSEFORGE with API key) or plain Forge installer + mounted mods | Owner is a DevOps engineer — infra-as-code welcome. |
| Client RAM | 8–12 GB allocated in launcher | |

---

## 7. Client Distribution

- Build the pack as a CurseForge profile based on ATM9 + manual jars; **export with overrides** so the manually added jars (Ice and Fire, Citadel, Immersive Petroleum) travel inside the export zip.
- Alternative (owner preference, git-friendly): **packwiz** CLI — TOML metadata in git, `packwiz modrinth|curseforge install`, `packwiz update --all`, export to both CurseForge and Modrinth formats. Good fit for agent-driven maintenance.
- Every player must run the identical mod set; version-pin the export.

---

## 8. Custom Mod / Scripting Path (vibecoding notes)

- **Tier 1 — KubeJS** (start here): recipes, item tweaks, quest rewards, simple custom items. Plain JavaScript, hot-reloadable via `/kubejs reload server_scripts`. Covers ~80% of "custom content" desires.
- **Tier 2 — real Forge mod** only if KubeJS can't express it: Forge MDK 1.20.1 or IntelliJ + Minecraft Development plugin, Gradle, `runClient` for testing.
- **Agent guardrails (learned from published vibe-coding post-mortems):**
  - LLMs freely mix APIs across Minecraft versions — **always pin "Minecraft 1.20.1 + Forge 47.3.x + Mojmap" in rules files** and reject anything referencing other versions.
  - Use a docs-pinning tool (e.g., Context7 MCP) for KubeJS/Forge docs.
  - Add a rules file telling the agent not to grep build/output dirs (wastes context).
  - Iterate against real feedback: server log on boot, `/kubejs errors`, in-game test — agents self-correct well from build/runtime errors.

---

## 9. Phased Task Plan for the Agent

- [ ] **Phase 1 — Base server up:** fetch ATM9 server files (latest 1.20.1 release), Java 17, first clean boot, ops/whitelist, verify 10–12 GB heap, baseline `/forge mods` list saved to repo.
- [ ] **Phase 2 — Manual mods:** add Ice and Fire + Citadel + Immersive Petroleum (clients too), boot test, confirm worldgen (dragon roosts, oil reservoirs) in a throwaway world first. Snapshot before/after.
- [ ] **Phase 3 — World prep:** fresh world, Chunky pregen, set world spawn, difficulty/gamerules, verify performance mods present (ModernFix etc.), add Spark/Chunky if missing.
- [ ] **Phase 4 — Tuning:** Ice and Fire griefing config, endgame policy level from §5 (default: level 1 + prepare level 2 quest edits), any recipe nerfs via KubeJS.
- [ ] **Phase 5 — Client export:** CurseForge export with overrides (or packwiz repo), smoke-test on a second machine, distribute.
- [ ] **Phase 6 — Playtest checklist:** each "player path" smoke-tested — Create contraption, IE multiblock, Mekanism fission, MineColonies town hall, Ars Nouveau spell, Ad Astra rocket, one Cataclysm boss, dragon encounter.

## 10. Verify-At-Build-Time List (research was snapshot-based)

- Exact latest ATM9 version and its pinned Forge version (use the pack's own server files, don't hand-pick Forge).
- Whether current ATM9 already ships: Immersive Petroleum, Twilight Forest, Alex's Caves, Spark, Chunky, FerriteCore — check `/mods` output before adding anything.
- Ice and Fire 1.20.1: check for any newer official build than 2.1.13-beta-5; re-check known-issues threads.
- Immersive Petroleum 1.20.1: latest build number; confirm Forge (not only NeoForge-marked) jar.

## 11. Key Sources

- [ATM9 on CurseForge](https://www.curseforge.com/minecraft/modpacks/all-the-mods-9) — pack page, 12.6M downloads
- [AllTheMods/ATM-9 GitHub](https://github.com/AllTheMods/ATM-9) — configs, scripts, issue tracker (also: "ATM9 No Frills" lighter variant exists)
- [ATM9 server wiki (SiriusMC)](https://wiki.siriusmc.net/books/server-information/page/atm9-all-the-mods-9) — RAM guidance, changelog-derived mod list
- [ATM9 mod list (Modpack Index)](https://www.modpackindex.com/modpack/64056/all-the-mods-9-atm9)
- [Ice and Fire 1.20.1 file](https://www.curseforge.com/minecraft/mc-mods/ice-and-fire-dragons/files/5633453)
- [r/allthemods — adding Ice and Fire to ATM9](https://www.reddit.com/r/ModdedMinecraft/comments/1g4bk9u/) — community experience: works, back up first
- [r/allthemods — ATM9 content mod reference](https://www.reddit.com/r/allthemods/comments/185mgj0/) — confirms Immersive Engineering in pack
- [packwiz](https://github.com/packwiz/packwiz) — git-friendly pack management
- [Vibe-coding Minecraft mods (Max Leiter)](https://maxleiter.com/blog/vibecoding-minecraft-mods) — agent guardrails in §8

---

## 12. Build-Time Verification Results (2026-08-15) — §10 executed

| Item | Finding | Action |
|---|---|---|
| Latest ATM9 | **1.1.1** (2025-10-12) still latest; client file `7097953`, server files `7097957`; pins **Forge 47.4.0** (not 47.3.29 as researched earlier) | Pinned via `CF_FILE_ID` in server repo |
| Twilight Forest | **Already in ATM9** (4.3.2508 in the pack's 435-mod list) | Removed from §4 optional adds |
| Spark / FerriteCore / ModernFix | All in pack | No action |
| Chunky | Not in pack; **no 1.20.1 Forge build on CurseForge at all** | Added server-side from Modrinth (`chunky:1.3.146`) via `MODRINTH_PROJECTS` |
| Ice and Fire | `2.1.13-1.20.1-beta-5` (file `5633453`) still newest official 1.20.1 build; beta-5 fixed Citadel 2.6.x incompat (beta-4 required Citadel ≤2.5.99) | Pinned in `extras/cf-mods.txt` |
| Citadel | Latest 1.20.1 = **2.6.3** (2026-01-17, file `7476570`) | Pinned; fallback 2.6.1 (`6002521`) documented if version-range gate trips |
| Immersive Petroleum | **4.3.1-36b** (2026-07-24, file `8499079`), Forge jar confirmed, actively maintained | Pinned |
| Alex's Caves / Mowzie's | Not in pack (confirmed) | Stay in §4 optional, post-playtest |

Server repo scaffolded at `server/` (docker-compose with itzg AUTO_CURSEFORGE + mc-backup sidecar, declarative mod pins, snapshot/pregen/override scripts, runbook README). Phases 1–2 of §9 are now "run `docker compose up`" on the host.
