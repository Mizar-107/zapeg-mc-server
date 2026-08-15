// Endgame policy — brief §5 ("no millions" rule), ACTIVE since v0.3.0.
// Decision: the pack must play out vanilla-ish; the million-scale chases are cut
// at the source by making the two "stars" uncraftable. Everything below them
// (Mekanism, Create, ATM ores, all mods' normal progression) is untouched.
//
// Ids verified against ATM9 1.1.x's own kubejs scripts:
//   ATM Star  = allthetweaks:atm_star   (crafting chain lives in modpack/atm_star.js)
//   Gregstar  = allthetweaks:greg_star  (starforge chain, mods/gtceu/starforge_recipes.js)
//
// Deploy: scripts/apply-overrides.sh ; live reload: /kubejs reload server_scripts
// Quest chapters for the stars stay visible in the book — they're lore now, not goals.

ServerEvents.recipes(event => {
  // --- ACTIVE: the ceiling -------------------------------------------------
  event.remove({ output: 'allthetweaks:atm_star' })   // ATM Star uncraftable
  event.remove({ output: 'allthetweaks:greg_star' })  // Gregstar uncraftable

  // --- STAGED (uncomment only after a playtest says so) --------------------
  // Draconic Evolution chaos tier (billion-RF scaling). Brief §5 level 4 says
  // DE can be removed entirely; leaving its mid-game gear alone for now.
  // event.remove({ output: 'draconicevolution:chaos_shard' })
  // event.remove({ mod: 'draconicevolution' })
})
