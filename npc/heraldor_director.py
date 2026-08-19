#!/usr/bin/env python3
"""Persistent pacing and story state for the Heraldor presence engine."""

from __future__ import annotations

import json
import math
import os
import random
import re
import shutil
import sqlite3
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


SCHEMA_VERSION = 2
SERVANT_SOURCE_PREFIX = "minecraft:scoreboard:zapeg_hsvc:#total:v1:world:"
SERVANT_STORY_FLAG_PREFIX = "heraldor_servants_defeated_3_v1_world_"
SERVANT_STORY_EVENT_PREFIX = "story:heraldor-servants:defeated:3:v1:world:"
SERVANT_AUDIO_CLIP_ID = "servants_after_three_v1"
SERVANT_THRESHOLD = 3
SERVANT_MAX_SCORE = 1_000_000
SERVANT_MAX_INGEST_JUMP = 100
DEATH_SOURCE_TEMPLATE = "minecraft:scoreboard:zh_death:{subject}:v1:world:{world}"
DEATH_MAX_INGEST_JUMP = 5
AFTERMATH_META_PREFIX = "aftermath:"
AFTERMATH_PROFILE = "footsteps_01"
# The far colossus: a render-only silhouette escalated one stage per live
# operator trigger, persisted per target per world. Rehearsals never advance
# it, and the autonomous scheduler must never plan it on its own.
COLOSSUS_PROFILE = "colossus_01"
COLOSSUS_MAX_STAGE = 4
COLOSSUS_META_PREFIX = "colossus:"
VISITATION_PROFILE = "visitation_01"
# Operator-only profiles: the scheduler never plans these on its own; they
# exist for deliberate OP/Director beats (rehearsal stays available).
OPERATOR_ONLY_PROFILES = frozenset({COLOSSUS_PROFILE, VISITATION_PROFILE})
# Manual Discord whispers share one world-tokened cooldown marker so the
# in-game bridge action can never spam the channel.
MANUAL_DISCORD_META_PREFIX = "discord_manual:"
MANUAL_DISCORD_MIN_GAP_SECONDS = 10 * 60
AUDIO_SINK = "discord_voice"
AUDIO_EVENT_TYPE = "heraldor.audio.requested"
AUDIO_LIVE_TTL_SECONDS = 5 * 60
AUDIO_REHEARSAL_TTL_SECONDS = 2 * 60
AUDIO_LIVE_GAP_SECONDS = 6 * 60 * 60
AUDIO_REHEARSAL_GAP_SECONDS = 30
ALLOWED_AUDIO_CLIPS = frozenset({SERVANT_AUDIO_CLIP_ID})
AMBIENT_KINDS = frozenset({"whisper", "global", "discord", "shadows"})
CONTROL_TOKEN_VERSION = "zhctl1"
CONTROL_TOKEN_MAX_FUTURE_SECONDS = 2 * 60
CONTROL_PHASES = ("dormant", "presence", "servants", "manifestation")
CONTROL_START_PHASES = frozenset(CONTROL_PHASES[1:])
CONTROL_SCENE_PROFILE_PHASES = {
    "echo_01": "presence",
    "threshold_01": "presence",
    "peripheral_01": "presence",
    "sky_mark_01": "presence",
    "whisper_steps_01": "presence",
    "motion_echo_01": "servants",
    "footsteps_01": "servants",
    "near_miss_01": "servants",
    "false_passage_01": "servants",
    "light_fault_01": "manifestation",
    "chroma_break_01": "manifestation",
    "colossus_01": "manifestation",
    "visitation_01": "manifestation",
}
# Mirrors SceneProfile.defaultTtlTicks() in zapeg-runtime; the Director scales
# these by campaign phase and passes the result as the optional ttl_ticks
# argument of /zapegscene trigger (server clamps to MAX_TTL_TICKS).
SCENE_PROFILE_DEFAULT_TTL_TICKS = {
    "echo_01": 200,
    "threshold_01": 160,
    "motion_echo_01": 220,
    "light_fault_01": 140,
    "peripheral_01": 140,
    "footsteps_01": 160,
    "sky_mark_01": 240,
    "false_passage_01": 300,
    "chroma_break_01": 120,
    "near_miss_01": 110,
    "whisper_steps_01": 180,
    "colossus_01": 320,
    "visitation_01": 70,
}
# Profiles whose runtime placement walks the ground around the target; only
# these can take a stalking-memory or grave-site anchor hint.
STALK_HINT_PROFILES = frozenset(
    {
        "echo_01",
        "threshold_01",
        "peripheral_01",
        "footsteps_01",
        "false_passage_01",
    }
)
SCENE_TTL_PHASE_SCALE = {
    "dormant": 1.0,
    "presence": 1.0,
    "servants": 1.15,
    "manifestation": 1.35,
}
SCENE_MAX_TTL_TICKS = 1200
# Stalking memory privacy boundary: positions are collapsed into 32-block
# cells, kept per world and per player, capped per player, and purged the
# moment a different world token is observed. Nothing finer than a cell ever
# leaves the daemon, and nothing is ever sent back to the world.
STALK_CELL_SIZE = 32
STALK_MAX_CELLS_PER_SUBJECT = 48
PLAYER_NAME_RE = re.compile(r"^[A-Za-z0-9_]{1,16}$")
CONTROL_ACTIONS = frozenset(
    {
        "status",
        "pause",
        "resume",
        "phase_start",
        "phase_advance",
        "scene_rehearse",
        "scene_trigger",
        "cancel",
        "colossus_reset",
        "discord_post",
        "voice_rehearse",
    }
)
CONTROL_EVENT_NAMESPACE = uuid.UUID("da548502-11dd-5b05-886a-650c4b74596c")
CONTROL_TOKEN_RE = re.compile(
    r"^zhctl1:(?P<world>[1-9]\d{0,9}):(?P<nonce>[0-9a-f]{16,32}):"
    r"(?P<expires>[1-9]\d{9}):(?P<action>[a-z_]+):"
    r"(?P<argument>[a-z0-9_-]+):(?P<target>[A-Za-z0-9_-]+):"
    r"(?P<operator>[A-Za-z0-9_]{1,16})$"
)
CONTROL_OUTPUT_TOKEN_RE = re.compile(
    r'^[^"\r\n]*"(zhctl1(?::[A-Za-z0-9_-]+){7})"\s*$'
)


@dataclass(frozen=True)
class DirectorPolicy:
    """Conservative defaults: a missed beat is safer than a clustered one."""

    ambient_gap_seconds: int = 6 * 60 * 60
    targeted_gap_seconds: int = 24 * 60 * 60
    ambient_window_seconds: int = 24 * 60 * 60
    ambient_budget: int = 2
    major_quiet_seconds: int = 24 * 60 * 60
    discord_cooldown_seconds: int = 7 * 24 * 60 * 60
    shadows_cooldown_seconds: int = 7 * 24 * 60 * 60
    # Scheduled beats: scenes cluster into one "night of activity". Each
    # delivered scene keeps the night alive for cluster_open_seconds; once
    # the night ends (or its budget is spent), at least
    # cluster_silence_seconds of silence must pass before a new one opens.
    cluster_open_seconds: int = 45 * 60
    cluster_silence_seconds: int = 2 * 24 * 60 * 60
    cluster_scene_budget: int = 5
    cluster_subject_gap_seconds: int = 20 * 60
    # Per scheduler tick: a long-quiet world rarely opens a night; an open
    # night beats more freely but still waits between scenes.
    scheduler_open_probability: float = 0.05
    scheduler_beat_probability: float = 0.20
    # Grave echoes never answer a fresh death and stay rare even then.
    grave_echo_min_age_seconds: int = 20 * 60
    grave_echo_probability: float = 0.5


@dataclass(frozen=True)
class Reservation:
    event_id: str
    kind: str
    subject: str | None
    rehearsal: bool


@dataclass(frozen=True)
class ServantIngestResult:
    previous_high_water: int
    high_water: int
    victory_event_ids: tuple[str, ...]
    story_event_id: str | None
    regression: bool = False
    quarantined: bool = False
    story_output_status: str | None = None


