import asyncio
import hashlib
import json
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from heraldor_director import (  # noqa: E402
    AUDIO_EVENT_TYPE,
    AudioDelivery,
    DirectorStateLock,
    DirectorStore,
    SERVANT_AUDIO_CLIP_ID,
    restore_snapshot,
    snapshot_lock_path,
    voice_lock_path,
)
from heraldor_voice import (  # noqa: E402
    ClipSpec,
    RelayConfig,
    _gateway_presence_options,
    _play_delivery,
    load_clip_catalog,
    relay_config_from_env,
    resolve_delivery,
)


class FakeClock:
    def __init__(self, value: int = 10_000) -> None:
        self.value = value

    def __call__(self) -> int:
        return self.value


class VoiceOutboxTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.db_path = self.root / "heraldor.sqlite3"
        self.snapshot_path = self.root / "backup" / "heraldor.sqlite3"
        self.clock = FakeClock(int(time.time()))

    def tearDown(self) -> None:
        self.temp.cleanup()

    def open_store(self, **kwargs) -> DirectorStore:
        return DirectorStore(
            self.db_path,
            snapshot_path=self.snapshot_path,
            clock=self.clock,
            **kwargs,
        )

    def test_live_audio_is_pending_only_when_sink_was_enabled_at_creation(self) -> None:
        with self.open_store() as store:
            store.ingest_servant_score(3, world_token=111111)
            status = store.connection.execute(
                "SELECT status FROM outbox"
            ).fetchone()[0]
            self.assertEqual(status, "suppressed_no_sink")

        # Enabling the sink later must never revive the historical row.
        with self.open_store(audio_sink_enabled=True) as store:
            self.assertEqual(
                store.connection.execute(
                    "SELECT status FROM outbox WHERE event_id LIKE ?",
                    ("%111111",),
                ).fetchone()[0],
                "suppressed_no_sink",
            )
            store.ingest_servant_score(3, world_token=222222)
            rows = store.connection.execute(
                "SELECT status FROM outbox ORDER BY created_at, event_id"
            ).fetchall()
            self.assertEqual(sorted(row[0] for row in rows), ["pending", "suppressed_no_sink"])

    def test_rehearsal_claim_is_atomic_and_snapshot_precedes_playback(self) -> None:
        with self.open_store() as first:
            event_id = first.enqueue_audio_rehearsal()
            delivery = first.claim_next_audio()
            self.assertEqual(delivery.event_id, event_id)
            self.assertTrue(delivery.rehearsal)

            snapshot = sqlite3.connect(self.snapshot_path)
            try:
                status = snapshot.execute(
                    "SELECT status FROM outbox WHERE event_id = ?", (event_id,)
                ).fetchone()[0]
                self.assertEqual(status, "attempting")
            finally:
                snapshot.close()

            with self.open_store(recover_interrupted_attempts=False) as second:
                self.assertIsNone(second.claim_next_audio())

            self.assertTrue(first.finish_audio(event_id, status="delivered"))
            self.assertEqual(
                first.connection.execute(
                    "SELECT COUNT(*) FROM story_flags"
                ).fetchone()[0],
                0,
            )

    def test_only_voice_worker_recovers_an_interrupted_audio_attempt(self) -> None:
        with self.open_store() as store:
            event_id = store.enqueue_audio_rehearsal()
            store.claim_next_audio()

        with self.open_store() as director_restart:
            status = director_restart.connection.execute(
                "SELECT status FROM outbox WHERE event_id = ?", (event_id,)
            ).fetchone()[0]
            self.assertEqual(status, "attempting")
            self.assertEqual(director_restart.recover_interrupted_audio(), 1)
            status = director_restart.connection.execute(
                "SELECT status FROM outbox WHERE event_id = ?", (event_id,)
            ).fetchone()[0]
            self.assertEqual(status, "ambiguous")

    def test_expiry_and_rehearsal_rate_limit_are_terminal(self) -> None:
        with self.open_store() as store:
            expired_id = store.enqueue_audio_rehearsal()
            self.clock.value += 120
            self.assertIsNone(store.claim_next_audio())
            self.assertEqual(
                store.connection.execute(
                    "SELECT status FROM outbox WHERE event_id = ?", (expired_id,)
                ).fetchone()[0],
                "suppressed_expired",
            )

            first_id = store.enqueue_audio_rehearsal()
            first = store.claim_next_audio()
            self.assertEqual(first.event_id, first_id)
            store.finish_audio(first_id, status="delivered")
            second_id = store.enqueue_audio_rehearsal()
            self.assertIsNone(store.claim_next_audio())
            self.assertEqual(
                store.connection.execute(
                    "SELECT status FROM outbox WHERE event_id = ?", (second_id,)
                ).fetchone()[0],
                "suppressed_rate_limit",
            )

    def test_restore_refuses_while_voice_worker_lock_is_held(self) -> None:
        with self.open_store() as store:
            store.enqueue_audio_rehearsal()
        with DirectorStateLock(voice_lock_path(self.db_path)):
            with self.assertRaisesRegex(RuntimeError, "state is locked"):
                restore_snapshot(self.db_path, self.snapshot_path)

    def test_snapshot_replace_is_serialized_across_processes(self) -> None:
        with self.open_store() as store:
            store.enqueue_audio_rehearsal()

        ready = self.root / "child-ready"
        module_root = Path(__file__).resolve().parents[1]
        child_code = (
            "import sys; from pathlib import Path; "
            "sys.path.insert(0, sys.argv[1]); "
            "from heraldor_director import DirectorStore; "
            "store=DirectorStore(sys.argv[2], snapshot_path=sys.argv[3], "
            "recover_interrupted_attempts=False); "
            "Path(sys.argv[4]).write_text('ready'); "
            "store.backup_snapshot(); store.close()"
        )
        process = None
        with DirectorStateLock(snapshot_lock_path(self.db_path)):
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-c",
                    child_code,
                    str(module_root),
                    str(self.db_path),
                    str(self.snapshot_path),
                    str(ready),
                ]
            )
            deadline = time.time() + 5
            while not ready.exists() and time.time() < deadline:
                time.sleep(0.02)
            self.assertTrue(ready.exists(), "child did not reach the snapshot lock")
            time.sleep(0.1)
            self.assertIsNone(process.poll(), "child bypassed the snapshot lock")

        self.assertEqual(process.wait(timeout=5), 0)
        snapshot = sqlite3.connect(self.snapshot_path)
        try:
            self.assertEqual(snapshot.execute("PRAGMA integrity_check").fetchone()[0], "ok")
        finally:
            snapshot.close()


class ClipCatalogTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.asset = self.root / "clip.ogg"
        self.asset.write_bytes(b"approved opus fixture")
        self.digest = hashlib.sha256(self.asset.read_bytes()).hexdigest()
        self.manifest = self.root / "clips.json"
        self.write_manifest(self.digest)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_manifest(self, digest: str, filename: str = "clip.ogg") -> None:
        self.manifest.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "clips": {
                        SERVANT_AUDIO_CLIP_ID: {
                            "filename": filename,
                            "sha256": digest,
                            "duration_seconds": 23.5,
                            "codec": "opus",
                            "sample_rate": 48000,
                            "channels": 2,
                        }
                    },
                }
            ),
            encoding="utf-8",
        )

    def test_catalog_hashes_asset_and_resolves_typed_event(self) -> None:
        catalog = load_clip_catalog(self.manifest, self.root, verify_media=False)
        event_id = "rehearsal:audio:test"
        delivery = AudioDelivery(
            event_id,
            {
                "event_id": event_id,
                "type": AUDIO_EVENT_TYPE,
                "clip_id": SERVANT_AUDIO_CLIP_ID,
                "expires_at": 2_000,
                "rehearsal": True,
            },
            True,
        )
        self.assertEqual(resolve_delivery(delivery, catalog, now=1_000).path, self.asset)

        routed = dict(delivery.payload, url="https://example.invalid/audio")
        with self.assertRaisesRegex(ValueError, "forbidden routing"):
            resolve_delivery(AudioDelivery(event_id, routed, True), catalog, now=1_000)

    def test_catalog_rejects_hash_mismatch_and_traversal(self) -> None:
        self.write_manifest("0" * 64)
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            load_clip_catalog(self.manifest, self.root, verify_media=False)

        self.write_manifest(self.digest, "../clip.ogg")
        with self.assertRaisesRegex(ValueError, "basename"):
            load_clip_catalog(self.manifest, self.root, verify_media=False)

    def test_rehearsal_channel_must_not_equal_live_channel(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "HERALDOR_DISCORD_GUILD_ID": "123456",
                "HERALDOR_DISCORD_VOICE_CHANNEL_ID": "654321",
                "HERALDOR_DISCORD_TEST_VOICE_CHANNEL_ID": "654321",
            },
            clear=False,
        ):
            with self.assertRaisesRegex(ValueError, "must be different"):
                relay_config_from_env()

    def test_shared_bot_mode_preserves_dci_presence(self) -> None:
        env = {
            "HERALDOR_DISCORD_GUILD_ID": "123456",
            "HERALDOR_DISCORD_VOICE_CHANNEL_ID": "654321",
            "HERALDOR_DISCORD_TEST_VOICE_CHANNEL_ID": "777777",
            "HERALDOR_DISCORD_SHARED_BOT": "true",
        }
        with patch.dict("os.environ", env, clear=True):
            self.assertTrue(relay_config_from_env().shared_bot)

        class Discord:
            class Status:
                invisible = object()

        self.assertEqual(
            _gateway_presence_options(Discord, shared_bot=True),
            {},
        )
        self.assertIs(
            _gateway_presence_options(Discord, shared_bot=False)["status"],
            Discord.Status.invisible,
        )

        env["HERALDOR_DISCORD_SHARED_BOT"] = "sometimes"
        with patch.dict("os.environ", env, clear=True):
            with self.assertRaisesRegex(ValueError, "must be true or false"):
                relay_config_from_env()


class VoiceTransportTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.db_path = self.root / "heraldor.sqlite3"
        self.snapshot_path = self.root / "backup" / "heraldor.sqlite3"
        self.asset = self.root / "clip.ogg"
        self.asset.write_bytes(b"fixture")
        self.clock = FakeClock(int(time.time()))

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_output_is_deafened_plays_once_and_disconnects(self) -> None:
        class VoiceState:
            deaf = False
            self_deaf = False

        class Member:
            bot = False
            voice = VoiceState()

        class Voice:
            def __init__(self) -> None:
                self.disconnected = False
                self.play_calls = 0
                self.consume_source = True

            def play(self, source, *, after) -> None:
                self.play_calls += 1
                if self.consume_source:
                    while source.read():
                        pass
                after(None)

            async def disconnect(self, *, force) -> None:
                self.disconnected = force

        voice = Voice()

        class Guild:
            id = 123456
            voice_client = None

        class Channel:
            guild = Guild()

            def __init__(self) -> None:
                self.connect_kwargs = None
                self.members = [Member()]
                self.drop_listener_during_connect = False

            async def connect(self, **kwargs):
                self.connect_kwargs = kwargs
                if self.drop_listener_during_connect:
                    self.members = []
                return voice

        channel = Channel()

        class Client:
            def get_channel(self, channel_id):
                return channel if channel_id == 654321 else None

        class AudioSource:
            pass

        class Source:
            next_error = None

            def __init__(self, *_args, **_kwargs) -> None:
                self.cleaned = False
                self._current_error = Source.next_error
                self.frames = [b"opus-frame", b""]

            def read(self) -> bytes:
                return self.frames.pop(0)

            def cleanup(self) -> None:
                self.cleaned = True

        class Discord:
            VoiceChannel = Channel

        Discord.AudioSource = AudioSource
        Discord.FFmpegOpusAudio = Source

        config = RelayConfig(
            self.db_path,
            self.snapshot_path,
            self.root / "token",
            123456,
            777777,
            654321,
            0.5,
            15,
        )
        catalog = {
            SERVANT_AUDIO_CLIP_ID: ClipSpec(
                SERVANT_AUDIO_CLIP_ID,
                self.asset,
                hashlib.sha256(self.asset.read_bytes()).hexdigest(),
                1,
            )
        }
        with DirectorStore(
            self.db_path,
            snapshot_path=self.snapshot_path,
            clock=self.clock,
        ) as store:
            event_id = store.enqueue_audio_rehearsal()
            delivery = store.claim_next_audio()
            asyncio.run(
                _play_delivery(
                    Client(), Discord, store, catalog, config, delivery, "secret-token"
                )
            )
            row = store.connection.execute(
                "SELECT status FROM outbox WHERE event_id = ?", (event_id,)
            ).fetchone()
            self.assertEqual(row[0], "delivered")

            self.clock.value += 31
            left_id = store.enqueue_audio_rehearsal()
            left = store.claim_next_audio()
            channel.drop_listener_during_connect = True
            asyncio.run(
                _play_delivery(
                    Client(), Discord, store, catalog, config, left, "secret-token"
                )
            )
            left_status = store.connection.execute(
                "SELECT status FROM outbox WHERE event_id = ?", (left_id,)
            ).fetchone()[0]
            self.assertEqual(left_status, "suppressed_empty_channel")
            channel.drop_listener_during_connect = False
            channel.members = [Member()]

            # discord.py can invoke after(None) on a truncated disconnect. A
            # clean callback without source EOF must remain terminal ambiguous.
            truncated_id = store.enqueue_audio_rehearsal()
            truncated = store.claim_next_audio()
            voice.consume_source = False
            asyncio.run(
                _play_delivery(
                    Client(), Discord, store, catalog, config, truncated, "secret-token"
                )
            )
            truncated_status = store.connection.execute(
                "SELECT status FROM outbox WHERE event_id = ?", (truncated_id,)
            ).fetchone()[0]
            self.assertEqual(truncated_status, "ambiguous")

            # A failed FFmpeg stream may also hand the player's callback a
            # clean-looking result; underlying source errors must not count as EOF.
            self.clock.value += 31
            errored_id = store.enqueue_audio_rehearsal()
            errored = store.claim_next_audio()
            voice.consume_source = True
            Source.next_error = RuntimeError("ffmpeg failed")
            asyncio.run(
                _play_delivery(
                    Client(), Discord, store, catalog, config, errored, "secret-token"
                )
            )
            errored_status = store.connection.execute(
                "SELECT status FROM outbox WHERE event_id = ?", (errored_id,)
            ).fetchone()[0]
            self.assertEqual(errored_status, "ambiguous")

        self.assertEqual(voice.play_calls, 3)
        self.assertTrue(voice.disconnected)
        self.assertTrue(channel.connect_kwargs["self_deaf"])
        self.assertFalse(channel.connect_kwargs["self_mute"])

    def test_no_audible_listener_is_terminal_without_connecting(self) -> None:
        class VoiceState:
            deaf = False
            self_deaf = True

        class Member:
            bot = False
            voice = VoiceState()

        class Guild:
            id = 123456

        class Channel:
            guild = Guild()
            members = [Member()]

            async def connect(self, **_kwargs):
                raise AssertionError("empty channel must never be joined")

        channel = Channel()

        class Client:
            def get_channel(self, _channel_id):
                return channel

        class Discord:
            VoiceChannel = Channel

        config = RelayConfig(
            self.db_path,
            self.snapshot_path,
            self.root / "token",
            123456,
            777777,
            654321,
            0.5,
            15,
        )
        catalog = {
            SERVANT_AUDIO_CLIP_ID: ClipSpec(
                SERVANT_AUDIO_CLIP_ID,
                self.asset,
                hashlib.sha256(self.asset.read_bytes()).hexdigest(),
                1,
            )
        }
        with DirectorStore(
            self.db_path,
            snapshot_path=self.snapshot_path,
            clock=self.clock,
        ) as store:
            event_id = store.enqueue_audio_rehearsal()
            delivery = store.claim_next_audio()
            asyncio.run(
                _play_delivery(
                    Client(), Discord, store, catalog, config, delivery, "secret-token"
                )
            )
            status = store.connection.execute(
                "SELECT status FROM outbox WHERE event_id = ?", (event_id,)
            ).fetchone()[0]
            self.assertEqual(status, "suppressed_empty_channel")


if __name__ == "__main__":
    unittest.main()
