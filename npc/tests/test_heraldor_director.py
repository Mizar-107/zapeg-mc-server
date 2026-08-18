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
    CampaignState,
    DirectorPolicy,
    DirectorStateLock,
    DirectorStore,
    SERVANT_AUDIO_CLIP_ID,
    ServantIngestResult,
    extract_control_request_token,
    parse_control_request,
    parse_score_output,
    restore_snapshot,
    servant_story_event_id,
)
import heraldor as heraldor_service  # noqa: E402

WORLD_TOKEN = 17082026
STORY_EVENT_ID = servant_story_event_id(WORLD_TOKEN)


def control_request(
    action: str,
    argument: str = "-",
    target: str = "-",
    *,
    nonce: int,
    world_token: int = WORLD_TOKEN,
    expires_at: int = 1_780_000_090,
    operator: str = "Mizar__107",
):
    return parse_control_request(
        f"zhctl1:{world_token}:{nonce:020x}:{expires_at}:"
        f"{action}:{argument}:{target}:{operator}"
    )


class FakeClock:
    def __init__(self, value: int = 1_780_000_000) -> None:
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
            self.assertEqual(store.status()["schema_version"], 2)
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

    def test_dormant_threshold_is_terminally_suppressed_and_never_banked(self) -> None:
        with self.open_store() as store:
            store.ingest_servant_score(3, world_token=WORLD_TOKEN)
            row = store.connection.execute(
                "SELECT payload_json, status FROM outbox WHERE event_id = ?",
                (STORY_EVENT_ID,),
            ).fetchone()

        payload = json.loads(row["payload_json"])
        self.assertEqual(row["status"], "suppressed_campaign_dormant")
        self.assertEqual(payload["type"], "heraldor.audio.requested")
        self.assertEqual(payload["clip_id"], SERVANT_AUDIO_CLIP_ID)
        self.assertNotIn("url", payload)
        self.assertNotIn("path", payload)

        with self.open_store(audio_sink_enabled=True) as store:
            heraldor_service.process_control_request(
                store,
                control_request("phase_start", "presence", nonce=1),
                observed_world_token=WORLD_TOKEN,
            )
            self.assertIsNone(store.claim_next_audio(now=self.clock.value + 1))

    def test_paused_threshold_is_observed_but_never_delivered_after_resume(self) -> None:
        with self.open_store(audio_sink_enabled=True) as store:
            heraldor_service.process_control_request(
                store,
                control_request("phase_start", "presence", nonce=2),
                observed_world_token=WORLD_TOKEN,
            )
            heraldor_service.process_control_request(
                store,
                control_request("pause", nonce=3),
                observed_world_token=WORLD_TOKEN,
            )
            result = store.ingest_servant_score(3, world_token=WORLD_TOKEN)
            self.assertEqual(result.story_output_status, "suppressed_campaign_paused")
            heraldor_service.process_control_request(
                store,
                control_request("resume", nonce=4),
                observed_world_token=WORLD_TOKEN,
            )
            self.assertIsNone(store.claim_next_audio(now=self.clock.value + 1))

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
            heraldor_service.process_control_request(
                store,
                control_request("phase_start", "presence", nonce=10),
                observed_world_token=WORLD_TOKEN,
            )
            self.assertIsNotNone(
                store.reserve_ambient(
                    "whisper", subject="Alice", world_token=WORLD_TOKEN
                )
            )
            self.clock.value += 9
            self.assertIsNone(
                store.reserve_ambient("global", world_token=WORLD_TOKEN)
            )

            # The exact boundary opens; names are compared case-insensitively.
            self.clock.value += 1
            self.assertIsNone(
                store.reserve_ambient(
                    "whisper", subject="ALICE", world_token=WORLD_TOKEN
                )
            )
            self.assertIsNotNone(
                store.reserve_ambient("global", world_token=WORLD_TOKEN)
            )

            self.clock.value += 11
            self.assertIsNone(
                store.reserve_ambient("global", world_token=WORLD_TOKEN)
            )  # rolling budget
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
            heraldor_service.process_control_request(
                store,
                control_request("phase_start", "presence", nonce=11),
                observed_world_token=WORLD_TOKEN,
            )
            store.ingest_servant_score(3, world_token=WORLD_TOKEN)
            self.clock.value += 39
            self.assertIsNone(
                store.reserve_ambient("global", world_token=WORLD_TOKEN)
            )
            self.clock.value += 1
            self.assertIsNotNone(
                store.reserve_ambient("global", world_token=WORLD_TOKEN)
            )

    def test_live_ambient_requires_an_active_unpaused_world(self) -> None:
        with self.open_store() as store:
            with self.assertRaisesRegex(ValueError, "requires a world token"):
                store.reserve_ambient("global")
            self.assertIsNone(
                store.reserve_ambient("global", world_token=WORLD_TOKEN)
            )
            heraldor_service.process_control_request(
                store,
                control_request("phase_start", "presence", nonce=12),
                observed_world_token=WORLD_TOKEN,
            )
            self.assertIsNotNone(
                store.reserve_ambient("global", world_token=WORLD_TOKEN)
            )
            heraldor_service.process_control_request(
                store,
                control_request("pause", nonce=13),
                observed_world_token=WORLD_TOKEN,
            )
            self.assertIsNone(
                store.reserve_ambient("whisper", world_token=WORLD_TOKEN)
            )

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


