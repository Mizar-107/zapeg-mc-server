// Endgame policy — brief §5. Stance since v0.3.1: NATURAL progression.
// Nothing is removed or nerfed. The "no millions" rule is social (level 1):
// the star chapters simply aren't group goals. If that ever changes,
// uncomment below — ids are verified against ATM9 1.1.x's own scripts:
//   ATM Star  = allthetweaks:atm_star   (modpack/atm_star.js)
//   Gregstar  = allthetweaks:greg_star  (mods/gtceu/starforge_recipes.js)
//
// Deploy: scripts/apply-overrides.sh ; live reload: /kubejs reload server_scripts

ServerEvents.recipes(event => {
  // event.remove({ output: 'allthetweaks:atm_star' })   // ATM Star
  // event.remove({ output: 'allthetweaks:greg_star' })  // Gregstar
  // event.remove({ output: 'draconicevolution:chaos_shard' })  // DE chaos tier
  // event.remove({ mod: 'draconicevolution' })          // nuclear option
})
