import json
import sqlite3
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if "mcrcon" not in sys.modules:
    mcrcon_stub = types.ModuleType("mcrcon")
    mcrcon_stub.MCRcon = object
    sys.modules["mcrcon"] = mcrcon_stub

from heraldor_director import (  # noqa: E402
    DirectorPolicy,
    DirectorStateLock,
    DirectorStore,
    SERVANT_AUDIO_CLIP_ID,
    ServantIngestResult,
    parse_score_output,
    restore_snapshot,
    servant_story_event_id,
)
import heraldor as heraldor_service  # noqa: E402

WORLD_TOKEN = 17082026
STORY_EVENT_ID = servant_story_event_id(WORLD_TOKEN)


class FakeClock:
    def __init__(self, value: int = 1_000) -> None:
        self.value = value

    def __call__(self) -> int:
        return self.value


class DirectorStoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.db_path = self.root / "heraldor.sqlite3"
        self.snapshot_path = self.root / "backup" / "heraldor.sqlite3"
        self.clock = FakeClock()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def open_store(self, **kwargs) -> DirectorStore:
        return DirectorStore(
            self.db_path,
            snapshot_path=self.snapshot_path,
            clock=self.clock,
            **kwargs,
        )

    def test_schema_reopen_and_consistent_snapshot(self) -> None:
        with self.open_store() as store:
            self.assertEqual(store.status()["schema_version"], 1)
            store.reserve_ambient("whisper", subject="Mizar__107", rehearsal=True)
            store.backup_snapshot()

        with self.open_store() as reopened:
            self.assertEqual(reopened.status()["event_status_counts"], {"reserved": 1})

        snapshot = sqlite3.connect(self.snapshot_path)
        try:
            self.assertEqual(snapshot.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertEqual(snapshot.execute("SELECT COUNT(*) FROM events").fetchone()[0], 1)
        finally:
            snapshot.close()

    def test_restore_promotes_snapshot_and_removes_stale_wal_files(self) -> None:
        with self.open_store() as store:
            store.ingest_servant_score(1, world_token=WORLD_TOKEN)

        live = sqlite3.connect(self.db_path)
        try:
            live.execute("UPDATE source_offsets SET high_water = 99")
            live.commit()
        finally:
            live.close()
        Path(str(self.db_path) + "-wal").write_bytes(b"stale")
        Path(str(self.db_path) + "-shm").write_bytes(b"stale")

        restore_snapshot(self.db_path, self.snapshot_path)
        self.assertFalse(Path(str(self.db_path) + "-wal").exists())
        self.assertFalse(Path(str(self.db_path) + "-shm").exists())
        with self.open_store(recover_interrupted_attempts=False) as restored:
            self.assertEqual(restored.status()["servant_high_water"], 1)

    def test_restore_refuses_while_daemon_state_lock_is_held(self) -> None:
        with self.open_store() as store:
            store.ingest_servant_score(1, world_token=WORLD_TOKEN)

        lock_path = Path(str(self.db_path) + ".lock")
        with DirectorStateLock(lock_path):
            with self.assertRaisesRegex(RuntimeError, "state is locked"):
                restore_snapshot(self.db_path, self.snapshot_path)

    def test_servant_jump_threshold_restart_and_regression_are_idempotent(self) -> None:
        with self.open_store() as store:
            first = store.ingest_servant_score(3, world_token=WORLD_TOKEN)
            self.assertEqual(first.victory_event_ids, (
                f"mc:heraldor-servant:v1:world:{WORLD_TOKEN}:1",
                f"mc:heraldor-servant:v1:world:{WORLD_TOKEN}:2",
                f"mc:heraldor-servant:v1:world:{WORLD_TOKEN}:3",
            ))
            self.assertEqual(first.story_event_id, STORY_EVENT_ID)

        with self.open_store() as store:
            replay = store.ingest_servant_score(3, world_token=WORLD_TOKEN)
            self.assertEqual(replay.victory_event_ids, ())
            self.assertIsNone(replay.story_event_id)

            later = store.ingest_servant_score(5, world_token=WORLD_TOKEN)
            self.assertEqual(later.victory_event_ids, (
                f"mc:heraldor-servant:v1:world:{WORLD_TOKEN}:4",
                f"mc:heraldor-servant:v1:world:{WORLD_TOKEN}:5",
            ))
            self.assertIsNone(later.story_event_id)

            regression = store.ingest_servant_score(1, world_token=WORLD_TOKEN)
            self.assertTrue(regression.regression)
            self.assertEqual(regression.high_water, 5)

            recovered = store.ingest_servant_score(6, world_token=WORLD_TOKEN)
            self.assertEqual(
                recovered.victory_event_ids,
                (f"mc:heraldor-servant:v1:world:{WORLD_TOKEN}:6",),
            )

            rows = store.connection.execute(
                "SELECT event_id FROM events WHERE kind = 'servant_threshold'"
            ).fetchall()
            self.assertEqual([row[0] for row in rows], [STORY_EVENT_ID])

    def test_servant_events_and_high_water_commit_atomically(self) -> None:
        with self.open_store() as store:
            store.connection.execute(
                """
                CREATE TRIGGER reject_test_offset
                BEFORE INSERT ON source_offsets
                BEGIN
                    SELECT RAISE(ABORT, 'injected failure');
                END
                """
            )
            with self.assertRaises(sqlite3.IntegrityError):
                store.ingest_servant_score(3, world_token=WORLD_TOKEN)

            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM events").fetchone()[0], 0)
            self.assertEqual(
                store.connection.execute("SELECT COUNT(*) FROM story_flags").fetchone()[0], 0
            )

    def test_new_world_token_starts_an_independent_victory_stream(self) -> None:
        second_world = WORLD_TOKEN + 1
        with self.open_store() as store:
            store.ingest_servant_score(5, world_token=WORLD_TOKEN)
            baseline = store.ingest_servant_score(0, world_token=second_world)
            self.assertFalse(baseline.regression)
            self.assertEqual(baseline.high_water, 0)

            second = store.ingest_servant_score(3, world_token=second_world)
            self.assertEqual(second.story_event_id, servant_story_event_id(second_world))
            status = store.status()
            self.assertEqual(status["servant_world_token"], str(second_world))
            self.assertEqual(status["servant_high_water"], 3)

    def test_implausible_score_jump_is_quarantined_without_row_expansion(self) -> None:
        with self.open_store() as store:
            rejected = store.ingest_servant_score(10_000, world_token=WORLD_TOKEN)
            self.assertTrue(rejected.quarantined)
            self.assertEqual(rejected.high_water, 0)
            self.assertEqual(store.connection.execute("SELECT COUNT(*) FROM events").fetchone()[0], 0)
            self.assertEqual(
                store.connection.execute("SELECT COUNT(*) FROM source_offsets").fetchone()[0], 0
            )

            accepted = store.ingest_servant_score(3, world_token=WORLD_TOKEN)
            self.assertFalse(accepted.quarantined)
            self.assertEqual(accepted.high_water, 3)

    def test_threshold_records_allowlisted_audio_but_does_not_play_later(self) -> None:
        with self.open_store() as store:
            store.ingest_servant_score(3, world_token=WORLD_TOKEN)
            row = store.connection.execute(
                "SELECT payload_json, status FROM outbox WHERE event_id = ?",
                (STORY_EVENT_ID,),
            ).fetchone()

        payload = json.loads(row["payload_json"])
        self.assertEqual(row["status"], "suppressed_no_sink")
        self.assertEqual(payload["type"], "heraldor.audio.requested")
        self.assertEqual(payload["clip_id"], SERVANT_AUDIO_CLIP_ID)
        self.assertNotIn("url", payload)
        self.assertNotIn("path", payload)

    def test_pacing_cooldowns_budget_and_rehearsal(self) -> None:
        policy = DirectorPolicy(
            ambient_gap_seconds=10,
            targeted_gap_seconds=30,
            ambient_window_seconds=100,
            ambient_budget=2,
            major_quiet_seconds=40,
            discord_cooldown_seconds=50,
            shadows_cooldown_seconds=50,
        )
        with self.open_store(policy=policy) as store:
            self.assertIsNotNone(store.reserve_ambient("whisper", subject="Alice"))
            self.clock.value += 9
            self.assertIsNone(store.reserve_ambient("global"))

            # The exact boundary opens; names are compared case-insensitively.
            self.clock.value += 1
            self.assertIsNone(store.reserve_ambient("whisper", subject="ALICE"))
            self.assertIsNotNone(store.reserve_ambient("global"))

            self.clock.value += 11
            self.assertIsNone(store.reserve_ambient("global"))  # rolling budget
            self.assertIsNotNone(
                store.reserve_ambient("shadows", subject="Alice", rehearsal=True)
            )

    def test_story_event_establishes_quiet_period(self) -> None:
        policy = DirectorPolicy(
            ambient_gap_seconds=0,
            targeted_gap_seconds=0,
            ambient_window_seconds=100,
            ambient_budget=10,
            major_quiet_seconds=40,
            discord_cooldown_seconds=0,
            shadows_cooldown_seconds=0,
        )
        with self.open_store(policy=policy) as store:
            store.ingest_servant_score(3, world_token=WORLD_TOKEN)
            self.clock.value += 39
            self.assertIsNone(store.reserve_ambient("global"))
            self.clock.value += 1
            self.assertIsNotNone(store.reserve_ambient("global"))

    def test_interrupted_side_effect_becomes_ambiguous_after_restart(self) -> None:
        with self.open_store() as store:
            reservation = store.reserve_ambient("global", rehearsal=True)
            self.assertTrue(store.mark_attempting(reservation.event_id))

            with self.open_store(recover_interrupted_attempts=False) as reader:
                status = reader.connection.execute(
                    "SELECT status FROM events WHERE event_id = ?", (reservation.event_id,)
                ).fetchone()[0]
                self.assertEqual(status, "attempting")

        self.clock.value += 100
        with self.open_store() as reopened:
            row = reopened.connection.execute(
                "SELECT status FROM events WHERE event_id = ?", (reservation.event_id,)
            ).fetchone()
            self.assertEqual(row["status"], "ambiguous")
            self.assertFalse(reopened.mark_attempting(reservation.event_id))

    def test_duplicate_explicit_event_id_is_rejected(self) -> None:
        with self.open_store() as store:
            first = store.reserve_ambient("global", rehearsal=True, event_id="rehearsal:v1")
            second = store.reserve_ambient("global", rehearsal=True, event_id="rehearsal:v1")
            self.assertIsNotNone(first)
            self.assertIsNone(second)


class ScoreParserTest(unittest.TestCase):
    def test_parses_value_after_has_not_username_digits(self) -> None:
        self.assertEqual(parse_score_output("Mizar__107 has 12 [zapeg_hsvc]"), 12)
        self.assertEqual(parse_score_output("#total has 3 [zapeg_hsvc]"), 3)

    def test_fallback_and_invalid_output(self) -> None:
        self.assertEqual(parse_score_output("#total: 8 [zapeg_hsvc]"), 8)
        self.assertIsNone(parse_score_output("No score is known for #total"))


class PresenceServiceTest(unittest.TestCase):
    def test_poll_pairs_score_with_stable_world_token(self) -> None:
        class CapturingDirector:
            call = None

            def ingest_servant_score(self, score, *, world_token):
                self.call = (score, world_token)
                return ServantIngestResult(0, score, (), None)

        director = CapturingDirector()
        outputs = [
            "#world has 12345 [zh_svc_world]",
            "#total has 2 [zapeg_hsvc]",
            "#world has 12345 [zh_svc_world]",
        ]
        with patch.object(heraldor_service, "rcon_many", return_value=outputs):
            polled = heraldor_service.poll_servant_score(director)
        self.assertEqual(director.call, (2, 12345))
        self.assertEqual(polled[1:], (2, 12345))

    def test_poll_rejects_a_world_change_between_reads(self) -> None:
        class RejectingDirector:
            def ingest_servant_score(self, *_args, **_kwargs):
                raise AssertionError("must not ingest a cross-world read")

        outputs = [
            "#world has 12345 [zh_svc_world]",
            "#total has 2 [zapeg_hsvc]",
            "#world has 67890 [zh_svc_world]",
        ]
        with patch.object(heraldor_service, "rcon_many", return_value=outputs):
            self.assertIsNone(heraldor_service.poll_servant_score(RejectingDirector()))

    def test_all_successful_rolls_still_reserve_only_one_ambient_event(self) -> None:
        class CapturingDirector:
            calls = []

            def reserve_ambient(self, kind, *, subject=None):
                self.calls.append((kind, subject))
                return None

        director = CapturingDirector()
        with (
            patch.object(heraldor_service, "online_players", return_value=["Alice"]),
            patch.object(heraldor_service, "is_night", return_value=True),
            patch.object(heraldor_service, "WEBHOOK", "https://unused.invalid"),
            patch.object(heraldor_service, "EVENTS", True),
            patch.object(heraldor_service, "P_WHISPER", 1.0),
            patch.object(heraldor_service, "P_GLOBAL", 1.0),
            patch.object(heraldor_service, "P_DISCORD", 1.0),
            patch.object(heraldor_service, "P_SHADOWS", 1.0),
            patch.object(heraldor_service.random, "random", return_value=0.0),
            patch.object(heraldor_service.random, "choice", side_effect=lambda values: values[0]),
        ):
            heraldor_service.ambient_cycle(director)

        self.assertEqual(len(director.calls), 1)


class ServantScriptContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        repo = Path(__file__).resolve().parents[2]
        cls.script = (
            repo
            / "overrides"
            / "kubejs"
            / "server_scripts"
            / "zapeg_heraldor_servant.js"
        ).read_text(encoding="utf-8")
        cls.startup_script = (
            repo
            / "overrides"
            / "kubejs"
            / "startup_scripts"
            / "zapeg_heraldor_servant_xp.js"
        ).read_text(encoding="utf-8")

    def test_rehearsal_is_separate_from_explicit_live_encounter(self) -> None:
        self.assertIn("Commands.literal('rehearse')", self.script)
        self.assertIn("Commands.literal('awaken')", self.script)
        death_handler = self.script[self.script.index("EntityEvents.death") :]
        self.assertIn("zhHasTag(servant, ZH_REHEARSAL_TAG)", death_handler)
        self.assertLess(
            death_handler.index("zhHasTag(servant, ZH_REHEARSAL_TAG)"),
            death_handler.index("scoreboard players add #total"),
        )

    def test_name_permission_and_no_reward_contract_are_present(self) -> None:
        self.assertIn("Heraldor'un Hizmetkârı", self.script)
        self.assertIn("source.hasPermission(2)", self.script)
        self.assertIn("DeathLootTable: 'minecraft:empty'", self.script)
        self.assertIn("event.drops.clear()", self.script)
        self.assertNotIn("ForgeEvents.onEvent", self.script)
        self.assertIn("ForgeEvents.onEvent", self.startup_script)
        self.assertIn("event.setDroppedExperience(0)", self.startup_script)
        self.assertIn("const ZH_WORLD_OBJECTIVE = 'zh_svc_world'", self.script)
        self.assertNotIn("level.runCommandSilent", self.script)
        self.assertNotIn("servant.runCommandSilent", self.script)
        self.assertNotIn("target.runCommandSilent", self.script)
        self.assertNotIn("killer.runCommandSilent", self.script)
        self.assertIn("servant.kill()", self.script)
        self.assertIn("/^[A-Za-z0-9_]{1,16}$/.test(name)", self.script)
        self.assertIn("server.runCommandSilent(\n      `execute in ${dimension}", self.script)


if __name__ == "__main__":
    unittest.main()