class ControlProtocolTest(unittest.TestCase):
    def test_strict_token_parser_and_localized_output_extractor(self) -> None:
        request = control_request(
            "scene_trigger", "motion_echo_01", "Alice_7", nonce=20
        )
        self.assertEqual(request.world_token, str(WORLD_TOKEN))
        self.assertEqual(request.target, "Alice_7")
        self.assertEqual(request.argument, "motion_echo_01")
        output = f'Depolama içeriği: "{request.token}"'
        self.assertEqual(extract_control_request_token(output), request.token)
        self.assertIsNone(
            extract_control_request_token(
                f'Data: "prefix {request.token} suffix"'
            )
        )
        self.assertIsNone(
            extract_control_request_token(f'Data: {{wrapped:"{request.token}"}}')
        )

    def test_token_rejects_free_form_actions_profiles_names_and_trailing_fields(self) -> None:
        bad_tokens = [
            f"zhctl1:{WORLD_TOKEN}:{21:020x}:1780000090:run_command:-:-:Mizar__107",
            f"zhctl1:{WORLD_TOKEN}:{22:020x}:1780000090:scene_trigger:custom:Alice:Mizar__107",
            f"zhctl1:{WORLD_TOKEN}:{23:020x}:1780000090:scene_trigger:echo_01:Bad-Name:Mizar__107",
            f"zhctl1:{WORLD_TOKEN}:{24:020x}:1780000090:pause:-:Alice:Mizar__107",
            f"zhctl1:{WORLD_TOKEN}:{25:020x}:1780000090:status:-:-:Mizar__107:extra",
        ]
        for token in bad_tokens:
            with self.subTest(token=token), self.assertRaises(ValueError):
                parse_control_request(token)


class DirectorControlBridgeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.db_path = self.root / "heraldor.sqlite3"
        self.clock = FakeClock()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def open_store(self, **kwargs) -> DirectorStore:
        return DirectorStore(self.db_path, clock=self.clock, **kwargs)

    def process(self, store, request):
        return heraldor_service.process_control_request(
            store, request, observed_world_token=WORLD_TOKEN
        )

    def test_phase_pause_gates_and_world_separation(self) -> None:
        with self.open_store() as store:
            self.assertEqual(store.campaign_state(WORLD_TOKEN).phase, "dormant")
            presence = self.process(
                store, control_request("phase_start", "presence", nonce=30)
            )
            self.assertEqual(presence.status, "delivered")
            self.assertEqual(store.campaign_state(WORLD_TOKEN).phase, "presence")

            pause = self.process(store, control_request("pause", nonce=31))
            self.assertEqual(pause.status, "delivered")
            with patch.object(heraldor_service, "rcon") as runtime:
                live = self.process(
                    store,
                    control_request("scene_trigger", "echo_01", "Alice", nonce=32),
                )
            self.assertEqual(live.status, "rejected")
            runtime.assert_not_called()

            advanced_while_paused = self.process(
                store, control_request("phase_advance", nonce=37)
            )
            self.assertEqual(advanced_while_paused.status, "delivered")
            self.assertEqual(
                store.campaign_state(WORLD_TOKEN),
                CampaignState(str(WORLD_TOKEN), "servants", True),
            )

            with patch.object(
                heraldor_service,
                "rcon",
                return_value="scene dispatched event=00000000-0000-0000-0000-000000000001",
            ):
                rehearsal = self.process(
                    store,
                    control_request("scene_rehearse", "echo_01", "Alice", nonce=33),
                )
            self.assertEqual(rehearsal.status, "delivered")

            self.process(store, control_request("resume", nonce=34))
            jumped = self.process(
                store, control_request("phase_start", "manifestation", nonce=35)
            )
            self.assertEqual(jumped.status, "delivered")
            backwards = self.process(
                store, control_request("phase_start", "servants", nonce=36)
            )
            self.assertEqual(backwards.status, "rejected")
            self.assertEqual(store.campaign_state(WORLD_TOKEN).phase, "manifestation")
            self.assertEqual(
                store.campaign_state(WORLD_TOKEN + 1),
                CampaignState(str(WORLD_TOKEN + 1), "dormant", False),
            )

    def test_profile_phase_gates_are_hard_boundaries(self) -> None:
        with self.open_store() as store:
            self.process(store, control_request("phase_advance", nonce=40))
            self.assertEqual(store.campaign_state(WORLD_TOKEN).phase, "presence")
            with patch.object(heraldor_service, "rcon") as runtime:
                motion = self.process(
                    store,
                    control_request(
                        "scene_trigger", "motion_echo_01", "Alice", nonce=41
                    ),
                )
            self.assertEqual(motion.status, "rejected")
            runtime.assert_not_called()

            self.process(store, control_request("phase_advance", nonce=42))
            with patch.object(
                heraldor_service,
                "rcon",
                return_value="scene dispatched event=00000000-0000-0000-0000-000000000002",
            ) as runtime:
                motion = self.process(
                    store,
                    control_request(
                        "scene_trigger", "motion_echo_01", "Alice", nonce=43
                    ),
                )
            self.assertEqual(motion.status, "delivered")
            runtime.assert_called_once()

            with patch.object(heraldor_service, "rcon") as runtime:
                light = self.process(
                    store,
                    control_request(
                        "scene_rehearse", "light_fault_01", "Alice", nonce=44
                    ),
                )
            self.assertEqual(light.status, "rejected")
            runtime.assert_not_called()

    def test_live_dispatch_is_at_most_once_and_uncertain_transport_is_ambiguous(self) -> None:
        with self.open_store() as store:
            self.process(
                store, control_request("phase_start", "presence", nonce=50)
            )
            request = control_request(
                "scene_trigger", "echo_01", "Alice", nonce=51
            )
            with patch.object(
                heraldor_service,
                "rcon",
                return_value=f"scene dispatched event={request.event_id}",
            ) as runtime:
                first = self.process(store, request)
                duplicate = self.process(store, request)
            self.assertEqual(first.status, "delivered")
            self.assertEqual(duplicate.status, "delivered")
            runtime.assert_called_once()

            uncertain = control_request(
                "scene_trigger", "threshold_01", "Alice", nonce=52
            )
            with patch.object(
                heraldor_service, "rcon", side_effect=OSError("connection reset")
            ) as runtime:
                result = self.process(store, uncertain)
            self.assertEqual(result.status, "ambiguous")
            runtime.assert_called_once()
            with patch.object(heraldor_service, "rcon") as runtime:
                replay = self.process(store, uncertain)
            self.assertEqual(replay.status, "ambiguous")
            runtime.assert_not_called()

    def test_restart_turns_claimed_control_into_non_replayable_ambiguous(self) -> None:
        request = control_request(
            "scene_rehearse", "echo_01", "Alice", nonce=60
        )
        with self.open_store() as store:
            store.record_control_event(
                request,
                kind="director_scene",
                category="directed",
                status="reserved",
                subject="Alice",
                rehearsal=True,
            )
            self.assertTrue(store.mark_attempting(request.event_id))

        with self.open_store() as reopened:
            self.assertEqual(
                reopened.control_event_status(request.event_id), "ambiguous"
            )
            with patch.object(heraldor_service, "rcon") as runtime:
                replay = self.process(reopened, request)
            self.assertEqual(replay.status, "ambiguous")
            runtime.assert_not_called()

    def test_wrong_world_and_expired_requests_are_terminal_without_runtime(self) -> None:
        with self.open_store() as store, patch.object(heraldor_service, "rcon") as runtime:
            wrong_world = self.process(
                store,
                control_request("scene_trigger", "echo_01", "Alice", nonce=70),
            )
            # Still dormant, so establish that the earlier rejection was a phase gate.
            self.assertEqual(wrong_world.status, "rejected")
            mismatch = heraldor_service.process_control_request(
                store,
                control_request(
                    "status", nonce=71, world_token=WORLD_TOKEN + 1
                ),
                observed_world_token=WORLD_TOKEN,
            )
            expired = self.process(
                store,
                control_request("status", nonce=72, expires_at=self.clock.value),
            )
        self.assertEqual(mismatch.status, "rejected")
        self.assertEqual(expired.status, "suppressed_expired")
        runtime.assert_not_called()

    def test_rejected_and_failed_scenes_do_not_spend_targeted_ambient_cooldown(self) -> None:
        policy = DirectorPolicy(
            ambient_gap_seconds=0,
            targeted_gap_seconds=100,
            ambient_window_seconds=100,
            ambient_budget=10,
            major_quiet_seconds=0,
            discord_cooldown_seconds=0,
            shadows_cooldown_seconds=0,
        )
        with self.open_store(policy=policy) as store:
            self.process(
                store, control_request("phase_start", "presence", nonce=73)
            )
            self.process(store, control_request("pause", nonce=74))
            rejected = self.process(
                store,
                control_request("scene_trigger", "echo_01", "Alice", nonce=75),
            )
            self.assertEqual(rejected.status, "rejected")
            self.process(store, control_request("resume", nonce=76))
            self.assertIsNotNone(
                store.reserve_ambient(
                    "whisper", subject="Alice", world_token=WORLD_TOKEN
                )
            )

            failed_request = control_request(
                "scene_trigger", "echo_01", "Bob", nonce=77
            )
            with patch.object(
                heraldor_service, "rcon", return_value="another scene is active"
            ):
                failed = self.process(store, failed_request)
            self.assertEqual(failed.status, "failed")
            self.assertIsNotNone(
                store.reserve_ambient(
                    "whisper", subject="Bob", world_token=WORLD_TOKEN
                )
            )

            delivered_request = control_request(
                "scene_trigger", "echo_01", "Charlie", nonce=78
            )
            with patch.object(
                heraldor_service,
                "rcon",
                return_value=f"scene dispatched event={delivered_request.event_id}",
            ):
                delivered = self.process(store, delivered_request)
            self.assertEqual(delivered.status, "delivered")
            self.assertIsNone(
                store.reserve_ambient(
                    "whisper", subject="Charlie", world_token=WORLD_TOKEN
                )
            )

    def test_cancel_does_not_change_phase_or_pause_state(self) -> None:
        with self.open_store() as store:
            self.process(
                store, control_request("phase_start", "servants", nonce=80)
            )
            self.process(store, control_request("pause", nonce=81))
            with patch.object(
                heraldor_service, "rcon", return_value="active=0"
            ) as runtime:
                cancelled = self.process(store, control_request("cancel", nonce=82))
            self.assertEqual(cancelled.status, "delivered")
            runtime.assert_called_once_with("zapegscene cancel-all")
            self.assertEqual(
                store.campaign_state(WORLD_TOKEN),
                CampaignState(str(WORLD_TOKEN), "servants", True),
            )

    def test_mailbox_poll_uses_stable_world_and_conditional_exact_clear(self) -> None:
        request = control_request("status", nonce=90, operator="console")
        outputs = [
            f"#world has {WORLD_TOKEN} [zh_svc_world]",
            f'Data: "{request.token}"',
            f"#world has {WORLD_TOKEN} [zh_svc_world]",
        ]
        with (
            self.open_store() as store,
            patch.object(heraldor_service, "rcon_many", return_value=outputs),
            patch.object(heraldor_service, "rcon", return_value="1") as command,
        ):
            result = heraldor_service.poll_control_request(store)
        self.assertEqual(result.status, "delivered")
        self.assertEqual(command.call_count, 1)
        clear = command.call_args.args[0]
        self.assertIn("execute if data storage zapeg:heraldor", clear)
        self.assertIn(request.token, clear)
        self.assertIn("run data remove storage zapeg:heraldor control_request", clear)