@dataclass(frozen=True)
class AudioDelivery:
    event_id: str
    payload: dict[str, object]
    rehearsal: bool


@dataclass(frozen=True)
class DeathIngestResult:
    previous_high_water: int
    high_water: int
    death_event_ids: tuple[str, ...]
    regression: bool = False
    quarantined: bool = False


@dataclass(frozen=True)
class ScenePlan:
    """One scheduler-planned live scene, already reserved in the ledger."""

    event_id: str
    profile: str
    subject: str
    ttl_ticks: int
    hint: tuple[int, int] | None
    reason: str


@dataclass(frozen=True)
class ControlRequest:
    token: str
    world_token: str
    nonce: str
    expires_at: int
    action: str
    argument: str
    target: str | None
    operator: str

    @property
    def event_id(self) -> str:
        return str(uuid.uuid5(CONTROL_EVENT_NAMESPACE, self.token))


@dataclass(frozen=True)
class ControlEventRecord:
    event_id: str
    status: str
    created: bool


@dataclass(frozen=True)
class CampaignState:
    world_token: str
    phase: str = "dormant"
    paused: bool = False

    def allows_profile(self, profile: str) -> bool:
        minimum = CONTROL_SCENE_PROFILE_PHASES.get(profile)
        if minimum is None:
            return False
        return CONTROL_PHASES.index(self.phase) >= CONTROL_PHASES.index(minimum)


def compact_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def normalize_world_token(value: int | str) -> str:
    token = str(value).strip()
    if not re.fullmatch(r"[1-9]\d{0,9}", token) or int(token) > 2_000_000_000:
        raise ValueError(f"invalid Heraldor world token: {value!r}")
    return token


def scene_ttl_ticks(profile: str, phase: str) -> int:
    """Phase-scaled scene length: scenes linger longer as the campaign
    escalates, always bounded by the runtime's MAX_TTL_TICKS clamp."""

    base = SCENE_PROFILE_DEFAULT_TTL_TICKS.get(profile)
    if base is None:
        raise ValueError(f"unknown Heraldor scene profile: {profile!r}")
    scale = SCENE_TTL_PHASE_SCALE.get(phase)
    if scale is None:
        raise ValueError(f"unknown Heraldor campaign phase: {phase!r}")
    return min(SCENE_MAX_TTL_TICKS, max(1, round(base * scale)))


def parse_control_request(token: str) -> ControlRequest:
    """Parse the complete, allowlisted Minecraft-to-Director control token."""

    match = CONTROL_TOKEN_RE.fullmatch(token)
    if not match:
        raise ValueError("invalid Heraldor control token")
    values = match.groupdict()
    world_token = normalize_world_token(values["world"])
    action = values["action"]
    argument = values["argument"]
    raw_target = values["target"]
    operator = values["operator"]

    if action not in CONTROL_ACTIONS:
        raise ValueError("unsupported Heraldor control action")
    if operator != "console" and not re.fullmatch(r"[A-Za-z0-9_]{1,16}", operator):
        raise ValueError("invalid Heraldor control operator")

    no_argument_actions = {
        "status",
        "pause",
        "resume",
        "phase_advance",
        "cancel",
        "discord_post",
        "voice_rehearse",
    }
    if action in no_argument_actions:
        if argument != "-" or raw_target != "-":
            raise ValueError("unexpected Heraldor control arguments")
        target = None
    elif action == "phase_start":
        if argument not in CONTROL_START_PHASES or raw_target != "-":
            raise ValueError("invalid Heraldor campaign phase")
        target = None
    elif action == "colossus_reset":
        if argument != "-":
            raise ValueError("unexpected Heraldor colossus reset argument")
        if not re.fullmatch(r"[A-Za-z0-9_]{1,16}", raw_target):
            raise ValueError("invalid Heraldor colossus reset target")
        target = raw_target
    else:
        if argument not in CONTROL_SCENE_PROFILE_PHASES:
            raise ValueError("invalid Heraldor scene profile")
        if not re.fullmatch(r"[A-Za-z0-9_]{1,16}", raw_target):
            raise ValueError("invalid Heraldor scene target")
        target = raw_target

    return ControlRequest(
        token=token,
        world_token=world_token,
        nonce=values["nonce"],
        expires_at=int(values["expires"]),
        action=action,
        argument=argument,
        target=target,
        operator=operator,
    )


def extract_control_request_token(output: str) -> str | None:
    """Accept only one exact quoted token value after localized output text."""

    match = CONTROL_OUTPUT_TOKEN_RE.fullmatch(output)
    return match.group(1) if match else None


def servant_story_event_id(world_token: int | str) -> str:
    return SERVANT_STORY_EVENT_PREFIX + normalize_world_token(world_token)


def voice_lock_path(db_path: str | os.PathLike[str]) -> Path:
    return Path(str(db_path) + ".voice.lock")


def snapshot_lock_path(db_path: str | os.PathLike[str]) -> Path:
    return Path(str(db_path) + ".snapshot.lock")


class DirectorStateLock:
    """Cross-process advisory lock shared by the daemon and destructive admin work."""

    def __init__(
        self,
        path: str | os.PathLike[str],
        *,
        blocking: bool = False,
        purpose: str = "state",
    ) -> None:
        self.path = Path(path)
        self.blocking = blocking
        self.purpose = purpose
        self.handle = None

    def __enter__(self) -> "DirectorStateLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.handle = self.path.open("a+b")
        self.handle.seek(0, os.SEEK_END)
        if self.handle.tell() == 0:
            self.handle.write(b"\0")
            self.handle.flush()
        self.handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                mode = msvcrt.LK_LOCK if self.blocking else msvcrt.LK_NBLCK
                msvcrt.locking(self.handle.fileno(), mode, 1)
            else:
                import fcntl

                mode = fcntl.LOCK_EX
                if not self.blocking:
                    mode |= fcntl.LOCK_NB
                fcntl.flock(self.handle.fileno(), mode)
        except OSError as exc:
            self.handle.close()
            self.handle = None
            raise RuntimeError(
                f"Heraldor {self.purpose} is locked by another process"
            ) from exc
        return self

    def __exit__(self, *_args: object) -> None:
        if not self.handle:
            return
        try:
            self.handle.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(self.handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)
        finally:
            self.handle.close()
            self.handle = None


def restore_snapshot(
    db_path: str | os.PathLike[str], snapshot_path: str | os.PathLike[str]
) -> None:
    """Promote a verified online snapshot while the Director daemon is stopped."""

    database = Path(db_path)
    snapshot = Path(snapshot_path)
    with DirectorStateLock(Path(str(database) + ".lock")):
        with DirectorStateLock(voice_lock_path(database)):
            with DirectorStateLock(
                snapshot_lock_path(database), blocking=True, purpose="snapshot"
            ):
                _restore_snapshot_unlocked(database, snapshot)


def _restore_snapshot_unlocked(database: Path, snapshot: Path) -> None:
    if not snapshot.is_file():
        raise FileNotFoundError(f"Heraldor snapshot not found: {snapshot}")
    check = sqlite3.connect(snapshot.resolve().as_uri() + "?mode=ro", uri=True)
    try:
        integrity = str(check.execute("PRAGMA integrity_check").fetchone()[0])
    finally:
        check.close()
    if integrity != "ok":
        raise RuntimeError(f"Heraldor snapshot failed integrity_check: {integrity}")

    database.parent.mkdir(parents=True, exist_ok=True)
    temporary = database.with_suffix(database.suffix + ".restore.tmp")
    temporary.unlink(missing_ok=True)
    shutil.copyfile(snapshot, temporary)
    for suffix in ("-wal", "-shm"):
        Path(str(database) + suffix).unlink(missing_ok=True)
    os.replace(temporary, database)


def parse_score_output(output: str, objective: str = "zapeg_hsvc") -> int | None:
    """Parse the score value, never digits embedded in a player name."""

    match = re.search(r"\bhas\s+(-?\d+)\b", output)
    if match:
        return int(match.group(1))

    # Some server/localization combinations move the number. The objective is
    # digit-free, so use the last integer before its bracketed display.
    marker = f"[{objective}]"
    prefix = output.split(marker, 1)[0] if marker in output else ""
    values = re.findall(r"(?<![A-Za-z0-9_])-?\d+(?![A-Za-z0-9_])", prefix)
    return int(values[-1]) if values else None


