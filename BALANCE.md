# BALANCE — duplicate-material & balance review (2026-08-17, pre-launch)

Scope: what ZapeG's manual content additions do to ATM9's economy. Verified against the pack's own file list and configs where possible; items marked *verify at boot* get checked in the throwaway world.

## Findings

| # | Finding | Verdict | Action |
|---|---|---|---|
| 1 | **Silver duplication** — base pack already has silver twice (AllTheOres + Thermal, unified via `forge:ingots/silver` tags). Ice and Fire adds a third: own ore worldgen + own ingot, used by its silver weapons / dragonsteel chain. Tag-based recipes interchange, but I&F-specific recipes want its exact item, and double ore veins are clutter | Real, mild | **Shipped**: `zapeg_balance.js` 1:1 two-way ingot conversion. **Post-boot**: I&F config → silver ORE generation off (ATO veins remain the single silver source; I&F silver stays obtainable via conversion + roost loot). Sapphire gen stays ON — unique to I&F. *Verify exact config key at boot via `scripts/iceandfire-config-check.sh`* |
| 2 | **Two oil systems** — PneumaticCraft (in pack) has surface oil lakes; Immersive Petroleum adds underground reservoirs + pumpjack | Not a conflict | Keep both — separate tech trees, both fluids serve their own mods (partial tag interop is a bonus where it exists). Revisit only if surface lakes feel spammy (PNC config can lower lake frequency) |
| 3 | **Alex's Caves materials** (neodymium pair, cave uranium, etc.) vs Mekanism/ATO uranium | By design | AC's economy is deliberately self-contained (own items, own recipes). No unification needed; Mekanism chain untouched |
| 4 | **Mowzie's Mobs** | No ores | Boss-drop items are strong but earned; configs exist if a drop feels broken post-playtest |
| 5 | **AC nuclear bomb** exists (cave uranium) | Social rule | Recipe-removal one-liner staged (commented) in `zapeg_balance.js` if the social rule fails |
| 6 | **Progression pace** | Baseline | ATM9 kitchen-sink with no recipe overhaul IS the low-grind mode; stars stay craftable per the natural-progression decision (v0.3.1). Nothing to tune pre-playtest |
| 7 | **v0.8.0 overlap audit** (post-add self-check) | Clean | Aquamirae vs pack's Aquaculture = horror biome vs fishing rods, no overlap. ATM9 1.1.1 already supplies WDA 2.1.58; the redundant ZapeG 2.1.57 declaration was removed, while its mega-dungeon niche remains. Structure layers by size (CTOV villages / Structory ruins / YUNG temples / WDA complexes). Simply Swords vs Silent Gear = found-loot vs crafted-gear systems, coexist. Two watch-items for playtest: combined night pressure (Born in Chaos + Apotheosis elites) and total structure density — both are config dials |
| 8 | **Immersive Vehicles transport/fuel overlap** | Compatible with a boundary | Keep IV for road/terrain vehicles and VS/Eureka for moving ships; do not expect IV collision on ship decks or Create contraptions. Inspect the generated IV fuel config in the throwaway boot before changing recipes: do not assume Immersive Petroleum or PneumaticCraft fuels are mapped. Map one existing fuel family only after its exact fluid IDs and consumption balance are verified; avoid adding a third oil worldgen system |
| 9 | **Aleki's Nifty Ships 1.0.14 core** | Economy clean; known compatibility risk accepted — **experimental** | It adds no ore, fluid, energy or library and uses moderate vanilla wood/iron/wool recipes. Its fixed sailing entities overlap Eureka's ship fantasy but not its arbitrary block-ship engineering, creating a third independent moving-vehicle physics stack beside Eureka/VS and IV. Generated unfinished boats also increase beach/river structure density and can shortcut part of the hull cost. The owner chose the age-of-sail loop with the known upstream chunk-reload mooring, drift, anchor and visibility defects recorded; core only is pinned, all BOP/every-wood/Firma addons stay out, and copied-world multiplayer persistence remains a promotion gate. |

## Rules for future adds

- Every candidate must pass the admission and promotion checks in
  `UPDATING.md`'s **Mandatory mod-add gate**. Balance, duplicate-content and
  compatibility findings are recorded before the mod becomes an active pin;
  uncertainty means defer, not assume.
- Any new mod that adds **overworld ores**: check ATO/`forge:ingots/*` tag overlap first; prefer disabling the newcomer's ore gen + a conversion bridge over letting veins double up.
- Any new mod with **its own energy/fluid system**: fine (Forge tags handle most interop); resist the urge to unify what doesn't ask to be unified.
- Playtest 1 owns all spawn-rate / drop-rate decisions (TUNING.md density row).