class ScoreParserTest(unittest.TestCase):
    def test_parses_value_after_has_not_username_digits(self) -> None:
        self.assertEqual(parse_score_output("Mizar__107 has 12 [zapeg_hsvc]"), 12)
        self.assertEqual(parse_score_output("#total has 3 [zapeg_hsvc]"), 3)

    def test_fallback_and_invalid_output(self) -> None:
        self.assertEqual(parse_score_output("#total: 8 [zapeg_hsvc]"), 8)
        self.assertIsNone(parse_score_output("No score is known for #total"))


class PresenceServiceTest(unittest.TestCase):
    def test_failed_or_unstable_poll_cannot_retain_an_old_world_token(self) -> None:
        old_world_poll = (
            ServantIngestResult(0, 0, (), None),
            0,
            WORLD_TOKEN,
        )
        self.assertEqual(
            heraldor_service._world_token_from_servant_poll(old_world_poll),
            WORLD_TOKEN,
        )
        self.assertIsNone(heraldor_service._world_token_from_servant_poll(None))

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

            def campaign_state(self, world_token):
                return CampaignState(str(world_token), "presence", False)

            def reserve_ambient(self, kind, *, subject=None, world_token=None):
                self.calls.append((kind, subject, world_token))
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
            heraldor_service.ambient_cycle(director, WORLD_TOKEN)

        self.assertEqual(len(director.calls), 1)

    def test_dormant_and_paused_campaigns_do_not_roll_ambient(self) -> None:
        class SuppressedDirector:
            def __init__(self, state):
                self.state = state

            def campaign_state(self, _world_token):
                return self.state

            def reserve_ambient(self, *_args, **_kwargs):
                raise AssertionError("suppressed ambient must never reserve")

        for state in (
            CampaignState(str(WORLD_TOKEN), "dormant", False),
            CampaignState(str(WORLD_TOKEN), "presence", True),
        ):
            with (
                self.subTest(state=state),
                patch.object(heraldor_service, "online_players") as players,
            ):
                heraldor_service.ambient_cycle(SuppressedDirector(state), WORLD_TOKEN)
                players.assert_not_called()

        with patch.object(heraldor_service, "online_players") as players:
            heraldor_service.ambient_cycle(
                SuppressedDirector(
                    CampaignState(str(WORLD_TOKEN), "manifestation", False)
                ),
                None,
            )
            players.assert_not_called()