def parse_pos_output(output: str) -> tuple[float, float, float] | None:
    """Parse `data get entity <player> Pos` into exact doubles, or None."""

    match = re.search(
        r"\[\s*(-?\d+(?:\.\d+)?)d\s*,\s*(-?\d+(?:\.\d+)?)d\s*,"
        r"\s*(-?\d+(?:\.\d+)?)d\s*\]",
        output,
    )
    if not match:
        return None
    return (float(match.group(1)), float(match.group(2)), float(match.group(3)))


def parse_death_site(output: str) -> tuple[int, int, int, str] | None:
    """Parse the stored `death_<name>` compound into (x, y, z, dimension)."""

    coords = {}
    for axis in ("x", "y", "z"):
        match = re.search(rf"\b{axis}:\s*(-?\d+)\b", output)
        if not match:
            return None
        coords[axis] = int(match.group(1))
    dimension = re.search(r'\bdim:\s*"([a-z0-9_:./-]+)"', output)
    if not dimension:
        return None
    return (coords["x"], coords["y"], coords["z"], dimension.group(1))


def parse_last_minion_kill(output: str) -> tuple[str, int, int] | None:
    """Parse `last_minion_kill` into (player, sequence, world_token)."""

    player = re.search(r'\bplayer:\s*"([A-Za-z0-9_]{1,16})"', output)
    sequence = re.search(r"\bsequence:\s*(-?\d+)\b", output)
    world = re.search(r"\bworld_token:\s*(-?\d+)\b", output)
    if not player or not sequence or not world:
        return None
    return (player.group(1), int(sequence.group(1)), int(world.group(1)))


