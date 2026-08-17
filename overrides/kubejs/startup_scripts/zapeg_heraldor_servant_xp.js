// ForgeEvents is available only in KubeJS startup_scripts on this exact build.
// Keep Heraldor's tagged servant rewardless without changing normal skeletons.

ForgeEvents.onEvent(
  'net.minecraftforge.event.entity.living.LivingExperienceDropEvent',
  event => {
    const entity = event.entity
    if (entity && entity.tags && entity.tags.contains('zh_hserv')) {
      event.setDroppedExperience(0)
    }
  }
)
