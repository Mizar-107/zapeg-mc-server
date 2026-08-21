"""Campaign engine tests: loader validation, stepping, waits, pacing,
rehearsal purity and the `/zapeg-lore story` control bridge."""

import json
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

import yaml  # noqa: E402

import heraldor as heraldor_service  # noqa: E402
from heraldor_campaign import (  # noqa: E402
    CampaignEngine,
    CampaignError,
    load_campaign,
)
from heraldor_director import (  # noqa: E402
    DirectorStore,
    parse_control_request,
)

WORLD_TOKEN = 17082026
NPC_ROOT = Path(__file__).resolve().parents[1]
SHIPPED_CAMPAIGN = NPC_ROOT / "campaign-heraldor.yml"


class FakeClock:
    def __init__(self, value: int = 1_780_000_000) -> None:
        self.value = value

    def __call__(self) -> int:
        return self.value


class FakeExecutor:
    def __init__(self, online=("Alice", "Bob"), night=True):
        self.online = list(online)
        self.night = night
        self.scenes = []
        self.whispers = []
        self.globals = []
        self.global_styles = []
        self.discords = []
        self.servants = []
        self.notices = []
        self.scene_result = (True, "scene dispatched event=x")

    def online_players(self):
        return list(self.online)

    def is_night(self):
        return self.night

    def scene(self, target, profile, event_id, rehearsal, ttl_override=None):
        self.scenes.append((target, profile, event_id, rehearsal, ttl_override))
        return self.scene_result

    def whisper(self, target, line):
        self.whispers.append((target, line))
        return True

    def global_line(self, line, style="named"):
        self.globals.append(line)
        self.global_styles.append(style)
        return True

    def discord(self, line):
        self.discords.append(line)
        return True, ""

    def servant(self, target, live):
        self.servants.append((target, live))
        return True, f"Awakened Heraldor'un Hizmetkârı for {target} — LIVE."

    def notify(self, operator, text):
        self.notices.append((operator, text))


BASE_DOCUMENT = {
    "version": 1,
    "pacing": {
        "cluster_beats": 2,
        "cluster_window_minutes": 30,
        "silence_hours": 40,
    },
    "pools": {
        "generic": ["birinci satır.", "ikinci satır."],
        "dossier": {"Alice": ["alice özel satırı."]},
    },
    "chapters": [
        {
            "id": "one",
            "title": "Bir",
            "tier": "presence",
            "beats": [
                {"type": "whisper", "pool": "dossier", "target": "Alice"},
                {"type": "wait", "manual": True},
                {"type": "scene", "profile": "echo_01", "target": "random"},
            ],
        },
        {
            "id": "two",
            "title": "İki",
            "tier": "servants",
            "beats": [
                {"type": "global", "line": "Yalnız değilsiniz."},
                {"type": "servant_wave", "count": 2, "target": "last_victim"},
                {"type": "wait", "victories": 2},
                {"type": "discord", "line": "sayıyorum."},
            ],
        },
    ],
}