class SceneTtlScalingTest(unittest.TestCase):
    def test_every_gated_profile_has_a_ttl_default(self) -> None:
        from heraldor_director import (
            CONTROL_SCENE_PROFILE_PHASES,
            SCENE_PROFILE_DEFAULT_TTL_TICKS,
        )

        self.assertEqual(
            set(CONTROL_SCENE_PROFILE_PHASES),
            set(SCENE_PROFILE_DEFAULT_TTL_TICKS),
        )

    def test_ttl_scales_up_with_phase_and_stays_bounded(self) -> None:
        from heraldor_director import SCENE_MAX_TTL_TICKS, scene_ttl_ticks

        self.assertEqual(scene_ttl_ticks("echo_01", "dormant"), 200)
        self.assertEqual(scene_ttl_ticks("echo_01", "presence"), 200)
        self.assertEqual(scene_ttl_ticks("echo_01", "servants"), 230)
        self.assertEqual(scene_ttl_ticks("echo_01", "manifestation"), 270)
        for profile in (
            "echo_01",
            "threshold_01",
            "motion_echo_01",
            "light_fault_01",
            "peripheral_01",
            "footsteps_01",
        ):
            for phase in ("dormant", "presence", "servants", "manifestation"):
                ttl = scene_ttl_ticks(profile, phase)
                self.assertGreaterEqual(ttl, 1)
                self.assertLessEqual(ttl, SCENE_MAX_TTL_TICKS)
        with self.assertRaises(ValueError):
            scene_ttl_ticks("unknown_profile", "presence")
        with self.assertRaises(ValueError):
            scene_ttl_ticks("echo_01", "unknown_phase")

    def test_trigger_command_carries_phase_scaled_ttl(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        store = DirectorStore(
            Path(temp.name) / "heraldor.sqlite3", clock=FakeClock()
        )
        self.addCleanup(store.close)
        heraldor_service.process_control_request(
            store,
            control_request("phase_start", "manifestation", nonce=90),
            observed_world_token=WORLD_TOKEN,
        )
        request = control_request("scene_trigger", "echo_01", "Alice", nonce=91)
        with patch.object(
            heraldor_service,
            "rcon",
            return_value=f"scene dispatched event={request.event_id}",
        ) as runtime:
            outcome = heraldor_service.process_control_request(
                store, request, observed_world_token=WORLD_TOKEN
            )
        self.assertEqual(outcome.status, "delivered")
        command = runtime.call_args.args[0]
        self.assertEqual(
            command,
            f"zapegscene trigger Alice {request.event_id} echo_01 270",
        )

    def test_rehearse_command_keeps_runtime_default_ttl(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        store = DirectorStore(
            Path(temp.name) / "heraldor.sqlite3", clock=FakeClock()
        )
        self.addCleanup(store.close)
        heraldor_service.process_control_request(
            store,
            control_request("phase_start", "presence", nonce=95),
            observed_world_token=WORLD_TOKEN,
        )
        with patch.object(
            heraldor_service,
            "rcon",
            return_value="scene dispatched event=00000000-0000-0000-0000-000000000099",
        ) as runtime:
            outcome = heraldor_service.process_control_request(
                store,
                control_request("scene_rehearse", "peripheral_01", "Alice", nonce=96),
                observed_world_token=WORLD_TOKEN,
            )
        self.assertEqual(outcome.status, "delivered")
        command = runtime.call_args.args[0]
        self.assertEqual(command, "zapegscene rehearse Alice peripheral_01")


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

    def test_director_bridge_is_allowlisted_queued_and_never_calls_runtime(self) -> None:
        self.assertIn("Commands.literal('director')", self.script)
        self.assertIn("zhDirectorSourceAllowed", self.script)
        self.assertIn("net.minecraft.server.rcon.RconConsoleSource", self.script)
        self.assertIn("net.minecraft.server.level.ServerPlayer", self.script)
        self.assertIn(
            "String(rawSource.getUUID()) === zhEntityUuid(player)", self.script
        )
        self.assertIn("const ZH_CONTROL_TTL_SECONDS = 90", self.script)
        self.assertIn("control_request", self.script)
        queue = self.script[
            self.script.index("function zhQueueDirectorRequest") :
            self.script.index("function zhDirectorApparitionBranch")
        ]
        self.assertIn(
            "run scoreboard players get #world ${ZH_WORLD_OBJECTIVE}", queue
        )
        self.assertNotIn(
            "run data get storage ${ZH_CONTROL_STORAGE} control_request", queue
        )
        self.assertIn("this is not an execution receipt", self.script)
        for public_name, profile in (
            ("echo", "echo_01"),
            ("threshold", "threshold_01"),
            ("motion-echo", "motion_echo_01"),
            ("light-fault", "light_fault_01"),
        ):
            self.assertIn(f"['{public_name}', '{profile}']", self.script)
        self.assertNotIn("zapegscene ", self.script)
        self.assertNotIn("Commands.argument('profile'", self.script)


class ScriptedRoll:
    """Deterministic stand-in for random.Random in planner tests.

    random() defaults to 0.0 (every probability gate opens) and choice/
    choices default to the first element; queue explicit values to steer.
    """

    def __init__(self, randoms=(), picks=()):
        self.randoms = list(randoms)
        self.picks = list(picks)

    def random(self):
        return self.randoms.pop(0) if self.randoms else 0.0

    def choice(self, seq):
        items = list(seq)
        return items[self.picks.pop(0) if self.picks else 0]

    def choices(self, seq, weights=None, k=1):
        items = list(seq)
        return [items[self.picks.pop(0) if self.picks else 0]]


class StalkMemoryTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.clock = FakeClock()
        self.store = DirectorStore(
            Path(self.temp.name) / "heraldor.sqlite3", clock=self.clock
        )
        self.addCleanup(self.store.close)

    def test_visits_collapse_into_coarse_cells_and_hint_hits_cell_centre(self) -> None:
        store = self.store
        store.record_stalk_visit(WORLD_TOKEN, "Alice", 100.4, 200.6)
        store.record_stalk_visit(WORLD_TOKEN, "Alice", 101.9, 201.1)
        store.record_stalk_visit(WORLD_TOKEN, "Alice", 1600.0, 2400.0)

        rows = store.connection.execute(
            "SELECT cell_x, cell_z, visits FROM stalk_cells ORDER BY cell_x, cell_z"
        ).fetchall()
        self.assertEqual(len(rows), 2)
        # 100/32 and 101/32 share cell (3, 6); the two visits merged.
        self.assertEqual((rows[0]["cell_x"], rows[0]["cell_z"]), (3, 6))
        self.assertEqual(rows[0]["visits"], 2)
        self.assertEqual((rows[1]["cell_x"], rows[1]["cell_z"]), (50, 75))

        hint = store.stalk_hint(WORLD_TOKEN, "Alice", rng=ScriptedRoll(picks=[0]))
        self.assertEqual(hint, (3 * 32 + 16, 6 * 32 + 16))
        hint = store.stalk_hint(WORLD_TOKEN, "Alice", rng=ScriptedRoll(picks=[1]))
        self.assertEqual(hint, (50 * 32 + 16, 75 * 32 + 16))
        self.assertIsNone(store.stalk_hint(WORLD_TOKEN, "Bob"))

    def test_world_change_purges_every_other_worlds_cells(self) -> None:
        store = self.store
        store.record_stalk_visit(WORLD_TOKEN, "Alice", 100.0, 200.0)
        store.record_stalk_visit(WORLD_TOKEN + 1, "Alice", 500.0, 600.0)
        self.assertIsNone(store.stalk_hint(WORLD_TOKEN, "Alice"))
        self.assertEqual(
            store.stalk_hint(WORLD_TOKEN + 1, "Alice", rng=ScriptedRoll()),
            (15 * 32 + 16, 18 * 32 + 16),
        )

    def test_cells_are_capped_and_the_oldest_are_forgotten(self) -> None:
        store = self.store
        for index in range(60):
            self.clock.value += 1
            store.record_stalk_visit(
                WORLD_TOKEN, "Alice", index * 64.0, 0.0
            )
        remaining = int(
            store.connection.execute(
                "SELECT COUNT(*) FROM stalk_cells WHERE subject = 'alice'"
            ).fetchone()[0]
        )
        self.assertEqual(remaining, 48)
        # The first recorded cells were the oldest and are gone.
        self.assertIsNone(
            store.connection.execute(
                "SELECT 1 FROM stalk_cells WHERE cell_x = 0 AND cell_z = 0"
            ).fetchone()
        )

    def test_invalid_subjects_and_coordinates_are_refused(self) -> None:
        store = self.store
        with self.assertRaises(ValueError):
            store.record_stalk_visit(WORLD_TOKEN, "bad name", 0.0, 0.0)
        with self.assertRaises(ValueError):
            store.record_stalk_visit(WORLD_TOKEN, "Alice", float("nan"), 0.0)
        with self.assertRaises(ValueError):
            store.record_stalk_visit(WORLD_TOKEN, "Alice", 40_000_000.0, 0.0)


class DeathIngestTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.clock = FakeClock()
        self.store = DirectorStore(
            Path(self.temp.name) / "heraldor.sqlite3", clock=self.clock
        )
        self.addCleanup(self.store.close)

    def test_only_the_newest_death_carries_a_site(self) -> None:
        result = self.store.ingest_death(
            WORLD_TOKEN, "Alice", 3, (100, 64, -30, "minecraft:overworld")
        )
        self.assertEqual(result.previous_high_water, 0)
        self.assertEqual(result.high_water, 3)
        self.assertEqual(len(result.death_event_ids), 3)
        rows = self.store.connection.execute(
            "SELECT payload_json FROM events WHERE kind = 'player_death' ORDER BY created_at, event_id"
        ).fetchall()
        payloads = [json.loads(str(row["payload_json"])) for row in rows]
        self.assertNotIn("site", payloads[0])
        self.assertNotIn("site", payloads[1])
        self.assertEqual(payloads[2]["site"], {"x": 100, "y": 64, "z": -30})
        self.assertEqual(payloads[2]["dimension"], "minecraft:overworld")

    def test_reingestion_is_idempotent_and_regression_is_flagged(self) -> None:
        first = self.store.ingest_death(WORLD_TOKEN, "Alice", 2, None)
        again = self.store.ingest_death(WORLD_TOKEN, "Alice", 2, None)
        self.assertEqual(again.death_event_ids, ())
        self.assertFalse(again.regression)
        regression = self.store.ingest_death(WORLD_TOKEN, "Alice", 1, None)
        self.assertTrue(regression.regression)
        self.assertEqual(self.store.death_high_water(WORLD_TOKEN, "Alice"), 2)
        self.assertEqual(len(first.death_event_ids), 2)

    def test_implausible_jumps_are_quarantined(self) -> None:
        result = self.store.ingest_death(WORLD_TOKEN, "Alice", 99, None)
        self.assertTrue(result.quarantined)
        self.assertEqual(self.store.death_high_water(WORLD_TOKEN, "Alice"), 0)
        self.assertEqual(
            self.store.connection.execute(
                "SELECT COUNT(*) FROM events WHERE kind = 'player_death'"
            ).fetchone()[0],
            0,
        )

    def test_death_counters_are_per_world_and_per_player(self) -> None:
        self.store.ingest_death(WORLD_TOKEN, "Alice", 1, None)
        self.assertEqual(self.store.death_high_water(WORLD_TOKEN + 1, "Alice"), 0)
        self.assertEqual(self.store.death_high_water(WORLD_TOKEN, "Bob"), 0)


class SceneSchedulerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.clock = FakeClock()
        self.store = DirectorStore(
            Path(self.temp.name) / "heraldor.sqlite3", clock=self.clock
        )
        self.addCleanup(self.store.close)

    def start_phase(self, phase: str, nonce: int = 900) -> None:
        outcome = heraldor_service.process_control_request(
            self.store,
            control_request("phase_start", phase, nonce=nonce),
            observed_world_token=WORLD_TOKEN,
        )
        self.assertEqual(outcome.status, "delivered")

    def deliver_scene(self, subject: str, nonce: int) -> None:
        request = control_request("scene_trigger", "echo_01", subject, nonce=nonce)
        with patch.object(
            heraldor_service,
            "rcon",
            return_value=f"scene dispatched event={request.event_id}",
        ):
            outcome = heraldor_service.process_control_request(
                self.store, request, observed_world_token=WORLD_TOKEN
            )
        self.assertEqual(outcome.status, "delivered")

    def test_dormant_and_paused_campaigns_never_plan(self) -> None:
        self.assertIsNone(
            self.store.plan_and_reserve_scene(WORLD_TOKEN, ["Alice"], rng=ScriptedRoll())
        )
        self.start_phase("presence")
        heraldor_service.process_control_request(
            self.store,
            control_request("pause", nonce=901),
            observed_world_token=WORLD_TOKEN,
        )
        self.assertIsNone(
            self.store.plan_and_reserve_scene(WORLD_TOKEN, ["Alice"], rng=ScriptedRoll())
        )

    def test_opening_beat_then_cluster_beat_then_silence(self) -> None:
        store = self.store
        self.start_phase("presence")
        policy = store.policy

        opening = store.plan_and_reserve_scene(WORLD_TOKEN, ["Alice"], rng=ScriptedRoll())
        self.assertIsNotNone(opening)
        self.assertEqual(opening.reason, "cluster_open")
        self.assertEqual(opening.profile, "echo_01")
        self.assertEqual(opening.subject, "Alice")
        # The reservation itself is a scene in flight: no double-planning.
        self.assertIsNone(
            store.plan_and_reserve_scene(WORLD_TOKEN, ["Alice"], rng=ScriptedRoll())
        )
        store.mark_attempting(opening.event_id)
        store.finish_attempt(opening.event_id, delivered=True)

        # Inside the night the per-subject gap relaxes to the cluster gap.
        self.clock.value += policy.cluster_subject_gap_seconds + 1
        beat = store.plan_and_reserve_scene(WORLD_TOKEN, ["Alice"], rng=ScriptedRoll())
        self.assertIsNotNone(beat)
        self.assertEqual(beat.reason, "cluster_beat")
        store.mark_attempting(beat.event_id)
        store.finish_attempt(beat.event_id, delivered=True)

        # After the open window but before the silence: the night is over.
        self.clock.value += policy.cluster_open_seconds + 60
        self.assertIsNone(
            store.plan_and_reserve_scene(WORLD_TOKEN, ["Alice"], rng=ScriptedRoll())
        )

        # After the full silence a new night may open.
        self.clock.value += policy.cluster_silence_seconds
        reopened = store.plan_and_reserve_scene(WORLD_TOKEN, ["Alice"], rng=ScriptedRoll())
        self.assertIsNotNone(reopened)
        self.assertEqual(reopened.reason, "cluster_open")

    def test_cluster_budget_is_a_hard_cap(self) -> None:
        store = self.store
        self.start_phase("presence")
        policy = store.policy
        for index in range(policy.cluster_scene_budget):
            plan = store.plan_and_reserve_scene(WORLD_TOKEN, ["Alice"], rng=ScriptedRoll())
            self.assertIsNotNone(plan)
            store.mark_attempting(plan.event_id)
            store.finish_attempt(plan.event_id, delivered=True)
            self.clock.value += policy.cluster_subject_gap_seconds + 1
        self.assertIsNone(
            store.plan_and_reserve_scene(WORLD_TOKEN, ["Alice"], rng=ScriptedRoll())
        )

    def test_story_events_impose_a_quiet_window(self) -> None:
        store = self.store
        self.start_phase("presence")
        store.ingest_servant_score(3, world_token=WORLD_TOKEN)
        self.assertIsNone(
            store.plan_and_reserve_scene(WORLD_TOKEN, ["Alice"], rng=ScriptedRoll())
        )
        self.clock.value += store.policy.major_quiet_seconds + 1
        self.assertIsNotNone(
            store.plan_and_reserve_scene(WORLD_TOKEN, ["Alice"], rng=ScriptedRoll())
        )

    def test_probability_gate_keeps_quiet_nights_quiet(self) -> None:
        store = self.store
        self.start_phase("presence")
        # random() above the open probability means no scene, even eligible.
        reluctant = ScriptedRoll(randoms=[0.99])
        self.assertIsNone(
            store.plan_and_reserve_scene(WORLD_TOKEN, ["Alice"], rng=reluctant)
        )

    def test_aftermath_forces_footsteps_and_is_consumed(self) -> None:
        store = self.store
        self.start_phase("servants")
        store.record_servant_aftermath(WORLD_TOKEN, "Alice", 1)

        plan = store.plan_and_reserve_scene(WORLD_TOKEN, ["Alice"], rng=ScriptedRoll())
        self.assertIsNotNone(plan)
        self.assertEqual(plan.reason, "aftermath")
        self.assertEqual(plan.profile, "footsteps_01")
        store.mark_attempting(plan.event_id)
        store.finish_attempt(plan.event_id, delivered=True)

        # The flag was consumed: the next beat falls back to normal choice.
        self.clock.value += store.policy.cluster_subject_gap_seconds + 1
        followup = store.plan_and_reserve_scene(WORLD_TOKEN, ["Alice"], rng=ScriptedRoll())
        self.assertIsNotNone(followup)
        self.assertNotEqual(followup.reason, "aftermath")

    def test_grave_echo_answers_an_old_death_at_its_site(self) -> None:
        store = self.store
        self.start_phase("servants")
        store.ingest_death(WORLD_TOKEN, "Alice", 1, (100, 64, -30, "minecraft:overworld"))
        self.clock.value += store.policy.grave_echo_min_age_seconds + 1

        plan = store.plan_and_reserve_scene(WORLD_TOKEN, ["Alice"], rng=ScriptedRoll())
        self.assertIsNotNone(plan)
        self.assertEqual(plan.reason, "grave_echo")
        self.assertEqual(plan.profile, "footsteps_01")
        self.assertEqual(plan.hint, (100, -30))
        death_status = store.connection.execute(
            "SELECT status FROM events WHERE kind = 'player_death'"
        ).fetchone()["status"]
        self.assertEqual(death_status, "echoed")

        store.mark_attempting(plan.event_id)
        store.finish_attempt(plan.event_id, delivered=True)
        self.clock.value += store.policy.cluster_subject_gap_seconds + 1
        # The echoed death is spent; the next beat is an ordinary one.
        followup = store.plan_and_reserve_scene(WORLD_TOKEN, ["Alice"], rng=ScriptedRoll())
        self.assertIsNotNone(followup)
        self.assertEqual(followup.reason, "cluster_beat")

    def test_grave_echo_never_answers_a_fresh_death(self) -> None:
        store = self.store
        self.start_phase("servants")
        store.ingest_death(WORLD_TOKEN, "Alice", 1, (100, 64, -30, "minecraft:overworld"))
        plan = store.plan_and_reserve_scene(WORLD_TOKEN, ["Alice"], rng=ScriptedRoll())
        self.assertIsNotNone(plan)
        self.assertNotEqual(plan.reason, "grave_echo")

    def test_ground_scenes_carry_a_stalking_hint_when_memory_exists(self) -> None:
        store = self.store
        self.start_phase("presence")
        store.record_stalk_visit(WORLD_TOKEN, "Alice", 100.0, 200.0)
        plan = store.plan_and_reserve_scene(WORLD_TOKEN, ["Alice"], rng=ScriptedRoll())
        self.assertIsNotNone(plan)
        self.assertEqual(plan.profile, "echo_01")
        self.assertEqual(plan.hint, (3 * 32 + 16, 6 * 32 + 16))

    def test_rehearsals_never_open_or_extend_a_cluster(self) -> None:
        store = self.store
        self.start_phase("presence")
        request = control_request("scene_rehearse", "echo_01", "Alice", nonce=950)
        with patch.object(
            heraldor_service,
            "rcon",
            return_value="scene dispatched event=00000000-0000-0000-0000-000000000099",
        ):
            heraldor_service.process_control_request(
                store, request, observed_world_token=WORLD_TOKEN
            )
        plan = store.plan_and_reserve_scene(WORLD_TOKEN, ["Alice"], rng=ScriptedRoll())
        self.assertIsNotNone(plan)
        self.assertEqual(plan.reason, "cluster_open")

    def test_phase_gates_apply_to_planned_profiles(self) -> None:
        store = self.store
        self.start_phase("presence")
        # Pick the last allowed profile: whisper_steps_01 (presence-allowed).
        plan = store.plan_and_reserve_scene(
            WORLD_TOKEN, ["Alice"], rng=ScriptedRoll(picks=[0, 4])
        )
        self.assertIsNotNone(plan)
        self.assertEqual(plan.profile, "whisper_steps_01")
        # manifestation-only profiles are never in the presence pool.
        self.assertNotIn(plan.profile, {"light_fault_01", "chroma_break_01"})


class SchedulerDispatchTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.clock = FakeClock()
        self.store = DirectorStore(
            Path(self.temp.name) / "heraldor.sqlite3", clock=self.clock
        )
        self.addCleanup(self.store.close)

    def test_scheduler_cycle_dispatches_with_hint_and_closes_out(self) -> None:
        store = self.store
        heraldor_service.process_control_request(
            store,
            control_request("phase_start", "presence", nonce=970),
            observed_world_token=WORLD_TOKEN,
        )
        store.record_stalk_visit(WORLD_TOKEN, "Alice", 100.0, 200.0)
        commands: list[str] = []
        with patch.object(
            heraldor_service, "online_players", return_value=["Alice"]
        ), patch.object(
            heraldor_service,
            "rcon",
            side_effect=lambda command: commands.append(command)
            or "scene dispatched event=x",
        ), patch.object(
            heraldor_service, "SCHEDULER_ENABLED", True
        ), patch(
            "heraldor_director.random"
        ) as director_random:
            director_random.Random.return_value = ScriptedRoll()
            heraldor_service.scene_scheduler_cycle(store, WORLD_TOKEN)
        self.assertEqual(len(commands), 1)
        self.assertTrue(commands[0].startswith("zapegscene trigger Alice "))
        self.assertIn(" echo_01 ", commands[0])
        self.assertTrue(commands[0].endswith(f" {3 * 32 + 16} {6 * 32 + 16}"))
        status = store.connection.execute(
            "SELECT status FROM events WHERE kind = 'director_scene'"
        ).fetchone()["status"]
        self.assertEqual(status, "delivered")

    def test_scheduler_cycle_stays_silent_when_disabled(self) -> None:
        with patch.object(heraldor_service, "SCHEDULER_ENABLED", False):
            with patch.object(heraldor_service, "online_players") as players:
                heraldor_service.scene_scheduler_cycle(self.store, WORLD_TOKEN)
        players.assert_not_called()


if __name__ == "__main__":
    unittest.main()
