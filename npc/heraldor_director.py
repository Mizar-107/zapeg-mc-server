#!/usr/bin/env python3
"""Persistent pacing and story state for the Heraldor presence engine."""

from __future__ import annotations

import json
import os
import re
import shutil
import sqlite3
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


SCHEMA_VERSION = 1
SERVANT_SOURCE_PREFIX = "minecraft:scoreboard:zapeg_hsvc:#total:v1:world:"
SERVANT_STORY_FLAG_PREFIX = "heraldor_servants_defeated_3_v1_world_"
SERVANT_STORY_EVENT_PREFIX = "story:heraldor-servants:defeated:3:v1:world:"
SERVANT_AUDIO_CLIP_ID = "servants_after_three_v1"
SERVANT_THRESHOLD = 3
SERVANT_MAX_SCORE = 1_000_000
SERVANT_MAX_INGEST_JUMP = 100
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
    "motion_echo_01": "servants",
    "light_fault_01": "manifestation",
}
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

    no_argument_actions = {"status", "pause", "resume", "phase_advance", "cancel"}
    if action in no_argument_actions:
        if argument != "-" or raw_target != "-":
            raise ValueError("unexpected Heraldor control arguments")
        target = None
    elif action == "phase_start":
        if argument not in CONTROL_START_PHASES or raw_target != "-":
            raise ValueError("invalid Heraldor campaign phase")
        target = None
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
        if version == SCHEMA_VERSION:
            return

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
            db.execute(f"PRAGMA user_version={SCHEMA_VERSION}")

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
