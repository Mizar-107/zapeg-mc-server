// Endgame policy hooks — brief §5 ("no millions" rule).
// Policy level 1 (social rule) is the default => everything below stays commented.
// Escalate deliberately, one recipe at a time.
//
// Deploy:      scripts/apply-overrides.sh   (rsyncs this into data/kubejs/)
// Live reload: /kubejs reload server_scripts   (in-game, OP)
// Verify ids:  hold item, run /kubejs hand
//
// Unique filename => never clobbered by ATM9 pack updates.

ServerEvents.recipes(event => {
  // --- Level 3 examples (uncomment to enact) ------------------------------
  // ATM Star (AllTheTweaks) — verify id with /kubejs hand before trusting it:
  // event.remove({ output: 'allthetweaks:atm_star' })

  // Draconic Evolution chaos tier:
  // event.remove({ output: 'draconicevolution:chaos_shard' })

  // Near-nuclear: all Draconic Evolution recipes (mod stays installed, becomes loot-only):
  // event.remove({ mod: 'draconicevolution' })
})