def write_campaign(root: Path, document: dict) -> Path:
    path = root / "campaign.yml"
    path.write_text(
        yaml.safe_dump(document, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return path


class CampaignLoaderTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def load(self, mutate=None):
        document = json.loads(json.dumps(BASE_DOCUMENT))
        if mutate:
            mutate(document)
        return load_campaign(write_campaign(self.root, document))

    def test_valid_campaign_loads_and_expands_servant_waves(self) -> None:
        campaign = self.load()
        self.assertEqual(len(campaign.chapters), 2)
        # servant_wave count 2 expands into two single-servant beats.
        kinds = [beat.type for beat in campaign.chapters[1].beats]
        self.assertEqual(
            kinds, ["global", "servant_wave", "servant_wave", "wait", "discord"]
        )
        self.assertEqual(campaign.pacing.cluster_beats, 2)
        self.assertEqual(campaign.chapter_index("two"), 2)
        self.assertEqual(campaign.chapter_index("2"), 2)
        self.assertIsNone(campaign.chapter_index("99"))

    def test_malformed_campaigns_fail_closed(self) -> None:
        cases = {
            "unknown beat type": lambda d: d["chapters"][0]["beats"].append(
                {"type": "jumpscare"}
            ),
            "unknown profile": lambda d: d["chapters"][0]["beats"].append(
                {"type": "scene", "profile": "nope_01", "target": "random"}
            ),
            "two wait conditions": lambda d: d["chapters"][0]["beats"].append(
                {"type": "wait", "manual": True, "victories": 1}
            ),
            "bad target": lambda d: d["chapters"][0]["beats"].append(
                {"type": "whisper", "pool": "generic", "target": "not a name!"}
            ),
            "missing generic pool": lambda d: d["pools"].pop("generic"),
            "duplicate chapter id": lambda d: d["chapters"].append(
                dict(d["chapters"][0])
            ),
            "dormant tier": lambda d: d["chapters"][0].update(tier="dormant"),
            "line and pool together": lambda d: d["chapters"][0]["beats"].append(
                {"type": "whisper", "pool": "generic", "line": "x", "target": "random"}
            ),
            "oversized wave": lambda d: d["chapters"][0]["beats"].append(
                {"type": "servant_wave", "count": 9, "target": "random"}
            ),
        }
        for name, mutate in cases.items():
            with self.subTest(case=name), self.assertRaises(CampaignError):
                self.load(mutate)

    def test_missing_file_fails_closed(self) -> None:
        with self.assertRaises(CampaignError):
            load_campaign(self.root / "missing.yml")

    def test_shipped_campaign_is_valid_and_escalates_to_the_finale(self) -> None:
        campaign = load_campaign(SHIPPED_CAMPAIGN)
        self.assertEqual(len(campaign.chapters), 5)
        tiers = [chapter.tier for chapter in campaign.chapters]
        self.assertEqual(
            tiers,
            ["presence", "presence", "servants", "servants", "manifestation"],
        )
        # The finale chapter contains the colossus ladder and the visitation.
        finale_profiles = [
            beat.profile
            for beat in campaign.chapters[-1].beats
            if beat.type == "scene"
        ]
        self.assertEqual(finale_profiles.count("colossus_01"), 5)
        self.assertIn("visitation_01", finale_profiles)
        # The dossier covers the five personalized players.
        self.assertEqual(
            set(campaign.dossier),
            {"SalihKarahan", "kralxlarge", "MertOnal", "eminomi12", "Thekingim"},
        )
        # A servant-victory wait arms the chapter-4 → threshold tie-in.
        waits = [
            beat.wait_victories
            for chapter in campaign.chapters
            for beat in chapter.beats
            if beat.type == "wait" and beat.wait_victories
        ]
        self.assertIn(3, waits)


class CampaignEngineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.clock = FakeClock()
        self.store = DirectorStore(
            self.root / "heraldor.sqlite3", clock=self.clock
        )
        self.addCleanup(self.store.close)
        self.campaign = load_campaign(write_campaign(self.root, BASE_DOCUMENT))
        self.engine = CampaignEngine(self.campaign)
        self.executor = FakeExecutor()
        # M1: give the fixture cohort recorded tenure so autonomous random
        # targeting stays eligible in these tests.
        for name in ("Alice", "Bob"):
            self.store.observe_presence(
                WORLD_TOKEN, name, now=self.clock.value - 24 * 3600
            )

    def now(self) -> int:
        return self.clock.value

    def step(self, *, rehearsal=False, manual=True):
        return self.engine.execute_current_beat(
            self.store,
            WORLD_TOKEN,
            self.executor,
            operator="Mizar__107",
            rehearsal=rehearsal,
            manual=manual,
            now=self.now(),
        )

    def test_start_promotes_tier_and_steps_execute_beats(self) -> None:
        self.assertEqual(self.store.campaign_state(WORLD_TOKEN).phase, "dormant")
        started = self.engine.start(self.store, WORLD_TOKEN, now=self.now())
        self.assertTrue(started.ok)
        self.assertEqual(self.store.campaign_state(WORLD_TOKEN).phase, "presence")

        # Beat 1: dossier whisper to Alice uses her personal line.
        outcome = self.step()
        self.assertTrue(outcome.ok)
        self.assertEqual(self.executor.whispers, [("Alice", "alice özel satırı.")])

        # Beat 2: manual wait — `story next` skips it.
        outcome = self.step()
        self.assertTrue(outcome.ok)
        self.assertIn("wait skipped", outcome.message)

        # Beat 3: scene beat dispatches live and finishes chapter one.
        outcome = self.step()
        self.assertTrue(outcome.ok)
        target, profile, event_id, rehearsal, _ttl = self.executor.scenes[0]
        self.assertIn(target, ("Alice", "Bob"))
        self.assertEqual(profile, "echo_01")
        self.assertFalse(rehearsal)
        # Beat event ids satisfy the runtime's strict UuidArgument.
        self.assertRegex(
            event_id, r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        )
        # Entering chapter two promotes the tier to servants.
        self.assertEqual(self.store.campaign_state(WORLD_TOKEN).phase, "servants")
        # The delivered scene row is auditable with campaign provenance.
        row = self.store.connection.execute(
            "SELECT payload_json, status FROM events WHERE kind = 'campaign_scene'"
        ).fetchone()
        self.assertEqual(row["status"], "delivered")
        self.assertEqual(json.loads(row["payload_json"])["planner"], "campaign")

    def test_last_victim_and_victory_wait_drive_chapter_two(self) -> None:
        self.engine.start(self.store, WORLD_TOKEN, now=self.now())
        self.step()  # whisper
        self.step()  # manual wait
        self.step()  # scene -> records the last victim
        victim = self.executor.scenes[0][0]

        self.step()  # global line
        self.assertEqual(self.executor.globals, ["Yalnız değilsiniz."])

        self.step()  # servant wave 1/2 -> last_victim
        self.step()  # servant wave 2/2
        self.assertEqual(
            self.executor.servants, [(victim, True), (victim, True)]
        )

        # Victory wait: not met, not skipped by autonomy — only real kills.
        blocked = self.engine.autonomous_tick(
            self.store, WORLD_TOKEN, self.executor, now=self.now()
        )
        self.assertIsNone(blocked)
        outcome = self.step(manual=False)
        self.assertFalse(outcome.ok)
        self.assertIn("waiting", outcome.message)
        self.store.ingest_servant_score(2, world_token=WORLD_TOKEN)
        outcome = self.step(manual=False)
        self.assertTrue(outcome.ok)

        self.step()  # discord line
        self.assertEqual(self.executor.discords, ["sayıyorum."])
        self.assertTrue(self.engine.finished(self.engine.progress(self.store, WORLD_TOKEN)))

    def test_offline_target_and_failed_beats_do_not_advance(self) -> None:
        self.engine.start(self.store, WORLD_TOKEN, now=self.now())
        self.executor.online = ["Bob"]  # Alice (named target) is offline
        outcome = self.step()
        self.assertFalse(outcome.ok)
        self.assertIn("offline", outcome.message)
        self.assertEqual(self.engine.progress(self.store, WORLD_TOKEN).beat, 0)

        # A failed runtime dispatch keeps the pointer and salts the retry id.
        self.executor.online = ["Alice"]
        self.step()  # whisper delivered
        self.step()  # wait skipped
        self.executor.scene_result = (False, "another scene is active")
        first_attempt = self.step()
        self.assertFalse(first_attempt.ok)
        progress = self.engine.progress(self.store, WORLD_TOKEN)
        self.assertEqual(progress.beat, 2)
        self.assertEqual(progress.attempt, 1)
        first_id = self.executor.scenes[0][2]
        self.executor.scene_result = (True, "scene dispatched event=x")
        second_attempt = self.step()
        self.assertTrue(second_attempt.ok)
        self.assertNotEqual(self.executor.scenes[1][2], first_id)

    def test_rehearsal_writes_no_campaign_state(self) -> None:
        self.engine.start(self.store, WORLD_TOKEN, now=self.now())
        before = self.store.campaign_progress_raw(WORLD_TOKEN)
        outcome = self.step(rehearsal=True)
        self.assertTrue(outcome.ok)
        # The whisper was previewed to the operator, not sent to the target.
        self.assertEqual(self.executor.whispers, [])
        self.assertEqual(len(self.executor.notices), 1)
        self.assertIn("alice özel satırı.", self.executor.notices[0][1])
        self.assertEqual(self.store.campaign_progress_raw(WORLD_TOKEN), before)
        self.assertIsNone(
            self.store.connection.execute(
                "SELECT 1 FROM events WHERE kind LIKE 'campaign_%'"
            ).fetchone()
        )

        # Scene rehearsal goes through the runtime rehearsal path.
        self.step()  # deliver the whisper
        self.step()  # skip the wait
        outcome = self.step(rehearsal=True)
        self.assertTrue(outcome.ok)
        self.assertTrue(self.executor.scenes[-1][3])
        self.assertEqual(
            self.engine.progress(self.store, WORLD_TOKEN).beat, 2
        )

    def test_autonomy_prefers_night_respects_pacing_and_waits(self) -> None:
        self.engine.start(self.store, WORLD_TOKEN, now=self.now())
        self.engine.set_auto(self.store, WORLD_TOKEN, True, now=self.now())

        # Daytime: actionable beats hold.
        self.executor.night = False
        self.assertIsNone(
            self.engine.autonomous_tick(
                self.store, WORLD_TOKEN, self.executor, now=self.now()
            )
        )
        self.assertEqual(self.executor.whispers, [])

        # Night: the whisper fires and opens a cluster.
        self.executor.night = True
        fired = self.engine.autonomous_tick(
            self.store, WORLD_TOKEN, self.executor, now=self.now()
        )
        self.assertIsNotNone(fired)
        self.assertEqual(len(self.executor.whispers), 1)

        # The manual wait never auto-resolves.
        self.assertIsNone(
            self.engine.autonomous_tick(
                self.store, WORLD_TOKEN, self.executor, now=self.now()
            )
        )
        self.step()  # OP skips the manual wait

        # Cluster budget (2): one more beat may fire, then silence holds even
        # the next night — nothing fires two nights in a row after a cluster.
        self.clock.value += 60
        self.assertIsNotNone(
            self.engine.autonomous_tick(
                self.store, WORLD_TOKEN, self.executor, now=self.now()
            )
        )
        self.clock.value += 60
        # chapter two entered; its global beat would be next
        self.assertIsNone(
            self.engine.autonomous_tick(
                self.store, WORLD_TOKEN, self.executor, now=self.now()
            )
        )
        self.clock.value += 24 * 3600  # the very next night: still silent
        self.assertIsNone(
            self.engine.autonomous_tick(
                self.store, WORLD_TOKEN, self.executor, now=self.now()
            )
        )
        self.clock.value += 17 * 3600  # past the 40h silence: beats again
        self.assertIsNotNone(
            self.engine.autonomous_tick(
                self.store, WORLD_TOKEN, self.executor, now=self.now()
            )
        )

    def test_game_night_and_real_hour_waits(self) -> None:
        document = json.loads(json.dumps(BASE_DOCUMENT))
        document["chapters"][0]["beats"] = [
            {"type": "wait", "game_nights": 2},
            {"type": "global", "line": "Geceler sayıldı.", "any_time": True},
            {"type": "wait", "real_hours": 2},
            {"type": "global", "line": "Saatler doldu.", "any_time": True},
        ]
        engine = CampaignEngine(
            load_campaign(write_campaign(self.root, document))
        )
        engine.start(self.store, WORLD_TOKEN, now=self.now())
        engine.set_auto(self.store, WORLD_TOKEN, True, now=self.now())

        def tick():
            return engine.autonomous_tick(
                self.store, WORLD_TOKEN, self.executor, now=self.now()
            )

        # Two day→night edges satisfy the night wait; a long night is one.
        self.executor.night = True
        self.assertIsNone(tick())  # first observation seeds the edge detector
        self.executor.night = False
        self.assertIsNone(tick())
        self.executor.night = True
        self.assertIsNone(tick())  # edge 1 counted, wait not met
        self.executor.night = False
        self.assertIsNone(tick())
        self.executor.night = True
        self.assertIsNotNone(tick())  # edge 2: wait satisfied
        self.assertIsNotNone(tick())  # any_time global fires even at night
        self.assertEqual(self.executor.globals, ["Geceler sayıldı."])

        # Real-hours wait: held until the clock passes, then the beat fires
        # once the lone-beat pacing gap (12h) has also elapsed.
        self.assertIsNone(tick())
        self.clock.value += 13 * 3600
        self.assertIsNotNone(tick())  # wait satisfied
        self.clock.value += 60
        self.assertIsNotNone(tick())
        self.assertEqual(
            self.executor.globals, ["Geceler sayıldı.", "Saatler doldu."]
        )

    def test_goto_and_reset(self) -> None:
        self.engine.start(self.store, WORLD_TOKEN, now=self.now())
        jumped = self.engine.goto(self.store, WORLD_TOKEN, "two", now=self.now())
        self.assertTrue(jumped.ok)
        self.assertEqual(self.store.campaign_state(WORLD_TOKEN).phase, "servants")
        missing = self.engine.goto(self.store, WORLD_TOKEN, "9", now=self.now())
        self.assertFalse(missing.ok)
        reset = self.engine.reset(self.store, WORLD_TOKEN, now=self.now())
        self.assertTrue(reset.ok)
        self.assertEqual(self.store.campaign_state(WORLD_TOKEN).phase, "dormant")
        self.assertEqual(self.engine.progress(self.store, WORLD_TOKEN).chapter, 0)


class PointerClampTest(unittest.TestCase):
    """H1: a persisted pointer must survive a shortened/edited campaign file
    without ever throwing inside the daemon."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.clock = FakeClock()
        self.store = DirectorStore(
            self.root / "heraldor.sqlite3", clock=self.clock
        )
        self.addCleanup(self.store.close)
        self.executor = FakeExecutor()
        for name in ("Alice", "Bob"):
            self.store.observe_presence(
                WORLD_TOKEN, name, now=self.clock.value - 24 * 3600
            )

    def test_stale_pointer_after_shorter_campaign_reload(self) -> None:
        # Season progress sits at chapter 1 beat 6 of a 6-beat chapter...
        long_document = json.loads(json.dumps(BASE_DOCUMENT))
        long_document["chapters"][0]["beats"] = [
            {"type": "whisper", "pool": "generic", "target": "random"}
        ] * 6
        long_engine = CampaignEngine(
            load_campaign(write_campaign(self.root, long_document))
        )
        long_engine.start(self.store, WORLD_TOKEN, now=self.clock.value)
        for _ in range(5):
            outcome = long_engine.execute_current_beat(
                self.store, WORLD_TOKEN, self.executor,
                operator="Mizar__107", rehearsal=False, manual=True,
                now=self.clock.value,
            )
            self.assertTrue(outcome.ok)
        self.assertEqual(
            long_engine.progress(self.store, WORLD_TOKEN).beat, 5
        )

        # ...then the owner trims chapter 1 to 2 beats and restarts.
        short_document = json.loads(json.dumps(BASE_DOCUMENT))
        short_document["chapters"][0]["beats"] = [
            {"type": "whisper", "pool": "generic", "target": "random"},
            {"type": "global", "line": "kısaldı.", "any_time": True},
        ]
        short_engine = CampaignEngine(
            load_campaign(write_campaign(self.root, short_document))
        )

        # Every read path clamps to the last valid beat instead of raising.
        progress = short_engine.progress(self.store, WORLD_TOKEN)
        self.assertEqual((progress.chapter, progress.beat), (1, 1))
        status = short_engine.status_text(
            self.store, WORLD_TOKEN, now=self.clock.value
        )
        self.assertIn("beat 2/2", status)
        self.assertIsNone(
            short_engine.autonomous_tick(
                self.store, WORLD_TOKEN, self.executor, now=self.clock.value
            )
        )  # auto is off; the point is it returns instead of raising
        # The clamped position may collide with a season-1 event id once;
        # the attempt salt self-heals it on the next step — never a crash.
        outcome = short_engine.execute_current_beat(
            self.store, WORLD_TOKEN, self.executor,
            operator="Mizar__107", rehearsal=False, manual=True,
            now=self.clock.value,
        )
        if not outcome.ok:
            self.assertIn("already recorded", outcome.message)
            outcome = short_engine.execute_current_beat(
                self.store, WORLD_TOKEN, self.executor,
                operator="Mizar__107", rehearsal=False, manual=True,
                now=self.clock.value,
            )
        self.assertTrue(outcome.ok, outcome.message)
        self.assertEqual(self.executor.globals, ["kısaldı."])

    def test_pointer_beyond_all_chapters_clamps_to_finished(self) -> None:
        engine = CampaignEngine(
            load_campaign(write_campaign(self.root, BASE_DOCUMENT))
        )
        self.store.save_campaign_progress(
            WORLD_TOKEN,
            json.dumps({"chapter": 9, "beat": 4, "auto": True}),
            now=self.clock.value,
        )
        progress = engine.progress(self.store, WORLD_TOKEN)
        self.assertTrue(engine.finished(progress))
        status = engine.status_text(self.store, WORLD_TOKEN, now=self.clock.value)
        self.assertIn("finished", status)
        outcome = engine.execute_current_beat(
            self.store, WORLD_TOKEN, self.executor,
            operator="Mizar__107", rehearsal=False, manual=True,
            now=self.clock.value,
        )
        self.assertFalse(outcome.ok)
        self.assertIn("finished", outcome.message)


class TargetResolutionTest(unittest.TestCase):
    """M3 last-victim fallback and the M1 tenure gate in campaign targeting."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.clock = FakeClock()
        self.store = DirectorStore(
            self.root / "heraldor.sqlite3", clock=self.clock
        )
        self.addCleanup(self.store.close)
        document = json.loads(json.dumps(BASE_DOCUMENT))
        document["chapters"][0]["beats"] = [
            {"type": "scene", "profile": "echo_01", "target": "random"},
            {"type": "scene", "profile": "peripheral_01", "target": "last_victim"},
        ]
        self.engine = CampaignEngine(
            load_campaign(write_campaign(self.root, document))
        )
        self.executor = FakeExecutor(online=("Alice", "Bob"))
        for name in ("Alice", "Bob"):
            self.store.observe_presence(
                WORLD_TOKEN, name, now=self.clock.value - 24 * 3600
            )

    def step(self, *, manual=True):
        return self.engine.execute_current_beat(
            self.store, WORLD_TOKEN, self.executor,
            operator="Mizar__107", rehearsal=False, manual=manual,
            now=self.clock.value,
        )

    def test_offline_last_victim_falls_back_to_random_and_is_audited(self) -> None:
        self.engine.start(self.store, WORLD_TOKEN, now=self.clock.value)
        first = self.step()
        self.assertTrue(first.ok)
        victim = self.executor.scenes[0][0]

        # The victim leaves forever; the beat retargets instead of stalling.
        others = [n for n in ("Alice", "Bob") if n != victim]
        self.executor.online = others
        second = self.step()
        self.assertTrue(second.ok)
        self.assertEqual(self.executor.scenes[1][0], others[0])
        row = self.store.connection.execute(
            "SELECT payload_json FROM events WHERE kind = 'campaign_scene'"
            " ORDER BY created_at DESC, rowid DESC LIMIT 1"
        ).fetchone()
        payload = json.loads(str(row["payload_json"]))
        self.assertEqual(payload["target_fallback"], "last_victim_offline")

    def test_fallback_holds_when_nobody_is_eligible(self) -> None:
        self.engine.start(self.store, WORLD_TOKEN, now=self.clock.value)
        self.assertTrue(self.step().ok)
        victim = self.executor.scenes[0][0]
        other = "Alice" if victim != "Alice" else "Bob"

        # Autonomous mode: the only online fallback candidate lacks tenure.
        self.engine.set_auto(self.store, WORLD_TOKEN, True, now=self.clock.value)
        stranger = "Newcomer1"
        self.store.observe_presence(WORLD_TOKEN, stranger, now=self.clock.value)
        self.executor.online = [stranger]
        held = self.step(manual=False)
        self.assertFalse(held.ok)
        self.assertIn("not ready", held.message)
        # The pointer did not move: existing wait-until-ready semantics.
        self.assertEqual(self.engine.progress(self.store, WORLD_TOKEN).beat, 1)
        # A tenured player coming online un-sticks the same beat.
        self.executor.online = [other]
        self.assertTrue(self.step(manual=False).ok)

    def test_autonomous_random_respects_tenure_and_manual_bypasses(self) -> None:
        self.engine.start(self.store, WORLD_TOKEN, now=self.clock.value)
        stranger = "Newcomer1"
        self.store.observe_presence(WORLD_TOKEN, stranger, now=self.clock.value)
        self.executor.online = [stranger]

        held = self.step(manual=False)
        self.assertFalse(held.ok)
        self.assertIn("tenure", held.message)
        self.assertEqual(self.executor.scenes, [])

        # The OP knows best: a manual step targets the newcomer anyway.
        bypass = self.step(manual=True)
        self.assertTrue(bypass.ok)
        self.assertEqual(self.executor.scenes[0][0], stranger)


class PacingUpgradesTest(unittest.TestCase):
    """Item 11: silence jitter, per-chapter pacing overrides, day_only."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.clock = FakeClock()
        self.store = DirectorStore(
            self.root / "heraldor.sqlite3", clock=self.clock
        )
        self.addCleanup(self.store.close)
        for name in ("Alice", "Bob"):
            self.store.observe_presence(
                WORLD_TOKEN, name, now=self.clock.value - 24 * 3600
            )

    def test_silence_range_loads_and_jitter_stays_in_bounds(self) -> None:
        document = json.loads(json.dumps(BASE_DOCUMENT))
        document["pacing"]["silence_hours"] = [32, 70]
        campaign = load_campaign(write_campaign(self.root, document))
        pacing = campaign.pacing
        self.assertEqual(pacing.silence_seconds, 32 * 3600)
        self.assertEqual(pacing.silence_seconds_max, 70 * 3600)
        seen = set()
        for last_at in range(1_780_000_000, 1_780_000_040):
            value = pacing.required_silence_seconds(f"{WORLD_TOKEN}:{last_at}")
            self.assertGreaterEqual(value, 32 * 3600)
            self.assertLessEqual(value, 70 * 3600)
            # Deterministic per gap: the same seed always answers the same.
            self.assertEqual(
                value,
                pacing.required_silence_seconds(f"{WORLD_TOKEN}:{last_at}"),
            )
            seen.add(value)
        self.assertGreater(len(seen), 1, "jitter never varied across gaps")

    def test_scalar_silence_still_accepted_and_bad_ranges_fail(self) -> None:
        document = json.loads(json.dumps(BASE_DOCUMENT))
        document["pacing"]["silence_hours"] = 46
        campaign = load_campaign(write_campaign(self.root, document))
        self.assertEqual(campaign.pacing.silence_seconds, 46 * 3600)
        self.assertEqual(campaign.pacing.silence_seconds_max, 46 * 3600)
        for bad in ([70, 32], [1], [1, 2, 3], ["a", "b"], [0, 40], [40, 400]):
            with self.subTest(bad=bad), self.assertRaises(CampaignError):
                document = json.loads(json.dumps(BASE_DOCUMENT))
                document["pacing"]["silence_hours"] = bad
                load_campaign(write_campaign(self.root, document))

    def test_chapter_pacing_override_merges_over_global(self) -> None:
        document = json.loads(json.dumps(BASE_DOCUMENT))
        document["pacing"]["silence_hours"] = 40
        document["chapters"][0]["pacing"] = {"silence_hours": [2, 2]}
        campaign = load_campaign(write_campaign(self.root, document))
        override = campaign.chapters[0].pacing
        self.assertIsNotNone(override)
        self.assertEqual(override.silence_seconds, 2 * 3600)
        # Unset knobs inherit the campaign values.
        self.assertEqual(override.cluster_beats, campaign.pacing.cluster_beats)
        self.assertIsNone(campaign.chapters[1].pacing)

        engine = CampaignEngine(campaign)
        from dataclasses import replace as dc_replace

        progress_ch1 = engine.progress(self.store, WORLD_TOKEN)
        progress_ch1 = dc_replace(progress_ch1, chapter=1)
        self.assertEqual(
            engine._effective_pacing(progress_ch1).silence_seconds, 2 * 3600
        )
        progress_ch2 = dc_replace(progress_ch1, chapter=2)
        self.assertEqual(
            engine._effective_pacing(progress_ch2).silence_seconds, 40 * 3600
        )

    def test_chapter_override_accelerates_the_autonomous_gate(self) -> None:
        # Chapter silence 2h beats the 40h global: after a 2-beat cluster the
        # next beat fires once ~2h (plus the 12h lone-beat floor cap logic)
        # has passed, not 40h. Cluster of 2 => full chapter silence applies.
        document = json.loads(json.dumps(BASE_DOCUMENT))
        document["pacing"]["silence_hours"] = 40
        document["chapters"][0]["pacing"] = {
            "cluster_beats": 2,
            "silence_hours": [2, 2],
        }
        document["chapters"][0]["beats"] = [
            {"type": "global", "line": "bir.", "any_time": True},
            {"type": "global", "line": "iki.", "any_time": True},
            {"type": "global", "line": "üç.", "any_time": True},
        ]
        engine = CampaignEngine(load_campaign(write_campaign(self.root, document)))
        executor = FakeExecutor()
        engine.start(self.store, WORLD_TOKEN, now=self.clock.value)
        engine.set_auto(self.store, WORLD_TOKEN, True, now=self.clock.value)

        def tick():
            return engine.autonomous_tick(
                self.store, WORLD_TOKEN, executor, now=self.clock.value
            )

        self.assertIsNotNone(tick())
        self.clock.value += 60
        self.assertIsNotNone(tick())  # cluster budget 2 reached
        self.clock.value += 60
        self.assertIsNone(tick())
        self.clock.value += 3 * 3600  # past the chapter's 2h silence
        self.assertIsNotNone(tick())
        self.assertEqual(executor.globals, ["bir.", "iki.", "üç."])

    def test_day_only_beat_waits_for_daylight(self) -> None:
        document = json.loads(json.dumps(BASE_DOCUMENT))
        document["chapters"][0]["beats"] = [
            {"type": "scene", "profile": "echo_01", "target": "random",
             "day_only": True},
        ]
        engine = CampaignEngine(load_campaign(write_campaign(self.root, document)))
        executor = FakeExecutor(night=True)
        engine.start(self.store, WORLD_TOKEN, now=self.clock.value)
        engine.set_auto(self.store, WORLD_TOKEN, True, now=self.clock.value)
        self.assertIsNone(
            engine.autonomous_tick(
                self.store, WORLD_TOKEN, executor, now=self.clock.value
            )
        )
        self.assertEqual(executor.scenes, [])
        executor.night = False
        self.assertIsNotNone(
            engine.autonomous_tick(
                self.store, WORLD_TOKEN, executor, now=self.clock.value
            )
        )
        self.assertEqual(len(executor.scenes), 1)

    def test_day_only_and_any_time_are_mutually_exclusive(self) -> None:
        document = json.loads(json.dumps(BASE_DOCUMENT))
        document["chapters"][0]["beats"].append(
            {"type": "scene", "profile": "echo_01", "target": "random",
             "any_time": True, "day_only": True}
        )
        with self.assertRaises(CampaignError):
            load_campaign(write_campaign(self.root, document))


class GlobalStyleTest(unittest.TestCase):
    """Item 12: the attribution ladder for global broadcasts."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.clock = FakeClock()
        self.store = DirectorStore(
            self.root / "heraldor.sqlite3", clock=self.clock
        )
        self.addCleanup(self.store.close)

    def build_engine(self, tier, style=None):
        document = json.loads(json.dumps(BASE_DOCUMENT))
        beat = {"type": "global", "line": "satır.", "any_time": True}
        if style is not None:
            beat["style"] = style
        document["chapters"][0]["tier"] = tier
        document["chapters"][0]["beats"] = [beat]
        return CampaignEngine(load_campaign(write_campaign(self.root, document)))

    def deliver(self, engine):
        executor = FakeExecutor()
        engine.start(self.store, WORLD_TOKEN, now=self.clock.value)
        outcome = engine.execute_current_beat(
            self.store, WORLD_TOKEN, executor,
            operator="Mizar__107", rehearsal=False, manual=True,
            now=self.clock.value,
        )
        self.assertTrue(outcome.ok)
        return executor

    def test_style_defaults_follow_the_chapter_tier(self) -> None:
        for tier, expected in (
            ("presence", "unsigned"),
            ("servants", "glitch"),
            ("manifestation", "named"),
        ):
            with self.subTest(tier=tier):
                self.store.reset_campaign(WORLD_TOKEN)
                executor = self.deliver(self.build_engine(tier))
                self.assertEqual(executor.global_styles, [expected])

    def test_explicit_style_overrides_the_tier_default_and_is_audited(self) -> None:
        executor = self.deliver(self.build_engine("presence", style="named"))
        self.assertEqual(executor.global_styles, ["named"])
        row = self.store.connection.execute(
            "SELECT payload_json FROM events WHERE kind = 'campaign_global'"
        ).fetchone()
        self.assertEqual(json.loads(str(row["payload_json"]))["style"], "named")

    def test_unknown_style_fails_closed_at_load(self) -> None:
        document = json.loads(json.dumps(BASE_DOCUMENT))
        document["chapters"][0]["beats"] = [
            {"type": "global", "line": "x.", "style": "neon"}
        ]
        with self.assertRaises(CampaignError):
            load_campaign(write_campaign(self.root, document))


class ResetGenerationTest(unittest.TestCase):
    """L4: after `story reset`, the first `story next` fires beat 1 once."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.clock = FakeClock()
        self.store = DirectorStore(
            self.root / "heraldor.sqlite3", clock=self.clock
        )
        self.addCleanup(self.store.close)
        self.engine = CampaignEngine(
            load_campaign(write_campaign(self.root, BASE_DOCUMENT))
        )
        self.executor = FakeExecutor()

    def step(self):
        return self.engine.execute_current_beat(
            self.store, WORLD_TOKEN, self.executor,
            operator="Mizar__107", rehearsal=False, manual=True,
            now=self.clock.value,
        )

    def test_reset_generation_desalts_beat_ids(self) -> None:
        self.engine.start(self.store, WORLD_TOKEN, now=self.clock.value)
        self.assertTrue(self.step().ok)  # season 1 beat 1 delivered

        self.engine.reset(self.store, WORLD_TOKEN, now=self.clock.value)
        self.engine.start(self.store, WORLD_TOKEN, now=self.clock.value)
        outcome = self.step()
        self.assertTrue(outcome.ok, outcome.message)
        self.assertNotIn("already recorded", outcome.message)
        # Both seasons' rows exist under distinct at-most-once ids.
        rows = self.store.connection.execute(
            "SELECT COUNT(*) FROM events WHERE kind = 'campaign_whisper'"
            " AND status = 'delivered'"
        ).fetchone()[0]
        self.assertEqual(rows, 2)


class ServantRetirementTest(unittest.TestCase):
    """Item 16 / HD-7a: live servant waves refuse after the finale."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.clock = FakeClock()
        self.store = DirectorStore(
            self.root / "heraldor.sqlite3", clock=self.clock
        )
        self.addCleanup(self.store.close)
        document = json.loads(json.dumps(BASE_DOCUMENT))
        document["chapters"][1]["beats"] = [
            {"type": "servant_wave", "count": 1, "target": "random"},
            {"type": "global", "line": "son.", "any_time": True},
        ]
        self.engine = CampaignEngine(
            load_campaign(write_campaign(self.root, document))
        )
        self.executor = FakeExecutor()
        for name in ("Alice", "Bob"):
            self.store.observe_presence(
                WORLD_TOKEN, name, now=self.clock.value - 24 * 3600
            )

    def step(self, *, rehearsal=False):
        return self.engine.execute_current_beat(
            self.store, WORLD_TOKEN, self.executor,
            operator="Mizar__107", rehearsal=rehearsal, manual=True,
            now=self.clock.value,
        )

    def finish_campaign(self) -> None:
        self.engine.start(self.store, WORLD_TOKEN, now=self.clock.value)
        while not self.engine.finished(
            self.engine.progress(self.store, WORLD_TOKEN)
        ):
            outcome = self.step()
            self.assertTrue(outcome.ok, outcome.message)

    def test_live_servant_wave_refuses_after_the_finale(self) -> None:
        self.finish_campaign()
        self.assertTrue(self.store.campaign_completed(WORLD_TOKEN))
        served_before = len(self.executor.servants)

        # An OP replay via goto lands on the servant beat: live refuses...
        self.engine.goto(self.store, WORLD_TOKEN, "2", now=self.clock.value)
        refused = self.step()
        self.assertFalse(refused.ok)
        self.assertIn("retired", refused.message)
        self.assertEqual(len(self.executor.servants), served_before)
        # ...while rehearsal remains legal (no story writes).
        rehearsed = self.step(rehearsal=True)
        self.assertTrue(rehearsed.ok)
        self.assertEqual(self.executor.servants[-1][1], False)

    def test_story_reset_starts_a_sanctioned_new_season(self) -> None:
        self.finish_campaign()
        self.engine.reset(self.store, WORLD_TOKEN, now=self.clock.value)
        self.assertFalse(self.store.campaign_completed(WORLD_TOKEN))
        self.engine.start(self.store, WORLD_TOKEN, now=self.clock.value)
        self.engine.goto(self.store, WORLD_TOKEN, "2", now=self.clock.value)
        outcome = self.step()
        self.assertTrue(outcome.ok, outcome.message)
        self.assertEqual(self.executor.servants[-1][1], True)


class ShippedCampaignContentTest(unittest.TestCase):
    """Items 12–13: the shipped file carries the accepted content edits."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.campaign = load_campaign(SHIPPED_CAMPAIGN)
        cls.raw = SHIPPED_CAMPAIGN.read_text(encoding="utf-8")

    def test_first_contact_wait_is_52_real_hours(self) -> None:
        chapter_one = self.campaign.chapters[0]
        self.assertEqual(chapter_one.beats[0].type, "whisper")
        second = chapter_one.beats[1]
        self.assertEqual(second.type, "wait")
        self.assertEqual(second.wait_real_hours, 52.0)

    def test_prophecy_pair_opens_chapter_three(self) -> None:
        chapter_three = self.campaign.chapters[2]
        prophecy, night_wait, passage = chapter_three.beats[0:3]
        self.assertEqual(prophecy.type, "whisper")
        self.assertEqual(
            prophecy.line, "yakında biriniz bir kapı görecek. inanmayın ona."
        )
        self.assertEqual(prophecy.target, "random")
        self.assertEqual(night_wait.wait_game_nights, 1)
        self.assertEqual(passage.profile, "false_passage_01")
        self.assertEqual(passage.target, "random")

    def test_chapter_three_has_exactly_one_day_only_daylight_beat(self) -> None:
        day_beats = [
            (index, beat)
            for chapter in self.campaign.chapters
            for index, beat in enumerate(chapter.beats)
            if beat.day_only
        ]
        self.assertEqual(len(day_beats), 1)
        _, beat = day_beats[0]
        self.assertEqual(beat.profile, "whisper_steps_01")
        self.assertEqual(beat.target, "last_victim")
        self.assertIn(beat, self.campaign.chapters[2].beats)

    def test_finale_order_visitation_before_stage_four_and_ends_in_silence(self) -> None:
        finale = self.campaign.chapters[-1].beats
        kinds = [(beat.type, beat.profile) for beat in finale]
        visitation_at = kinds.index(("scene", "visitation_01"))
        last_colossus_at = max(
            index for index, item in enumerate(kinds)
            if item == ("scene", "colossus_01")
        )
        witness_at = kinds.index(("scene", "witness_01"))
        self.assertLess(witness_at, visitation_at)
        self.assertLess(visitation_at, last_colossus_at)
        # No discord beat anywhere in the finale: the campaign ends in
        # silence after one named global (HD-6a).
        self.assertNotIn("discord", [beat.type for beat in finale])
        self.assertEqual(finale[-1].type, "global")
        self.assertEqual(finale[-1].style, "named")
        self.assertEqual(finale[last_colossus_at - 1].wait_game_nights, 1)

    def test_attribution_ladder_styles_in_shipped_file(self) -> None:
        styles = {
            (chapter.id, beat.line): beat.style
            for chapter in self.campaign.chapters
            for beat in chapter.beats
            if beat.type == "global"
        }
        self.assertEqual(
            styles[("izleniyorsun", "ışıklarınızı saydım. bir eksik.")],
            "unsigned",
        )
        self.assertEqual(styles[("hizmetkarlar", "yalnız gelmedim.")], "glitch")
        self.assertEqual(
            styles[("tezahur", "Gördü. Artık hepiniz görüldünüz.")], "named"
        )

    def test_accelerando_chapter_pacing_shrinks_monotonically(self) -> None:
        silences = []
        for chapter in self.campaign.chapters:
            self.assertIsNotNone(chapter.pacing, chapter.id)
            self.assertLessEqual(
                chapter.pacing.silence_seconds, chapter.pacing.silence_seconds_max
            )
            silences.append(
                (chapter.pacing.silence_seconds, chapter.pacing.silence_seconds_max)
            )
        for earlier, later in zip(silences, silences[1:]):
            self.assertGreater(earlier[0], later[0])
            self.assertGreater(earlier[1], later[1])
        # ch1 slowest around 64h, ch5 fastest around 18h (review guidance).
        self.assertGreaterEqual(silences[0][1], 64 * 3600)
        self.assertLessEqual(silences[-1][0], 18 * 3600)

    def test_dossier_has_six_lines_per_nick_and_never_list_comment(self) -> None:
        for nick, lines in self.campaign.dossier.items():
            self.assertEqual(len(lines), 6, nick)
            for line in lines:
                self.assertNotIn("!", line)
        for expected in (
            "külleri saklıyorum. hepsini.",
            "seni geçtim. fark etmedin.",
            "koltuğunu geri ittim. sığmıyorum.",
            "köyde bir kapı fazla. say.",
            "iniş yerini ben seçiyorum.",
        ):
            found = any(
                expected in lines for lines in self.campaign.dossier.values()
            )
            self.assertTrue(found, expected)
        # The NEVER list rides at the top of pools as authored law.
        self.assertIn("ASLA listesi", self.raw)
        for fragment in ("oyun-mekaniği", "doğrulanabilir sayı", "kendi adını",
                         "cevap vermez", "gerçek dünya verisi"):
            self.assertIn(fragment, self.raw)


class ShippedFinaleLadderTest(unittest.TestCase):
    """End-to-end walk of the shipped chapter 5 over the real dispatch path:
    the colossus must climb stages 0..4 with the visitation before stage 4."""

    def test_colossus_stage_ladder_and_visitation_order(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        clock = FakeClock()
        store = DirectorStore(Path(temp.name) / "heraldor.sqlite3", clock=clock)
        self.addCleanup(store.close)
        engine = CampaignEngine(load_campaign(SHIPPED_CAMPAIGN))
        executor = heraldor_service.RconCampaignExecutor(store, WORLD_TOKEN)
        commands: list[str] = []

        def fake_rcon(command):
            commands.append(command)
            if command == "list":
                return "There are 1 of a max of 20 players online: Alice"
            if command.startswith("zapegscene"):
                return "scene dispatched event=x"
            return "ok"

        engine.goto(store, WORLD_TOKEN, "5", now=clock.value)
        with (
            patch.object(heraldor_service, "rcon", side_effect=fake_rcon),
            patch.object(
                heraldor_service, "rcon_many",
                side_effect=lambda batch: [fake_rcon(c) for c in batch],
            ),
        ):
            for _ in range(64):
                progress = engine.progress(store, WORLD_TOKEN)
                if engine.finished(progress):
                    break
                clock.value += 60
                outcome = engine.execute_current_beat(
                    store, WORLD_TOKEN, executor,
                    operator="Mizar__107", rehearsal=False, manual=True,
                    now=clock.value,
                )
                self.assertTrue(outcome.ok, outcome.message)
        self.assertTrue(
            engine.finished(engine.progress(store, WORLD_TOKEN))
        )

        colossus_stages = [
            int(command.split(" stage ")[1].split()[0])
            for command in commands
            if command.startswith("zapegscene trigger") and " colossus_01 " in command
        ]
        self.assertEqual(colossus_stages, [0, 1, 2, 3, 4])
        scene_order = [
            command.split()[4]
            for command in commands
            if command.startswith("zapegscene trigger")
        ]
        self.assertLess(
            scene_order.index("visitation_01"),
            len(scene_order) - 1 - scene_order[::-1].index("colossus_01"),
        )
        # The finale set the one-way completion flag: servants are retired.
        self.assertTrue(store.campaign_completed(WORLD_TOKEN))


class StoryControlBridgeTest(unittest.TestCase):
    """`/zapeg-lore story next` through the real control path, with RCON and
    the campaign runtime faked at the edges."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.clock = FakeClock()
        self.store = DirectorStore(
            self.root / "heraldor.sqlite3", clock=self.clock
        )
        self.addCleanup(self.store.close)
        campaign_path = write_campaign(self.root, BASE_DOCUMENT)
        runtime = heraldor_service.CampaignRuntime(campaign_path)
        self.assertIsNotNone(runtime.engine)
        patcher = patch.object(heraldor_service, "_CAMPAIGN", runtime)
        patcher.start()
        self.addCleanup(patcher.stop)

    def control(self, argument, target="-", nonce=1):
        expires_at = self.clock.value + 90
        return parse_control_request(
            f"zhctl1:{WORLD_TOKEN}:{nonce:020x}:{expires_at}:"
            f"story:{argument}:{target}:Mizar__107"
        )

    def process(self, request):
        return heraldor_service.process_control_request(
            self.store, request, observed_world_token=WORLD_TOKEN
        )

    def test_story_next_delivers_a_whisper_beat_over_rcon(self) -> None:
        self.process(self.control("start", nonce=1))
        commands: list[str] = []

        def fake_rcon(command):
            commands.append(command)
            if command == "list":
                return "There are 2 of a max of 20 players online: Alice, Bob"
            return "ok"

        with (
            patch.object(heraldor_service, "rcon", side_effect=fake_rcon),
            patch.object(
                heraldor_service, "rcon_many",
                side_effect=lambda batch: [fake_rcon(c) for c in batch],
            ),
        ):
            outcome = self.process(self.control("next", nonce=2))
        self.assertEqual(outcome.status, "delivered")
        tellraws = [c for c in commands if c.startswith("tellraw Alice")]
        self.assertTrue(tellraws, f"no whisper tellraw in {commands}")
        self.assertIn("alice özel satırı.", tellraws[0])

        # A replayed token acknowledges without executing again.
        with patch.object(heraldor_service, "rcon") as runtime:
            replay = self.process(self.control("next", nonce=2))
        self.assertEqual(replay.status, "delivered")
        runtime.assert_not_called()

    def test_story_rehearse_previews_to_the_operator_only(self) -> None:
        self.process(self.control("start", nonce=3))
        commands: list[str] = []

        def fake_rcon(command):
            commands.append(command)
            if command == "list":
                return "There are 2 of a max of 20 players online: Alice, Bob"
            return "ok"

        with (
            patch.object(heraldor_service, "rcon", side_effect=fake_rcon),
            patch.object(
                heraldor_service, "rcon_many",
                side_effect=lambda batch: [fake_rcon(c) for c in batch],
            ),
        ):
            outcome = self.process(self.control("rehearse", nonce=4))
        self.assertEqual(outcome.status, "delivered")
        self.assertTrue(
            any(c.startswith("tellraw Mizar__107") for c in commands),
            f"operator preview missing in {commands}",
        )
        self.assertFalse(any(c.startswith("tellraw Alice") for c in commands))
        # Zero campaign writes: the pointer still sits on beat 0.
        runtime = heraldor_service.campaign_runtime()
        self.assertEqual(
            runtime.engine.progress(self.store, WORLD_TOKEN).beat, 0
        )

    def test_invalid_story_tokens_fail_closed(self) -> None:
        for token in (
            f"zhctl1:{WORLD_TOKEN}:{9:020x}:1999999999:story:destroy:-:Mizar__107",
            f"zhctl1:{WORLD_TOKEN}:{10:020x}:1999999999:story:start:Alice:Mizar__107",
            f"zhctl1:{WORLD_TOKEN}:{11:020x}:1999999999:story:goto:-:Mizar__107",
        ):
            with self.subTest(token=token), self.assertRaises(ValueError):
                parse_control_request(token)


if __name__ == "__main__":
    unittest.main()
