"""Static contract tests for the KubeJS servant bridge.

The servant's live breakage was invisible to the behavioral suite: on
kubejs-forge-2001.6.5 / rhino-forge-2001.2.3 a missing bean property reads
back as undefined, String(undefined) == "undefined" passes the player-name
regex, and getUUID() stays ".UUID" (leading all-caps segments are never
decapitalized). Every one of those failures is silent in-game, so the bridge
source itself is pinned here against the accessors that actually exist and
against the Director's Python-side constants.
"""

import re
import sys
import types
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if "mcrcon" not in sys.modules:
    mcrcon_stub = types.ModuleType("mcrcon")
    mcrcon_stub.MCRcon = object
    sys.modules["mcrcon"] = mcrcon_stub

import heraldor as heraldor_service  # noqa: E402
from heraldor_director import (  # noqa: E402
    CONTROL_ACTIONS,
    CONTROL_PHASES,
    CONTROL_SCENE_PROFILE_PHASES,
    SERVANT_AUDIO_CLIP_ID,
    SERVANT_SOURCE_PREFIX,
    SERVANT_THRESHOLD,
)

SERVER_ROOT = Path(__file__).resolve().parents[2]
BRIDGE_PATH = (
    SERVER_ROOT
    / "overrides"
    / "kubejs"
    / "server_scripts"
    / "zapeg_heraldor_servant.js"
)
XP_PATH = (
    SERVER_ROOT
    / "overrides"
    / "kubejs"
    / "startup_scripts"
    / "zapeg_heraldor_servant_xp.js"
)


def _read(path: Path) -> str:
    if not path.is_file():
        raise unittest.SkipTest(f"bridge source not checked out: {path}")
    return path.read_text(encoding="utf-8")


class RhinoPropertyMappingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.source = _read(BRIDGE_PATH)

    def test_no_username_property_anywhere(self) -> None:
        # No username getter exists on Player/Entity KJS interfaces; the
        # scoreboard name is the command-safe player name.
        self.assertIsNone(re.search(r"\.username\b", self.source))
        self.assertIn(".scoreboardName", self.source)

    def test_no_uuid_property_anywhere(self) -> None:
        # Rhino keeps all-caps bean names: getUUID() is ".UUID", so ".uuid"
        # reads undefined. Only the explicit method call is safe.
        self.assertIsNone(re.search(r"\.uuid\b", self.source))
        self.assertIn(".getUUID()", self.source)

    def test_dimension_reads_stay_on_the_kubejs_wrapper_property(self) -> None:
        # Every level flowing through this script is a KubeJS LevelJS
        # wrapper — proven by `level.getBlock(x, y, z)`, which only exists on
        # the wrapper — so `level.dimension` is the real getDimension() bean
        # property, and the raw ServerLevel#dimension() method form must
        # never appear. The single sanctioned read is the zhDimensionId
        # helper.
        self.assertIsNone(re.search(r"\.dimension\(\)", self.source))
        self.assertIn("String(level.dimension)", self.source)

    def test_every_string_interpolation_dimension_uses_helper(self) -> None:
        for match in re.finditer(r"execute in \$\{([^}]+)\}", self.source):
            self.assertIn(
                "dimension",
                match.group(1),
                "execute-in interpolation must come from zhDimensionId",
            )


class ServantKillCountingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.source = _read(BRIDGE_PATH)

    def test_true_attacker_is_counted_not_the_direct_entity(self) -> None:
        # source.player only unwraps the DIRECT entity, so projectile final
        # blows resolve to the arrow and never count; source.entity is the
        # true attacker (shooter) and must be instanceof-checked instead.
        self.assertNotIn("event.source.player", self.source)
        self.assertIn("event.source.entity", self.source)
        self.assertIn(
            "Java.loadClass('net.minecraft.world.entity.player.Player')",
            self.source,
        )
        self.assertIn("instanceof ZH_PLAYER_CLASS", self.source)

    def test_rehearsal_expired_and_counted_servants_never_count(self) -> None:
        self.assertIn("ZH_REHEARSAL_TAG", self.source)
        self.assertIn("ZH_EXPIRED_TAG", self.source)
        self.assertIn("ZH_COUNTED_TAG", self.source)
        guard = re.search(
            r"zhHasTag\(servant, ZH_EXPIRED_TAG\).*?\) return",
            self.source,
            re.DOTALL,
        )
        self.assertIsNotNone(guard)
        self.assertIn("ZH_COUNTED_TAG", guard.group(0))
        self.assertIn("ZH_REHEARSAL_TAG", guard.group(0))

    def test_numen_bodies_are_excluded_from_kills_and_targets(self) -> None:
        self.assertIn("zhIsNumenPlayer(killer)", self.source)
        self.assertIn("zhIsNumenPlayer(target)", self.source)

    def test_servant_can_only_damage_its_target(self) -> None:
        hurt = re.search(
            r"EntityEvents\.hurt\(event => \{(.*?)\n\}\)",
            self.source,
            re.DOTALL,
        )
        self.assertIsNotNone(hurt)
        self.assertIn("zhTargetUuid", hurt.group(1))
        self.assertIn("event.cancel()", hurt.group(1))

    def test_servant_yields_no_loot_or_xp(self) -> None:
        self.assertIn("DeathLootTable: 'minecraft:empty'", self.source)
        self.assertIn("event.drops.clear()", self.source)
        xp_source = _read(XP_PATH)
        self.assertIn("LivingExperienceDropEvent", xp_source)
        self.assertIn("setDroppedExperience(0)", xp_source)

    def test_display_name_is_the_locked_lore_name(self) -> None:
        self.assertIn("Heraldor'un Hizmetkârı", self.source)


class DirectorBridgeContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.source = _read(BRIDGE_PATH)

    def test_scoreboard_objectives_match_python_constants(self) -> None:
        self.assertIn(f"'{heraldor_service.SERVANT_OBJECTIVE}'", self.source)
        self.assertIn(f"'{heraldor_service.SERVANT_WORLD_OBJECTIVE}'", self.source)
        self.assertIn(f"{heraldor_service.SERVANT_SCORE_HOLDER} ", self.source)
        self.assertIn(f"{heraldor_service.SERVANT_WORLD_HOLDER} ", self.source)
        self.assertIn(heraldor_service.SERVANT_OBJECTIVE, SERVANT_SOURCE_PREFIX)
        self.assertIn(heraldor_service.SERVANT_SCORE_HOLDER, SERVANT_SOURCE_PREFIX)

    def test_control_action_allowlist_matches_director(self) -> None:
        match = re.search(
            r"allowedActions = \[(.*?)\]", self.source, re.DOTALL
        )
        self.assertIsNotNone(match)
        actions = set(re.findall(r"'([a-z_]+)'", match.group(1)))
        self.assertEqual(actions, set(CONTROL_ACTIONS))

    def test_control_argument_allowlist_matches_director(self) -> None:
        match = re.search(
            r"allowedArguments = \[(.*?)\]", self.source, re.DOTALL
        )
        self.assertIsNotNone(match)
        arguments = set(re.findall(r"'([a-z0-9_\-]+)'", match.group(1)))
        expected = {"-"} | set(CONTROL_PHASES[1:]) | set(
            CONTROL_SCENE_PROFILE_PHASES
        )
        self.assertEqual(arguments, expected)

    def test_scene_literals_cover_every_director_profile(self) -> None:
        for profile in CONTROL_SCENE_PROFILE_PHASES:
            self.assertIn(f"'{profile}'", self.source)

    def test_threshold_and_clip_id_match_director(self) -> None:
        self.assertEqual(SERVANT_THRESHOLD, 3)
        self.assertEqual(SERVANT_AUDIO_CLIP_ID, "servants_after_three_v1")

    def test_lore_root_attaches_director_and_servant_as_siblings(self) -> None:
        self.assertIn("Commands.literal('zapeg-lore')", self.source)
        self.assertIn("Commands.literal('servant')", self.source)
        self.assertIn("Commands.literal('director')", self.source)
        self.assertIn("root.then(servant)", self.source)
        self.assertIn("root.then(director)", self.source)
        self.assertNotIn(
            ".requires(source => zhDirectorSourceAllowed(source))",
            self.source,
        )
        queue = self.source[
            self.source.index("function zhQueueDirectorRequest") :
            self.source.index("function zhDirectorUsage")
        ]
        self.assertIn("zhDirectorSourceAllowed(source)", queue)
        self.assertIn("if (!rawSource) return true", self.source)


if __name__ == "__main__":
    unittest.main()