class DirectorStore:
    def __init__(
        self,
        db_path: str | os.PathLike[str],
        *,
        snapshot_path: str | os.PathLike[str] | None = None,
        policy: DirectorPolicy | None = None,
        clock=time.time,
        recover_interrupted_attempts: bool = True,
        audio_sink_enabled: bool = False,
    ) -> None:
        self.db_path = Path(db_path) if str(db_path) != ":memory:" else None
        self.snapshot_path = Path(snapshot_path) if snapshot_path else None
        self.policy = policy or DirectorPolicy()
        self.clock = clock
        self.audio_sink_enabled = audio_sink_enabled

        if self.db_path:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(str(db_path), timeout=5, isolation_level=None)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA busy_timeout=5000")
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.execute("PRAGMA synchronous=FULL")
        self.connection.execute("PRAGMA journal_mode=WAL")
        self._migrate()
        if recover_interrupted_attempts:
            self._recover_interrupted_attempts()

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "DirectorStore":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            yield self.connection
        except Exception:
            self.connection.rollback()
            raise
        else:
            self.connection.commit()

    def _migrate(self) -> None:
        version = int(self.connection.execute("PRAGMA user_version").fetchone()[0])
        if version > SCHEMA_VERSION:
            raise RuntimeError(
                f"Heraldor DB schema {version} is newer than supported {SCHEMA_VERSION}"
            )

        if version < 1:
            with self._transaction() as db:
                db.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS events (
                        event_id TEXT PRIMARY KEY,
                        kind TEXT NOT NULL,
                        category TEXT NOT NULL,
                        subject TEXT,
                        rehearsal INTEGER NOT NULL DEFAULT 0 CHECK (rehearsal IN (0, 1)),
                        payload_json TEXT NOT NULL DEFAULT '{}',
                        status TEXT NOT NULL,
                        created_at INTEGER NOT NULL,
                        attempted_at INTEGER,
                        finished_at INTEGER,
                        error TEXT
                    );
                    CREATE INDEX IF NOT EXISTS events_policy_idx
                        ON events (rehearsal, category, created_at);
                    CREATE INDEX IF NOT EXISTS events_kind_idx
                        ON events (rehearsal, kind, created_at);
                    CREATE INDEX IF NOT EXISTS events_subject_idx
                        ON events (rehearsal, subject, created_at);

                    CREATE TABLE IF NOT EXISTS source_offsets (
                        source TEXT PRIMARY KEY,
                        high_water INTEGER NOT NULL CHECK (high_water >= 0),
                        updated_at INTEGER NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS story_flags (
                        flag TEXT PRIMARY KEY,
                        event_id TEXT NOT NULL REFERENCES events(event_id),
                        created_at INTEGER NOT NULL
                    );

                    CREATE TABLE IF NOT EXISTS outbox (
                        event_id TEXT NOT NULL REFERENCES events(event_id),
                        sink TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        payload_json TEXT NOT NULL,
                        status TEXT NOT NULL,
                        created_at INTEGER NOT NULL,
                        attempted_at INTEGER,
                        delivered_at INTEGER,
                        error TEXT,
                        PRIMARY KEY (event_id, sink)
                    );
                    """
                )
                db.execute("PRAGMA user_version=1")

        if version < 2:
            # v2: stalking memory (coarse per-world visit cells) and the
            # Director's small pacing-memory key/value store (aftermath
            # flags). Both are pacing state, never story state.
            with self._transaction() as db:
                db.executescript(
                    """
                    CREATE TABLE IF NOT EXISTS stalk_cells (
                        world_token TEXT NOT NULL,
                        subject TEXT NOT NULL,
                        cell_x INTEGER NOT NULL,
                        cell_z INTEGER NOT NULL,
                        visits INTEGER NOT NULL DEFAULT 1 CHECK (visits >= 1),
                        last_seen INTEGER NOT NULL,
                        PRIMARY KEY (world_token, subject, cell_x, cell_z)
                    );

                    CREATE TABLE IF NOT EXISTS director_meta (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at INTEGER NOT NULL
                    );
                    """
                )
                db.execute("PRAGMA user_version=2")

    def _recover_interrupted_attempts(self) -> None:
        """Recover Director-owned ambient/directed attempts only.

        Audio attempts belong to the separately locked voice worker. Opening or
        restarting the Director must never alter an in-progress playback.
        """

        now = int(self.clock())
        with self._transaction() as db:
            db.execute(
                """
                UPDATE events
                   SET status = 'ambiguous', finished_at = ?,
                       error = COALESCE(error, 'process restarted during side effect')
                 WHERE status = 'attempting'
                """,
                (now,),
            )

    def backup_snapshot(self) -> None:
        """Write a transactionally consistent copy for the normal server backup."""

        if not self.snapshot_path or not self.db_path:
            return
        # Director and voice are separate SQLite writers. Serializing the whole
        # source-backup-and-replace sequence prevents an older, slower backup
        # from overwriting a newer replay barrier written by the other process.
        with DirectorStateLock(
            snapshot_lock_path(self.db_path), blocking=True, purpose="snapshot"
        ):
            self.snapshot_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.snapshot_path.with_name(
                f"{self.snapshot_path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp"
            )
            try:
                target = sqlite3.connect(temporary)
                try:
                    self.connection.backup(target)
                finally:
                    target.close()
                os.replace(temporary, self.snapshot_path)
            finally:
                temporary.unlink(missing_ok=True)

    @staticmethod
    def _campaign_state(db: sqlite3.Connection, world_token: str) -> CampaignState:
        phase = "dormant"
        paused = False
        rows = db.execute(
            """
            SELECT kind, payload_json FROM events
             WHERE category = 'campaign' AND status = 'delivered'
             ORDER BY created_at, rowid
            """
        )
        for row in rows:
            try:
                payload = json.loads(str(row["payload_json"]))
                control = payload["control"]
                if str(control["world_token"]) != world_token:
                    continue
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                continue

            kind = str(row["kind"])
            if kind == "director_phase":
                candidate = payload.get("phase")
                if candidate in CONTROL_PHASES:
                    # Corrupt or hand-edited rows cannot rewind the campaign.
                    phase = CONTROL_PHASES[
                        max(CONTROL_PHASES.index(phase), CONTROL_PHASES.index(candidate))
                    ]
            elif kind == "director_pause":
                paused = True
            elif kind == "director_resume":
                paused = False
        return CampaignState(world_token, phase, paused)

    def campaign_state(self, world_token: int | str) -> CampaignState:
        token = normalize_world_token(world_token)
        return self._campaign_state(self.connection, token)

    def record_control_event(
        self,
        request: ControlRequest,
        *,
        kind: str,
        category: str,
        status: str,
        payload: dict[str, object] | None = None,
        subject: str | None = None,
        rehearsal: bool = False,
        error: str | None = None,
        now: int | None = None,
    ) -> ControlEventRecord:
        """Insert one canonical request row, or return its existing terminal state."""

        if category not in {"campaign", "operator", "directed"}:
            raise ValueError(f"invalid control event category: {category}")
        if status not in {"reserved", "delivered", "rejected", "suppressed_expired"}:
            raise ValueError(f"invalid initial control event status: {status}")
        timestamp = int(self.clock() if now is None else now)
        body = dict(payload or {})
        if "control" in body:
            raise ValueError("control payload is reserved")
        body["control"] = {
            "version": CONTROL_TOKEN_VERSION,
            "world_token": request.world_token,
            "nonce": request.nonce,
            "expires_at": request.expires_at,
            "action": request.action,
            "argument": request.argument,
            "target": request.target,
            "operator": request.operator,
        }
        finished_at = timestamp if status != "reserved" else None
        with self._transaction() as db:
            changed = db.execute(
                """
                INSERT OR IGNORE INTO events
                    (event_id, kind, category, subject, rehearsal, payload_json,
                     status, created_at, finished_at, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request.event_id,
                    kind,
                    category,
                    subject.casefold() if subject else None,
                    int(rehearsal),
                    compact_json(body),
                    status,
                    timestamp,
                    finished_at,
                    error[:500] if error else None,
                ),
            ).rowcount
            row = db.execute(
                "SELECT status FROM events WHERE event_id = ?", (request.event_id,)
            ).fetchone()
        if changed:
            self.backup_snapshot()
        return ControlEventRecord(request.event_id, str(row["status"]), bool(changed))

    def control_event_status(self, event_id: str) -> str | None:
        row = self.connection.execute(
            "SELECT status FROM events WHERE event_id = ?", (event_id,)
        ).fetchone()
        return str(row["status"]) if row else None

    def finish_reserved_control(
        self,
        event_id: str,
        *,
        status: str,
        error: str,
        now: int | None = None,
    ) -> bool:
        if status not in {"rejected", "suppressed_expired"}:
            raise ValueError(f"invalid reserved control terminal status: {status}")
        timestamp = int(self.clock() if now is None else now)
        with self._transaction() as db:
            changed = db.execute(
                """
                UPDATE events SET status = ?, finished_at = ?, error = ?
                 WHERE event_id = ? AND status = 'reserved'
                """,
                (status, timestamp, error[:500], event_id),
            ).rowcount
        if changed:
            self.backup_snapshot()
        return bool(changed)

    def reserve_ambient(
        self,
        kind: str,
        *,
        subject: str | None = None,
        payload: dict[str, object] | None = None,
        rehearsal: bool = False,
        world_token: int | str | None = None,
        now: int | None = None,
        event_id: str | None = None,
    ) -> Reservation | None:
        if kind not in AMBIENT_KINDS:
            raise ValueError(f"unsupported ambient kind: {kind}")
        if not rehearsal and world_token is None:
            raise ValueError("live ambient reservation requires a world token")
        timestamp = int(self.clock() if now is None else now)
        identifier = event_id or f"ambient:{kind}:{timestamp}:{uuid.uuid4().hex}"
        token = normalize_world_token(world_token) if world_token is not None else None
        event_payload = dict(payload or {})
        if token:
            supplied_token = event_payload.get("world_token")
            if supplied_token is not None and str(supplied_token) != token:
                raise ValueError("ambient payload has a different world token")
            event_payload["world_token"] = token

        with self._transaction() as db:
            if not rehearsal:
                assert token is not None
                state = self._campaign_state(db, token)
                if state.phase == "dormant" or state.paused:
                    return None
            if not rehearsal and not self._ambient_allowed(db, kind, subject, timestamp):
                return None
            try:
                db.execute(
                    """
                    INSERT INTO events
                        (event_id, kind, category, subject, rehearsal, payload_json, status, created_at)
                    VALUES (?, ?, 'ambient', ?, ?, ?, 'reserved', ?)
                    """,
                    (
                        identifier,
                        kind,
                        subject.casefold() if subject else None,
                        int(rehearsal),
                        compact_json(event_payload),
                        timestamp,
                    ),
                )
            except sqlite3.IntegrityError:
                return None

        self.backup_snapshot()
        return Reservation(identifier, kind, subject, rehearsal)

    def _ambient_allowed(
        self, db: sqlite3.Connection, kind: str, subject: str | None, now: int
    ) -> bool:
        policy = self.policy

        if db.execute(
            """
            SELECT 1 FROM events
             WHERE rehearsal = 0 AND category = 'story' AND created_at > ?
             LIMIT 1
            """,
            (now - policy.major_quiet_seconds,),
        ).fetchone():
            return False

        if db.execute(
            """
            SELECT 1 FROM events
             WHERE rehearsal = 0 AND category = 'ambient' AND created_at > ?
             LIMIT 1
            """,
            (now - policy.ambient_gap_seconds,),
        ).fetchone():
            return False

        recent_count = int(
            db.execute(
                """
                SELECT COUNT(*) FROM events
                 WHERE rehearsal = 0 AND category = 'ambient' AND created_at > ?
                """,
                (now - policy.ambient_window_seconds,),
            ).fetchone()[0]
        )
        if recent_count >= policy.ambient_budget:
            return False

        cooldown = {
            "discord": policy.discord_cooldown_seconds,
            "shadows": policy.shadows_cooldown_seconds,
        }.get(kind)
        if cooldown and db.execute(
            """
            SELECT 1 FROM events
             WHERE rehearsal = 0 AND kind = ? AND created_at > ?
             LIMIT 1
            """,
            (kind, now - cooldown),
        ).fetchone():
            return False

        if subject and db.execute(
            """
            SELECT 1 FROM events
             WHERE rehearsal = 0 AND subject = ? AND created_at > ?
               AND status IN ('reserved', 'attempting', 'delivered', 'ambiguous')
             LIMIT 1
            """,
            (subject.casefold(), now - policy.targeted_gap_seconds),
        ).fetchone():
            return False
        return True

    def mark_attempting(self, event_id: str, *, now: int | None = None) -> bool:
        timestamp = int(self.clock() if now is None else now)
        with self._transaction() as db:
            changed = db.execute(
                """
                UPDATE events SET status = 'attempting', attempted_at = ?
                 WHERE event_id = ? AND status = 'reserved'
                """,
                (timestamp, event_id),
            ).rowcount
        if changed:
            self.backup_snapshot()
        return bool(changed)

    def finish_attempt(
        self,
        event_id: str,
        *,
        delivered: bool | None,
        error: str | None = None,
        now: int | None = None,
    ) -> bool:
        timestamp = int(self.clock() if now is None else now)
        status = (
            "ambiguous"
            if delivered is None
            else ("delivered" if delivered else "failed")
        )
        with self._transaction() as db:
            changed = db.execute(
                """
                UPDATE events SET status = ?, finished_at = ?, error = ?
                 WHERE event_id = ? AND status = 'attempting'
                """,
                (status, timestamp, error[:500] if error else None, event_id),
            ).rowcount
        if changed:
            self.backup_snapshot()
        return bool(changed)

    def ingest_servant_score(
        self,
        score: int,
        *,
        world_token: int | str,
        now: int | None = None,
    ) -> ServantIngestResult:
        if score < 0:
            raise ValueError("servant score cannot be negative")
        threshold = SERVANT_THRESHOLD
        token = normalize_world_token(world_token)
        source = SERVANT_SOURCE_PREFIX + token
        story_flag = SERVANT_STORY_FLAG_PREFIX + token
        threshold_event_id = servant_story_event_id(token)
        timestamp = int(self.clock() if now is None else now)
        victories: list[str] = []
        story_event_id: str | None = None
        story_output_status: str | None = None
        changed = False

        with self._transaction() as db:
            row = db.execute(
                "SELECT high_water FROM source_offsets WHERE source = ?", (source,)
            ).fetchone()
            previous = int(row[0]) if row else 0
            if score > SERVANT_MAX_SCORE or score - previous > SERVANT_MAX_INGEST_JUMP:
                result = ServantIngestResult(
                    previous,
                    previous,
                    (),
                    None,
                    quarantined=True,
                )
            elif score <= previous:
                if row is None:
                    db.execute(
                        "INSERT INTO source_offsets (source, high_water, updated_at) VALUES (?, 0, ?)",
                        (source, timestamp),
                    )
                    changed = True
                result = ServantIngestResult(previous, previous, (), None, score < previous)
            else:
                for ordinal in range(previous + 1, score + 1):
                    victory_id = f"mc:heraldor-servant:v1:world:{token}:{ordinal}"
                    db.execute(
                        """
                        INSERT OR IGNORE INTO events
                            (event_id, kind, category, payload_json, status, created_at)
                        VALUES (?, 'servant_victory', 'observation', ?, 'observed', ?)
                        """,
                        (
                            victory_id,
                            compact_json({"ordinal": ordinal, "world_token": token}),
                            timestamp,
                        ),
                    )
                    victories.append(victory_id)

                if previous < threshold <= score:
                    existing = db.execute(
                        "SELECT 1 FROM story_flags WHERE flag = ?", (story_flag,)
                    ).fetchone()
                    if not existing:
                        story_payload = {
                            "trigger": {
                                "kind": "servant_victory_threshold",
                                "count": threshold,
                                "world_token": token,
                            }
                        }
                        db.execute(
                            """
                            INSERT INTO events
                                (event_id, kind, category, payload_json, status, created_at)
                            VALUES (?, 'servant_threshold', 'story', ?, 'observed', ?)
                            """,
                            (threshold_event_id, compact_json(story_payload), timestamp),
                        )
                        db.execute(
                            "INSERT INTO story_flags (flag, event_id, created_at) VALUES (?, ?, ?)",
                            (story_flag, threshold_event_id, timestamp),
                        )
                        audio_payload = {
                            "event_id": threshold_event_id,
                            "type": AUDIO_EVENT_TYPE,
                            "clip_id": SERVANT_AUDIO_CLIP_ID,
                            "expires_at": timestamp + AUDIO_LIVE_TTL_SECONDS,
                            "rehearsal": False,
                            "trigger": {
                                "kind": "servant_victory_threshold",
                                "count": threshold,
                                "world_token": token,
                            },
                        }
                        campaign = self._campaign_state(db, token)
                        if campaign.phase == "dormant":
                            story_output_status = "suppressed_campaign_dormant"
                        elif campaign.paused:
                            story_output_status = "suppressed_campaign_paused"
                        elif self.audio_sink_enabled:
                            story_output_status = "pending"
                        else:
                            story_output_status = "suppressed_no_sink"
                        db.execute(
                            """
                            INSERT INTO outbox
                                (event_id, sink, event_type, payload_json, status, created_at)
                            VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (
                                threshold_event_id,
                                AUDIO_SINK,
                                AUDIO_EVENT_TYPE,
                                compact_json(audio_payload),
                                story_output_status,
                                timestamp,
                            ),
                        )
                        story_event_id = threshold_event_id

                db.execute(
                    """
                    INSERT INTO source_offsets (source, high_water, updated_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT(source) DO UPDATE
                        SET high_water = excluded.high_water, updated_at = excluded.updated_at
                    """,
                    (source, score, timestamp),
                )
                changed = True
                result = ServantIngestResult(
                    previous,
                    score,
                    tuple(victories),
                    story_event_id,
                    story_output_status=story_output_status,
                )

        if changed:
            self.backup_snapshot()
        return result

    def record_stalk_visit(
        self,
        world_token: int | str,
        subject: str,
        x: float,
        z: float,
        *,
        now: int | None = None,
    ) -> bool:
        """Remember one coarse visit cell for the stalking memory.

        Privacy boundary: positions collapse into 32-block cells, keyed per
        world and per player, capped per player, and every cell from any
        other world is purged the moment a different world token is seen.
        Cells are disposable pacing memory, so they are deliberately not
        snapshot-backed: a restore simply forgets where players have been.
        """

        token = normalize_world_token(world_token)
        if not PLAYER_NAME_RE.fullmatch(subject):
            raise ValueError(f"invalid stalk subject: {subject!r}")
        if not math.isfinite(x) or not math.isfinite(z):
            raise ValueError("stalk coordinates must be finite")
        if abs(x) > 30_000_000 or abs(z) > 30_000_000:
            raise ValueError("stalk coordinates outside the world border")
        timestamp = int(self.clock() if now is None else now)
        cell_x = math.floor(x / STALK_CELL_SIZE)
        cell_z = math.floor(z / STALK_CELL_SIZE)
        folded = subject.casefold()
        with self._transaction() as db:
            db.execute("DELETE FROM stalk_cells WHERE world_token <> ?", (token,))
            db.execute(
                """
                INSERT INTO stalk_cells
                    (world_token, subject, cell_x, cell_z, visits, last_seen)
                VALUES (?, ?, ?, ?, 1, ?)
                ON CONFLICT(world_token, subject, cell_x, cell_z) DO UPDATE
                    SET visits = visits + 1, last_seen = excluded.last_seen
                """,
                (token, folded, cell_x, cell_z, timestamp),
            )
            db.execute(
                """
                DELETE FROM stalk_cells
                 WHERE world_token = ? AND subject = ? AND rowid NOT IN (
                     SELECT rowid FROM stalk_cells
                      WHERE world_token = ? AND subject = ?
                      ORDER BY last_seen DESC, rowid DESC
                      LIMIT ?
                 )
                """,
                (token, folded, token, folded, STALK_MAX_CELLS_PER_SUBJECT),
            )
        return True

    @staticmethod
    def _stalk_hint(
        db: sqlite3.Connection,
        world_token: str,
        subject: str,
        roll: random.Random,
    ) -> tuple[int, int] | None:
        rows = db.execute(
            """
            SELECT cell_x, cell_z, visits FROM stalk_cells
             WHERE world_token = ? AND subject = ?
             ORDER BY cell_x, cell_z
            """,
            (world_token, subject.casefold()),
        ).fetchall()
        if not rows:
            return None
        cells = [(int(row["cell_x"]), int(row["cell_z"])) for row in rows]
        weights = [int(row["visits"]) for row in rows]
        cell_x, cell_z = roll.choices(cells, weights=weights, k=1)[0]
        # The hint is the cell centre: the runtime still chooses the exact
        # anchor, so the memory never pins a precise position.
        return (
            cell_x * STALK_CELL_SIZE + STALK_CELL_SIZE // 2,
            cell_z * STALK_CELL_SIZE + STALK_CELL_SIZE // 2,
        )

    def stalk_hint(
        self,
        world_token: int | str,
        subject: str,
        *,
        rng: random.Random | None = None,
    ) -> tuple[int, int] | None:
        """A visit-weighted coarse anchor hint, or None when nowhere is known."""

        token = normalize_world_token(world_token)
        if not PLAYER_NAME_RE.fullmatch(subject):
            raise ValueError(f"invalid stalk subject: {subject!r}")
        return self._stalk_hint(
            self.connection, token, subject, rng or random.Random()
        )

    def record_servant_aftermath(
        self,
        world_token: int | str,
        subject: str,
        ordinal: int,
        *,
        now: int | None = None,
    ) -> bool:
        """After a servant victory, that player's next scene is footsteps_01.

        Pure pacing memory in director_meta plus an audit observation; the
        scheduler honours and consumes the flag when it next plans a scene
        for the subject. Operator-triggered scenes are never overridden.
        """

        token = normalize_world_token(world_token)
        if not PLAYER_NAME_RE.fullmatch(subject):
            raise ValueError(f"invalid aftermath subject: {subject!r}")
        if ordinal < 1:
            raise ValueError("aftermath ordinal must be positive")
        timestamp = int(self.clock() if now is None else now)
        key = AFTERMATH_META_PREFIX + token + ":" + subject.casefold()
        with self._transaction() as db:
            db.execute(
                """
                INSERT INTO director_meta (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE
                    SET value = excluded.value, updated_at = excluded.updated_at
                """,
                (key, AFTERMATH_PROFILE, timestamp),
            )
            db.execute(
                """
                INSERT OR IGNORE INTO events
                    (event_id, kind, category, subject, payload_json, status, created_at)
                VALUES (?, 'servant_aftermath', 'observation', ?, ?, 'observed', ?)
                """,
                (
                    f"mc:heraldor-servant:aftermath:v1:world:{token}:{ordinal}",
                    subject.casefold(),
                    compact_json(
                        {
                            "ordinal": ordinal,
                            "world_token": token,
                            "profile": AFTERMATH_PROFILE,
                        }
                    ),
                    timestamp,
                ),
            )
        self.backup_snapshot()
        return True

    def colossus_stage(self, world_token: int | str, subject: str) -> int:
        """The target's current colossus approach stage (0 when never seen).

        Pure pacing memory in director_meta, world-tokened like servant
        state; rehearsals read it but never advance it.
        """

        token = normalize_world_token(world_token)
        key = COLOSSUS_META_PREFIX + token + ":" + subject.casefold()
        with self._transaction() as db:
            row = db.execute(
                "SELECT value FROM director_meta WHERE key = ?", (key,)
            ).fetchone()
        if row is None:
            return 0
        try:
            stage = int(str(row["value"]))
        except ValueError:
            return 0
        return max(0, min(COLOSSUS_MAX_STAGE, stage))

    def advance_colossus_stage(
        self,
        world_token: int | str,
        subject: str,
        *,
        now: int | None = None,
    ) -> int:
        """Advance the target's colossus stage after a delivered live scene.

        Stages climb 0..COLOSSUS_MAX_STAGE and wrap to 0 after the finale, so
        the encounter passes once it has stood over the target. Only called
        for delivered live triggers — never for rehearsals or failures.
        """

        token = normalize_world_token(world_token)
        if not PLAYER_NAME_RE.fullmatch(subject):
            raise ValueError(f"invalid colossus subject: {subject!r}")
        timestamp = int(self.clock() if now is None else now)
        key = COLOSSUS_META_PREFIX + token + ":" + subject.casefold()
        with self._transaction() as db:
            row = db.execute(
                "SELECT value FROM director_meta WHERE key = ?", (key,)
            ).fetchone()
            try:
                current = int(str(row["value"])) if row is not None else 0
            except ValueError:
                current = 0
            current = max(0, min(COLOSSUS_MAX_STAGE, current))
            following = current + 1 if current < COLOSSUS_MAX_STAGE else 0
            db.execute(
                """
                INSERT INTO director_meta (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE
                    SET value = excluded.value, updated_at = excluded.updated_at
                """,
                (key, str(following), timestamp),
            )
            db.execute(
                """
                INSERT OR IGNORE INTO events
                    (event_id, kind, category, subject, payload_json, status, created_at)
                VALUES (?, 'colossus_stage', 'observation', ?, ?, 'observed', ?)
                """,
                (
                    f"director:colossus:stage:v1:{uuid.uuid4().hex}",
                    subject.casefold(),
                    compact_json(
                        {
                            "world_token": token,
                            "previous_stage": current,
                            "stage": following,
                        }
                    ),
                    timestamp,
                ),
            )
        self.backup_snapshot()
        return following

    def reset_colossus_stage(
        self,
        world_token: int | str,
        subject: str,
        *,
        now: int | None = None,
    ) -> None:
        """Operator reset: the target's colossus approach starts over."""

        token = normalize_world_token(world_token)
        if not PLAYER_NAME_RE.fullmatch(subject):
            raise ValueError(f"invalid colossus subject: {subject!r}")
        timestamp = int(self.clock() if now is None else now)
        key = COLOSSUS_META_PREFIX + token + ":" + subject.casefold()
        with self._transaction() as db:
            db.execute("DELETE FROM director_meta WHERE key = ?", (key,))
            db.execute(
                """
                INSERT OR IGNORE INTO events
                    (event_id, kind, category, subject, payload_json, status, created_at)
                VALUES (?, 'colossus_stage', 'observation', ?, ?, 'observed', ?)
                """,
                (
                    f"director:colossus:reset:v1:{uuid.uuid4().hex}",
                    subject.casefold(),
                    compact_json({"world_token": token, "reset": True}),
                    timestamp,
                ),
            )
        self.backup_snapshot()

    def manual_discord_cooldown_remaining(
        self,
        world_token: int | str,
        *,
        gap_seconds: int,
        now: int | None = None,
    ) -> int:
        """Seconds left before another operator Discord whisper may post.

        One world-tokened marker paces the in-game bridge action so the
        channel can never be spammed; zero means a post may go now.
        """

        token = normalize_world_token(world_token)
        timestamp = int(self.clock() if now is None else now)
        key = MANUAL_DISCORD_META_PREFIX + token
        with self._transaction() as db:
            row = db.execute(
                "SELECT value FROM director_meta WHERE key = ?", (key,)
            ).fetchone()
        if row is None:
            return 0
        try:
            last = int(str(row["value"]))
        except ValueError:
            return 0
        return max(0, gap_seconds - (timestamp - last))

    def record_manual_discord_post(
        self,
        world_token: int | str,
        *,
        now: int | None = None,
    ) -> None:
        """Mark the world-tokened manual Discord whisper cooldown."""

        token = normalize_world_token(world_token)
        timestamp = int(self.clock() if now is None else now)
        key = MANUAL_DISCORD_META_PREFIX + token
        with self._transaction() as db:
            db.execute(
                """
                INSERT INTO director_meta (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE
                    SET value = excluded.value, updated_at = excluded.updated_at
                """,
                (key, str(timestamp), timestamp),
            )
        self.backup_snapshot()

    def death_high_water(self, world_token: int | str, subject: str) -> int:
        token = normalize_world_token(world_token)
        if not PLAYER_NAME_RE.fullmatch(subject):
            raise ValueError(f"invalid death subject: {subject!r}")
        source = DEATH_SOURCE_TEMPLATE.format(
            subject=subject.casefold(), world=token
        )
        row = self.connection.execute(
            "SELECT high_water FROM source_offsets WHERE source = ?", (source,)
        ).fetchone()
        return int(row[0]) if row else 0

    def ingest_death(
        self,
        world_token: int | str,
        subject: str,
        sequence: int,
        site: tuple[int, int, int, str] | None = None,
        *,
        now: int | None = None,
    ) -> DeathIngestResult:
        """High-water ingestion of the per-player death counter.

        Only the newest death has a known site (the world stores just the
        last one); older skipped ordinals are recorded site-less so the log
        tail stays complete without ever inventing coordinates.
        """

        token = normalize_world_token(world_token)
        if not PLAYER_NAME_RE.fullmatch(subject):
            raise ValueError(f"invalid death subject: {subject!r}")
        if sequence < 0:
            raise ValueError("death sequence cannot be negative")
        timestamp = int(self.clock() if now is None else now)
        source = DEATH_SOURCE_TEMPLATE.format(
            subject=subject.casefold(), world=token
        )
        folded = subject.casefold()
        deaths: list[str] = []
        changed = False

        with self._transaction() as db:
            row = db.execute(
                "SELECT high_water FROM source_offsets WHERE source = ?", (source,)
            ).fetchone()
            previous = int(row[0]) if row else 0
            if sequence - previous > DEATH_MAX_INGEST_JUMP:
                result = DeathIngestResult(previous, previous, (), quarantined=True)
            elif sequence <= previous:
                if row is None:
                    db.execute(
                        "INSERT INTO source_offsets (source, high_water, updated_at) VALUES (?, 0, ?)",
                        (source, timestamp),
                    )
                    changed = True
                result = DeathIngestResult(
                    previous, previous, (), regression=sequence < previous
                )
            else:
                for ordinal in range(previous + 1, sequence + 1):
                    death_id = (
                        f"mc:heraldor-death:v1:world:{token}:{folded}:{ordinal}"
                    )
                    payload: dict[str, object] = {
                        "ordinal": ordinal,
                        "world_token": token,
                    }
                    if ordinal == sequence and site is not None:
                        payload["site"] = {"x": site[0], "y": site[1], "z": site[2]}
                        payload["dimension"] = site[3]
                    db.execute(
                        """
                        INSERT OR IGNORE INTO events
                            (event_id, kind, category, subject, payload_json, status, created_at)
                        VALUES (?, 'player_death', 'observation', ?, ?, 'observed', ?)
                        """,
                        (death_id, folded, compact_json(payload), timestamp),
                    )
                    deaths.append(death_id)
                db.execute(
                    """
                    INSERT INTO source_offsets (source, high_water, updated_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT(source) DO UPDATE
                        SET high_water = excluded.high_water, updated_at = excluded.updated_at
                    """,
                    (source, sequence, timestamp),
                )
                changed = True
                result = DeathIngestResult(previous, sequence, tuple(deaths))

        if changed:
            self.backup_snapshot()
        return result

    def plan_and_reserve_scene(
        self,
        world_token: int | str,
        players: list[str],
        *,
        now: int | None = None,
        rng: random.Random | None = None,
    ) -> ScenePlan | None:
        """Plan and atomically reserve one scheduler-driven live scene.

        Scheduled beats: delivered scenes cluster into a night of activity —
        each beat keeps the night alive for cluster_open_seconds — and once
        the night ends or its budget is spent, cluster_silence_seconds of
        silence must pass before a new one opens. Story quiet windows and
        per-subject gaps still apply, and a scene already in flight anywhere
        suppresses planning entirely.
        """

        token = normalize_world_token(world_token)
        timestamp = int(self.clock() if now is None else now)
        roll = rng if rng is not None else random.Random()
        names: dict[str, str] = {}
        for name in players:
            if PLAYER_NAME_RE.fullmatch(name):
                names.setdefault(name.casefold(), name)
        if not names:
            return None
        policy = self.policy

        with self._transaction() as db:
            state = self._campaign_state(db, token)
            if state.phase == "dormant" or state.paused:
                return None

            if db.execute(
                """
                SELECT 1 FROM events
                 WHERE rehearsal = 0 AND category = 'directed'
                   AND status IN ('reserved', 'attempting')
                 LIMIT 1
                """
            ).fetchone():
                return None

            scene_times = [
                int(row["created_at"])
                for row in db.execute(
                    """
                    SELECT created_at FROM events
                     WHERE rehearsal = 0 AND category = 'directed'
                       AND kind = 'director_scene' AND status = 'delivered'
                     ORDER BY created_at
                    """
                )
            ]
            opening = (
                not scene_times
                or timestamp - scene_times[-1] >= policy.cluster_silence_seconds
            )
            if not opening:
                if timestamp - scene_times[-1] > policy.cluster_open_seconds:
                    # The night ended; the silence between nights has begun.
                    return None
                cluster_count = 1
                for index in range(len(scene_times) - 1, 0, -1):
                    if (
                        scene_times[index] - scene_times[index - 1]
                        <= policy.cluster_open_seconds
                    ):
                        cluster_count += 1
                    else:
                        break
                if cluster_count >= policy.cluster_scene_budget:
                    return None

            if db.execute(
                """
                SELECT 1 FROM events
                 WHERE rehearsal = 0 AND category = 'story' AND created_at > ?
                 LIMIT 1
                """,
                (timestamp - policy.major_quiet_seconds,),
            ).fetchone():
                return None

            chance = (
                policy.scheduler_open_probability
                if opening
                else policy.scheduler_beat_probability
            )
            if roll.random() >= chance:
                return None

            gap = (
                policy.targeted_gap_seconds
                if opening
                else policy.cluster_subject_gap_seconds
            )
            eligible = []
            for folded in names:
                if db.execute(
                    """
                    SELECT 1 FROM events
                     WHERE rehearsal = 0 AND subject = ? AND created_at > ?
                       AND status IN ('reserved', 'attempting', 'delivered', 'ambiguous')
                     LIMIT 1
                    """,
                    (folded, timestamp - gap),
                ).fetchone():
                    continue
                eligible.append(folded)
            if not eligible:
                return None
            subject = roll.choice(eligible)

            profile: str | None = None
            hint: tuple[int, int] | None = None
            echo_of: str | None = None
            reason = "cluster_open" if opening else "cluster_beat"

            # Servant aftermath: the next scene is always footsteps_01.
            aftermath_key = AFTERMATH_META_PREFIX + token + ":" + subject
            row = db.execute(
                "SELECT value FROM director_meta WHERE key = ?", (aftermath_key,)
            ).fetchone()
            if row is not None:
                candidate = str(row["value"])
                if state.allows_profile(candidate):
                    profile = candidate
                    reason = "aftermath"
                    db.execute(
                        "DELETE FROM director_meta WHERE key = ?", (aftermath_key,)
                    )

            # Grave echo: rarely, a later scene answers an old death site.
            if profile is None and roll.random() < policy.grave_echo_probability:
                death_rows = db.execute(
                    """
                    SELECT event_id, payload_json, created_at FROM events
                     WHERE kind = 'player_death' AND category = 'observation'
                       AND subject = ? AND status = 'observed'
                     ORDER BY created_at
                    """,
                    (subject,),
                ).fetchall()
                for death in death_rows:
                    if int(death["created_at"]) > timestamp - policy.grave_echo_min_age_seconds:
                        continue
                    try:
                        payload = json.loads(str(death["payload_json"]))
                    except (ValueError, json.JSONDecodeError):
                        continue
                    if str(payload.get("world_token")) != token:
                        continue
                    candidate = roll.choice(("footsteps_01", "whisper_steps_01"))
                    if not state.allows_profile(candidate):
                        continue
                    profile = candidate
                    reason = "grave_echo"
                    echo_of = str(death["event_id"])
                    site = payload.get("site")
                    if profile in STALK_HINT_PROFILES and isinstance(site, dict):
                        try:
                            hint = (int(site["x"]), int(site["z"]))
                        except (KeyError, TypeError, ValueError):
                            hint = None
                    db.execute(
                        """
                        UPDATE events SET status = 'echoed'
                         WHERE event_id = ? AND status = 'observed'
                        """,
                        (echo_of,),
                    )
                    break

            if profile is None:
                allowed = [
                    name
                    for name in CONTROL_SCENE_PROFILE_PHASES
                    if state.allows_profile(name) and name not in OPERATOR_ONLY_PROFILES
                ]
                if not allowed:
                    return None
                profile = roll.choice(allowed)

            if hint is None and profile in STALK_HINT_PROFILES:
                hint = self._stalk_hint(db, token, subject, roll)

            ttl_ticks = scene_ttl_ticks(profile, state.phase)
            event_id = f"director:scene:{token}:{timestamp}:{uuid.uuid4().hex}"
            payload = {
                "profile": profile,
                "target": subject,
                "planner": "scheduler",
                "reason": reason,
                "world_token": token,
                "runtime_event_id": event_id,
            }
            if hint is not None:
                payload["hint_x"] = hint[0]
                payload["hint_z"] = hint[1]
            if echo_of is not None:
                payload["echo_of"] = echo_of
            db.execute(
                """
                INSERT INTO events
                    (event_id, kind, category, subject, rehearsal, payload_json,
                     status, created_at)
                VALUES (?, 'director_scene', 'directed', ?, 0, ?, 'reserved', ?)
                """,
                (event_id, subject, compact_json(payload), timestamp),
            )

        self.backup_snapshot()
        return ScenePlan(
            event_id=event_id,
            profile=profile,
            subject=names[subject],
            ttl_ticks=ttl_ticks,
            hint=hint,
            reason=reason,
        )

    def enqueue_audio_rehearsal(
        self,
        clip_id: str = SERVANT_AUDIO_CLIP_ID,
        *,
        now: int | None = None,
    ) -> str:
        """Queue an operator-only clip test without touching live story state."""

        if clip_id not in ALLOWED_AUDIO_CLIPS:
            raise ValueError(f"audio clip is not allowlisted: {clip_id}")
        timestamp = int(self.clock() if now is None else now)
        event_id = f"rehearsal:audio:{clip_id}:{timestamp}:{uuid.uuid4().hex}"
        payload = {
            "event_id": event_id,
            "type": AUDIO_EVENT_TYPE,
            "clip_id": clip_id,
            "expires_at": timestamp + AUDIO_REHEARSAL_TTL_SECONDS,
            "rehearsal": True,
        }
        with self._transaction() as db:
            db.execute(
                """
                INSERT INTO events
                    (event_id, kind, category, rehearsal, payload_json, status, created_at)
                VALUES (?, 'audio_rehearsal', 'operator', 1, ?, 'observed', ?)
                """,
                (event_id, compact_json({"clip_id": clip_id}), timestamp),
            )
            db.execute(
                """
                INSERT INTO outbox
                    (event_id, sink, event_type, payload_json, status, created_at)
                VALUES (?, ?, ?, ?, 'pending', ?)
                """,
                (event_id, AUDIO_SINK, AUDIO_EVENT_TYPE, compact_json(payload), timestamp),
            )
        self.backup_snapshot()
        return event_id

    def recover_interrupted_audio(self, *, now: int | None = None) -> int:
        """Make this voice worker's uncertain prior attempts terminal."""

        timestamp = int(self.clock() if now is None else now)
        with self._transaction() as db:
            changed = db.execute(
                """
                UPDATE outbox
                   SET status = 'ambiguous',
                       error = COALESCE(error, 'voice worker restarted during playback')
                 WHERE sink = ? AND status = 'attempting'
                """,
                (AUDIO_SINK,),
            ).rowcount
        if changed:
            self.backup_snapshot()
        return int(changed)

    def claim_next_audio(
        self,
        *,
        now: int | None = None,
        live_gap_seconds: int = AUDIO_LIVE_GAP_SECONDS,
        rehearsal_gap_seconds: int = AUDIO_REHEARSAL_GAP_SECONDS,
    ) -> AudioDelivery | None:
        """Atomically claim one fresh audio request for at-most-once playback."""

        timestamp = int(self.clock() if now is None else now)
        while True:
            terminal_change = False
            delivery: AudioDelivery | None = None
            with self._transaction() as db:
                row = db.execute(
                    """
                    SELECT o.event_id, o.payload_json, e.rehearsal
                      FROM outbox AS o
                      JOIN events AS e ON e.event_id = o.event_id
                     WHERE o.sink = ? AND o.event_type = ? AND o.status = 'pending'
                     ORDER BY o.created_at, o.event_id
                     LIMIT 1
                    """,
                    (AUDIO_SINK, AUDIO_EVENT_TYPE),
                ).fetchone()
                if row is None:
                    return None

                try:
                    payload = json.loads(str(row["payload_json"]))
                    expires_at = int(payload["expires_at"])
                except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                    db.execute(
                        """
                        UPDATE outbox SET status = 'rejected_clip', error = ?
                         WHERE event_id = ? AND sink = ? AND status = 'pending'
                        """,
                        ("invalid audio payload", row["event_id"], AUDIO_SINK),
                    )
                    terminal_change = True
                else:
                    rehearsal = bool(row["rehearsal"])
                    if expires_at <= timestamp:
                        db.execute(
                            """
                            UPDATE outbox SET status = 'suppressed_expired', error = ?
                             WHERE event_id = ? AND sink = ? AND status = 'pending'
                            """,
                            ("audio request expired", row["event_id"], AUDIO_SINK),
                        )
                        terminal_change = True
                    else:
                        gap = rehearsal_gap_seconds if rehearsal else live_gap_seconds
                        recent = db.execute(
                            """
                            SELECT 1
                              FROM outbox AS prior
                              JOIN events AS prior_event
                                ON prior_event.event_id = prior.event_id
                             WHERE prior.sink = ?
                               AND prior.event_id <> ?
                               AND prior_event.rehearsal = ?
                               AND prior.attempted_at > ?
                               AND prior.status IN ('attempting', 'delivered', 'ambiguous', 'failed')
                             LIMIT 1
                            """,
                            (
                                AUDIO_SINK,
                                row["event_id"],
                                int(rehearsal),
                                timestamp - gap,
                            ),
                        ).fetchone()
                        if recent:
                            db.execute(
                                """
                                UPDATE outbox SET status = 'suppressed_rate_limit', error = ?
                                 WHERE event_id = ? AND sink = ? AND status = 'pending'
                                """,
                                ("audio pacing gate closed", row["event_id"], AUDIO_SINK),
                            )
                            terminal_change = True
                        else:
                            changed = db.execute(
                                """
                                UPDATE outbox SET status = 'attempting', attempted_at = ?, error = NULL
                                 WHERE event_id = ? AND sink = ? AND status = 'pending'
                                """,
                                (timestamp, row["event_id"], AUDIO_SINK),
                            ).rowcount
                            if changed:
                                delivery = AudioDelivery(
                                    str(row["event_id"]), payload, rehearsal
                                )

            if terminal_change or delivery:
                # Persist the replay barrier before the caller may touch Discord.
                self.backup_snapshot()
            if delivery:
                return delivery

    def finish_audio(
        self,
        event_id: str,
        *,
        status: str,
        error: str | None = None,
        now: int | None = None,
    ) -> bool:
        terminal = {
            "delivered",
            "ambiguous",
            "failed",
            "rejected_clip",
            "rejected_destination",
            "suppressed_expired",
            "suppressed_empty_channel",
        }
        if status not in terminal:
            raise ValueError(f"invalid audio terminal status: {status}")
        timestamp = int(self.clock() if now is None else now)
        delivered_at = timestamp if status == "delivered" else None
        with self._transaction() as db:
            changed = db.execute(
                """
                UPDATE outbox
                   SET status = ?, delivered_at = ?, error = ?
                 WHERE event_id = ? AND sink = ? AND status = 'attempting'
                """,
                (
                    status,
                    delivered_at,
                    error[:500] if error else None,
                    event_id,
                    AUDIO_SINK,
                ),
            ).rowcount
        if changed:
            self.backup_snapshot()
        return bool(changed)

    def status(self) -> dict[str, object]:
        row = self.connection.execute(
            """
            SELECT source, high_water, updated_at FROM source_offsets
             WHERE source LIKE ? ORDER BY updated_at DESC, rowid DESC LIMIT 1
            """,
            (SERVANT_SOURCE_PREFIX + "%",),
        ).fetchone()
        servant_world_token = (
            str(row["source"])[len(SERVANT_SOURCE_PREFIX) :] if row else None
        )
        campaign = self.campaign_state(servant_world_token) if servant_world_token else None
        counts = {
            str(item["status"]): int(item["total"])
            for item in self.connection.execute(
                "SELECT status, COUNT(*) AS total FROM events GROUP BY status"
            )
        }
        outbox = [
            dict(item)
            for item in self.connection.execute(
                """
                SELECT event_id, sink, event_type, status, created_at,
                       attempted_at, delivered_at, error
                  FROM outbox ORDER BY created_at DESC LIMIT 10
                """
            )
        ]
        recent_events = [
            dict(item)
            for item in self.connection.execute(
                """
                SELECT event_id, kind, category, subject, status, created_at
                  FROM events ORDER BY created_at DESC, event_id DESC LIMIT 10
                """
            )
        ]
        return {
            "schema_version": SCHEMA_VERSION,
            "servant_world_token": servant_world_token,
            "servant_high_water": int(row["high_water"]) if row else 0,
            "servant_updated_at": int(row["updated_at"]) if row else None,
            "campaign": (
                {"phase": campaign.phase, "paused": campaign.paused}
                if campaign
                else {"phase": "dormant", "paused": False}
            ),
            "event_status_counts": counts,
            "recent_events": recent_events,
            "outbox": outbox,
        }
