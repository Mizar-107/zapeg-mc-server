#!/usr/bin/env python3
"""Data-driven Heraldor campaign engine.

One authorable file (``campaign-heraldor.yml``) defines ordered chapters of
beats; this module validates it, keeps per-world progress in the Director's
SQLite meta store, and executes beats through an injected executor so tests
never need RCON. Two run modes share the same beats:

* manual stepping — ``/zapeg-lore story status|start|next|goto|reset``
* autonomous     — ``/zapeg-lore story auto on`` (the daemon advances beats,
  respecting wait conditions, night preference and quiet-cluster pacing)

``story rehearse`` plays the current beat with zero campaign/pacing writes:
scenes rehearse through the runtime's rehearsal path, text beats are shown to
the operator instead of the target. Rehearsals never advance anything.
"""

from __future__ import annotations

import json
import random
import re
import uuid
from dataclasses import dataclass, replace
from pathlib import Path

import yaml

from heraldor_director import (
    CAMPAIGN_GENERATION_META_PREFIX,
    CAMPAIGN_NIGHTS_META_PREFIX,
    CONTROL_EVENT_NAMESPACE,
    CONTROL_PHASES,
    CONTROL_SCENE_PROFILE_PHASES,
    DirectorStore,
    SCENE_MAX_TTL_TICKS,
    jittered_silence_seconds,
)

PLAYER_NAME_RE = re.compile(r"^[A-Za-z0-9_]{1,16}$")
TARGET_SELECTORS = frozenset({"random", "last_victim"})
BEAT_TYPES = frozenset(
    {"scene", "whisper", "global", "discord", "servant_wave", "wait"}
)
MAX_LINE_LENGTH = 200
MAX_SERVANT_WAVE = 3
# Attribution ladder (HD-2a): how a `global` broadcast is dressed. The name
# must be earned by the players, so early tiers broadcast unsigned; the
# glitch tier signs with an unreadable §k fragment; only manifestation shows
# the dark-red name. A beat-level `style:` overrides the tier default.
GLOBAL_STYLES = ("unsigned", "glitch", "named")
GLOBAL_STYLE_BY_TIER = {
    "presence": "unsigned",
    "servants": "glitch",
    "manifestation": "named",
}


class CampaignError(ValueError):
    """The campaign file is malformed; the engine fails closed."""


@dataclass(frozen=True)
class Beat:
    type: str
    label: str
    profile: str | None = None
    target: str | None = None
    ttl_ticks: int | None = None
    line: str | None = None
    pool: str | None = None
    any_time: bool = False
    day_only: bool = False
    style: str | None = None
    wait_real_hours: float | None = None
    wait_game_nights: int | None = None
    wait_manual: bool = False
    wait_victories: int | None = None


@dataclass(frozen=True)
class Pacing:
    cluster_beats: int = 3
    cluster_window_seconds: int = 45 * 60
    silence_seconds: int = 40 * 60 * 60
    # silence_hours may be authored as [min, max]; equal values = no jitter.
    silence_seconds_max: int = 40 * 60 * 60

    def required_silence_seconds(self, seed: object) -> int:
        return jittered_silence_seconds(
            self.silence_seconds, self.silence_seconds_max, seed=seed
        )


@dataclass(frozen=True)
class Chapter:
    id: str
    title: str
    tier: str
    beats: tuple[Beat, ...]
    # Per-chapter pacing override (accelerando, HD-1e): merged over the
    # campaign-level pacing at load time; None = use the campaign default.
    pacing: Pacing | None = None


@dataclass(frozen=True)
class Campaign:
    version: int
    pacing: Pacing
    pools: dict[str, tuple[str, ...]]
    dossier: dict[str, tuple[str, ...]]
    chapters: tuple[Chapter, ...]

    def chapter_index(self, ref: str) -> int | None:
        """1-based chapter index from a number or a chapter id, else None."""

        if re.fullmatch(r"[1-9][0-9]?", ref):
            index = int(ref)
            return index if 1 <= index <= len(self.chapters) else None
        for position, chapter in enumerate(self.chapters, start=1):
            if chapter.id == ref:
                return position
        return None


@dataclass(frozen=True)
class Progress:
    chapter: int = 0  # 1-based; 0 = not started; len(chapters)+1 = finished
    beat: int = 0  # 0-based index into the current chapter's beats
    auto: bool = False
    attempt: int = 0  # failed-delivery salt for the current beat's event id
    opened_at: int = 0  # when the current beat became current
    nights_at_open: int = 0


@dataclass(frozen=True)
class BeatOutcome:
    ok: bool
    advanced: bool
    message: str


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CampaignError(message)


def _line_list(value: object, where: str) -> tuple[str, ...]:
    _require(isinstance(value, list) and value, f"{where} must be a non-empty list")
    lines: list[str] = []
    for item in value:
        _require(
            isinstance(item, str) and 0 < len(item) <= MAX_LINE_LENGTH,
            f"{where} lines must be 1..{MAX_LINE_LENGTH} characters",
        )
        lines.append(item)
    return tuple(lines)


def _valid_target(value: object, where: str) -> str:
    _require(isinstance(value, str) and bool(value), f"{where} needs a target")
    assert isinstance(value, str)
    _require(
        value in TARGET_SELECTORS or bool(PLAYER_NAME_RE.fullmatch(value)),
        f"{where} target must be a player name, 'random' or 'last_victim'",
    )
    return value


def _parse_beat(raw: object, where: str) -> list[Beat]:
    """One YAML beat → one or more Beats (servant waves expand)."""

    _require(isinstance(raw, dict), f"{where} must be a mapping")
    assert isinstance(raw, dict)
    kind = raw.get("type")
    _require(kind in BEAT_TYPES, f"{where} has unknown type {kind!r}")
    label = str(raw.get("label", "") or f"{where}:{kind}")[:80]
    any_time = bool(raw.get("any_time", False))
    day_only = bool(raw.get("day_only", False))
    _require(
        not (any_time and day_only),
        f"{where} cannot be both any_time and day_only",
    )

    if kind == "scene":
        profile = raw.get("profile")
        _require(
            profile in CONTROL_SCENE_PROFILE_PHASES,
            f"{where} has unknown scene profile {profile!r}",
        )
        ttl = raw.get("ttl")
        if ttl is not None:
            _require(
                isinstance(ttl, int) and 1 <= ttl <= SCENE_MAX_TTL_TICKS,
                f"{where} ttl must be 1..{SCENE_MAX_TTL_TICKS} ticks",
            )
        return [
            Beat(
                "scene",
                label,
                profile=str(profile),
                target=_valid_target(raw.get("target"), where),
                ttl_ticks=ttl,
                any_time=any_time,
                day_only=day_only,
            )
        ]
    if kind == "whisper":
        line = raw.get("line")
        pool = raw.get("pool")
        _require(
            (line is None) != (pool is None),
            f"{where} needs exactly one of line/pool",
        )
        if line is not None:
            _require(
                isinstance(line, str) and 0 < len(line) <= MAX_LINE_LENGTH,
                f"{where} line must be 1..{MAX_LINE_LENGTH} characters",
            )
        else:
            _require(isinstance(pool, str) and bool(pool), f"{where} pool name")
        return [
            Beat(
                "whisper",
                label,
                target=_valid_target(raw.get("target"), where),
                line=line if isinstance(line, str) else None,
                pool=pool if isinstance(pool, str) else None,
                any_time=any_time,
                day_only=day_only,
            )
        ]
    if kind in {"global", "discord"}:
        line = raw.get("line")
        _require(
            isinstance(line, str) and 0 < len(line) <= MAX_LINE_LENGTH,
            f"{where} line must be 1..{MAX_LINE_LENGTH} characters",
        )
        style = raw.get("style")
        if kind == "global" and style is not None:
            _require(
                style in GLOBAL_STYLES,
                f"{where} style must be one of {'/'.join(GLOBAL_STYLES)}",
            )
        return [
            Beat(
                kind,
                label,
                line=str(line),
                any_time=any_time,
                day_only=day_only,
                style=str(style) if kind == "global" and style is not None else None,
            )
        ]
    if kind == "servant_wave":
        count = raw.get("count", 1)
        _require(
            isinstance(count, int) and 1 <= count <= MAX_SERVANT_WAVE,
            f"{where} count must be 1..{MAX_SERVANT_WAVE}",
        )
        target = _valid_target(raw.get("target", "random"), where)
        return [
            Beat("servant_wave", f"{label} ({n + 1}/{count})" if count > 1 else label,
                 target=target, any_time=any_time, day_only=day_only)
            for n in range(count)
        ]
    # wait
    keys = [k for k in ("real_hours", "game_nights", "manual", "victories") if k in raw]
    _require(len(keys) == 1, f"{where} wait needs exactly one condition")
    if "real_hours" in raw:
        hours = raw["real_hours"]
        _require(
            isinstance(hours, (int, float)) and 0 < float(hours) <= 24 * 30,
            f"{where} real_hours must be 0..720",
        )
        return [Beat("wait", label, wait_real_hours=float(hours))]
    if "game_nights" in raw:
        nights = raw["game_nights"]
        _require(
            isinstance(nights, int) and 1 <= nights <= 60,
            f"{where} game_nights must be 1..60",
        )
        return [Beat("wait", label, wait_game_nights=nights)]
    if "victories" in raw:
        victories = raw["victories"]
        _require(
            isinstance(victories, int) and 1 <= victories <= 100,
            f"{where} victories must be 1..100",
        )
        return [Beat("wait", label, wait_victories=victories)]
    _require(raw.get("manual") is True, f"{where} manual wait must be `manual: true`")
    return [Beat("wait", label, wait_manual=True)]


def _parse_silence_hours(value: object, where: str) -> tuple[int, int]:
    """A scalar or a [min, max] pair of hours → (seconds, seconds_max)."""

    if isinstance(value, list):
        _require(
            len(value) == 2
            and all(
                isinstance(item, (int, float)) and not isinstance(item, bool)
                for item in value
            ),
            f"{where}.silence_hours must be a number or [min, max] hours",
        )
        low, high = float(value[0]), float(value[1])
        _require(
            1 <= low <= high <= 240,
            f"{where}.silence_hours range must satisfy 1 <= min <= max <= 240",
        )
        return int(low * 3600), int(high * 3600)
    _require(
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and 1 <= float(value) <= 240,
        f"{where}.silence_hours must be 1..240",
    )
    seconds = int(float(value) * 3600)
    return seconds, seconds


def _parse_pacing(raw: object, where: str, base: Pacing | None) -> Pacing:
    """One pacing mapping; a chapter override merges over the campaign base."""

    _require(isinstance(raw, dict), f"{where} must be a mapping")
    assert isinstance(raw, dict)
    defaults = base or Pacing()
    cluster_beats = raw.get("cluster_beats", defaults.cluster_beats)
    window_minutes = raw.get(
        "cluster_window_minutes", defaults.cluster_window_seconds // 60
    )
    _require(
        isinstance(cluster_beats, int) and 1 <= cluster_beats <= 10,
        f"{where}.cluster_beats must be 1..10",
    )
    _require(
        isinstance(window_minutes, int) and 5 <= window_minutes <= 240,
        f"{where}.cluster_window_minutes must be 5..240",
    )
    if "silence_hours" in raw:
        silence_seconds, silence_seconds_max = _parse_silence_hours(
            raw["silence_hours"], where
        )
    else:
        silence_seconds = defaults.silence_seconds
        silence_seconds_max = defaults.silence_seconds_max
    return Pacing(
        cluster_beats, window_minutes * 60, silence_seconds, silence_seconds_max
    )


def load_campaign(path: str | Path) -> Campaign:
    """Parse and strictly validate the campaign file; fail closed on doubt."""

    source = Path(path)
    if not source.is_file():
        raise CampaignError(f"campaign file not found: {source}")
    try:
        document = yaml.safe_load(source.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise CampaignError(f"campaign file is not valid YAML: {exc}") from exc
    _require(isinstance(document, dict), "campaign root must be a mapping")
    _require(document.get("version") == 1, "campaign version must be 1")

    pacing = _parse_pacing(document.get("pacing", {}) or {}, "pacing", None)

    raw_pools = document.get("pools", {}) or {}
    _require(isinstance(raw_pools, dict), "pools must be a mapping")
    dossier_raw = raw_pools.get("dossier", {}) or {}
    _require(isinstance(dossier_raw, dict), "pools.dossier must be a mapping")
    dossier = {}
    for name, lines in dossier_raw.items():
        _require(
            bool(PLAYER_NAME_RE.fullmatch(str(name))),
            f"dossier key {name!r} is not a player name",
        )
        dossier[str(name)] = _line_list(lines, f"pools.dossier.{name}")
    pools = {
        str(name): _line_list(lines, f"pools.{name}")
        for name, lines in raw_pools.items()
        if name != "dossier"
    }
    _require("generic" in pools, "pools.generic is required")

    raw_chapters = document.get("chapters")
    _require(
        isinstance(raw_chapters, list) and raw_chapters,
        "chapters must be a non-empty list",
    )
    chapters: list[Chapter] = []
    seen_ids: set[str] = set()
    for position, raw_chapter in enumerate(raw_chapters, start=1):
        where = f"chapters[{position}]"
        _require(isinstance(raw_chapter, dict), f"{where} must be a mapping")
        chapter_id = raw_chapter.get("id")
        _require(
            isinstance(chapter_id, str)
            and bool(re.fullmatch(r"[a-z0-9_-]{1,24}", chapter_id)),
            f"{where}.id must be a short lowercase slug",
        )
        _require(chapter_id not in seen_ids, f"duplicate chapter id {chapter_id!r}")
        seen_ids.add(str(chapter_id))
        tier = raw_chapter.get("tier")
        _require(
            tier in CONTROL_PHASES and tier != "dormant",
            f"{where}.tier must be presence/servants/manifestation",
        )
        title = str(raw_chapter.get("title", chapter_id))[:60]
        raw_beats = raw_chapter.get("beats")
        _require(
            isinstance(raw_beats, list) and raw_beats,
            f"{where}.beats must be a non-empty list",
        )
        beats: list[Beat] = []
        for beat_position, raw_beat in enumerate(raw_beats, start=1):
            beats.extend(_parse_beat(raw_beat, f"{where}.beats[{beat_position}]"))
        chapter_pacing: Pacing | None = None
        if "pacing" in raw_chapter:
            chapter_pacing = _parse_pacing(
                raw_chapter["pacing"], f"{where}.pacing", pacing
            )
        chapters.append(
            Chapter(
                str(chapter_id), title, str(tier), tuple(beats),
                pacing=chapter_pacing,
            )
        )
    # `pool: dossier` whispers fall back to generic for unknown players, so a
    # dossier entry is optional per player; the file itself must stay valid.
    return Campaign(1, pacing, pools, dossier, tuple(chapters))


def _decode_progress(raw: str | None) -> Progress:
    if not raw:
        return Progress()
    try:
        data = json.loads(raw)
        return Progress(
            chapter=max(0, int(data.get("chapter", 0))),
            beat=max(0, int(data.get("beat", 0))),
            auto=bool(data.get("auto", False)),
            attempt=max(0, int(data.get("attempt", 0))),
            opened_at=max(0, int(data.get("opened_at", 0))),
            nights_at_open=max(0, int(data.get("nights_at_open", 0))),
        )
    except (TypeError, ValueError, json.JSONDecodeError):
        return Progress()


def _encode_progress(progress: Progress) -> str:
    return json.dumps(
        {
            "chapter": progress.chapter,
            "beat": progress.beat,
            "auto": progress.auto,
            "attempt": progress.attempt,
            "opened_at": progress.opened_at,
            "nights_at_open": progress.nights_at_open,
        },
        sort_keys=True,
        separators=(",", ":"),
    )


class CampaignEngine:
    """Progress bookkeeping plus beat execution over an injected executor.

    The executor contract (implemented over RCON in heraldor.py, faked in
    tests):
      online_players() -> list[str]
      is_night() -> bool
      scene(target, profile_argument, event_id, rehearsal) -> (bool|None, str)
      whisper(target, line) / global_line(line, style) -> bool
      discord(line) -> (bool|None, str)   # handles webhook+cooldown itself
      servant(target, live) -> (bool, str)
      notify(operator, text) -> None      # rehearsal previews
    """

    def __init__(self, campaign: Campaign, *, rng: random.Random | None = None):
        self.campaign = campaign
        self.rng = rng or random.Random()
        self._night_flags: dict[str, bool] = {}
        self._clamp_warned: set[tuple[str, int, int]] = set()

    # -- progress ----------------------------------------------------------

    def progress(self, store: DirectorStore, world_token: int | str) -> Progress:
        decoded = _decode_progress(store.campaign_progress_raw(world_token))
        return self._clamp_progress(world_token, decoded)

    def _clamp_progress(
        self, world_token: int | str, progress: Progress
    ) -> Progress:
        """H1: never trust a persisted pointer against an edited file.

        Every read clamps out-of-range chapter/beat values to the last valid
        beat (or `finished`) with a deduped WARN instead of letting a
        shortened campaign turn `story status`/`next` into daemon crashes.
        """

        total = len(self.campaign.chapters)
        chapter, beat = progress.chapter, progress.beat
        if chapter > total + 1:
            chapter, beat = total + 1, 0
        elif chapter == total + 1:
            beat = 0
        elif 1 <= chapter <= total:
            beat_count = len(self.campaign.chapters[chapter - 1].beats)
            if beat >= beat_count:
                beat = beat_count - 1
        else:
            beat = 0 if chapter == 0 else beat
        if (chapter, beat) == (progress.chapter, progress.beat):
            return progress
        key = (str(world_token), progress.chapter, progress.beat)
        if key not in self._clamp_warned:
            self._clamp_warned.add(key)
            print(
                "[heraldor] WARN: kampanya işaretçisi dosyanın dışında "
                f"(chapter {progress.chapter}, beat {progress.beat + 1}); "
                f"chapter {chapter}, beat {beat + 1} olarak kırpıldı — "
                "dosya kısalmış olabilir, `story status`/`story goto` ile doğrulayın"
            )
        return replace(progress, chapter=chapter, beat=beat)

    def _save(
        self,
        store: DirectorStore,
        world_token: int | str,
        progress: Progress,
        *,
        now: int,
    ) -> None:
        store.save_campaign_progress(
            world_token, _encode_progress(progress), now=now
        )

    def finished(self, progress: Progress) -> bool:
        return progress.chapter > len(self.campaign.chapters)

    def current(self, progress: Progress) -> tuple[Chapter, Beat] | None:
        if progress.chapter < 1 or self.finished(progress):
            return None
        chapter = self.campaign.chapters[progress.chapter - 1]
        if progress.beat >= len(chapter.beats):
            return None
        return chapter, chapter.beats[progress.beat]

    def _open_position(
        self,
        store: DirectorStore,
        world_token: int | str,
        progress: Progress,
        chapter: int,
        beat: int,
        *,
        now: int,
    ) -> Progress:
        """Move the pointer and promote the campaign tier on chapter entry."""

        moved = replace(
            progress,
            chapter=chapter,
            beat=beat,
            attempt=0,
            opened_at=now,
            nights_at_open=store.campaign_counter(
                CAMPAIGN_NIGHTS_META_PREFIX, world_token
            ),
        )
        if 1 <= chapter <= len(self.campaign.chapters):
            store.promote_campaign_tier(
                world_token, self.campaign.chapters[chapter - 1].tier, now=now
            )
        elif chapter > len(self.campaign.chapters):
            # The finale finished: servants retire permanently (HD-7a) and
            # the afterlife lane owns the silence until `story reset`.
            store.mark_campaign_completed(world_token, now=now)
        self._save(store, world_token, moved, now=now)
        return moved

    def _advance(
        self,
        store: DirectorStore,
        world_token: int | str,
        progress: Progress,
        *,
        now: int,
    ) -> Progress:
        chapter = self.campaign.chapters[progress.chapter - 1]
        if progress.beat + 1 < len(chapter.beats):
            return self._open_position(
                store, world_token, progress, progress.chapter, progress.beat + 1,
                now=now,
            )
        return self._open_position(
            store, world_token, progress, progress.chapter + 1, 0, now=now
        )

    # -- operator commands -------------------------------------------------

    def status_text(
        self, store: DirectorStore, world_token: int | str, *, now: int
    ) -> str:
        progress = self.progress(store, world_token)
        tier = store.campaign_state(world_token).phase
        nights = store.campaign_counter(CAMPAIGN_NIGHTS_META_PREFIX, world_token)
        victories = store.servant_high_water(world_token)
        if progress.chapter == 0:
            return (
                f"story: not started ({len(self.campaign.chapters)} chapters), "
                f"tier={tier}, victories={victories}"
            )
        if self.finished(progress):
            return f"story: finished, tier={tier}, victories={victories}"
        chapter = self.campaign.chapters[progress.chapter - 1]
        beat = chapter.beats[progress.beat]
        described = self.describe_beat(beat)
        wait_state = ""
        if beat.type == "wait":
            wait_state = f", waiting: {self._wait_hint(store, world_token, progress, beat, now=now)}"
        return (
            f"story: chapter {progress.chapter}/{len(self.campaign.chapters)} "
            f"'{chapter.title}' beat {progress.beat + 1}/{len(chapter.beats)} "
            f"[{described}], auto={'on' if progress.auto else 'off'}, "
            f"tier={tier}, nights={nights}, victories={victories}{wait_state}"
        )

    def describe_beat(self, beat: Beat) -> str:
        if beat.type == "scene":
            return f"scene {beat.profile} -> {beat.target}"
        if beat.type == "whisper":
            return f"whisper ({beat.pool or 'line'}) -> {beat.target}"
        if beat.type == "servant_wave":
            return f"servant -> {beat.target}"
        if beat.type == "wait":
            if beat.wait_manual:
                return "wait for `story next`"
            if beat.wait_real_hours is not None:
                return f"wait {beat.wait_real_hours:g} real hours"
            if beat.wait_game_nights is not None:
                return f"wait {beat.wait_game_nights} game nights"
            return f"wait for {beat.wait_victories} servant victories"
        return beat.type

    def start(
        self, store: DirectorStore, world_token: int | str, *, now: int
    ) -> BeatOutcome:
        progress = self.progress(store, world_token)
        if progress.chapter != 0:
            return BeatOutcome(False, False, "story already started; use status/goto/reset")
        self._open_position(store, world_token, progress, 1, 0, now=now)
        first = self.campaign.chapters[0]
        return BeatOutcome(
            True, True, f"story started at chapter 1 '{first.title}'"
        )

    def goto(
        self, store: DirectorStore, world_token: int | str, ref: str, *, now: int
    ) -> BeatOutcome:
        index = self.campaign.chapter_index(ref)
        if index is None:
            return BeatOutcome(False, False, f"unknown chapter: {ref}")
        progress = self.progress(store, world_token)
        self._open_position(store, world_token, progress, index, 0, now=now)
        chapter = self.campaign.chapters[index - 1]
        return BeatOutcome(
            True, True, f"story moved to chapter {index} '{chapter.title}'"
        )

    def reset(
        self, store: DirectorStore, world_token: int | str, *, now: int
    ) -> BeatOutcome:
        store.reset_campaign(world_token, now=now)
        return BeatOutcome(
            True, True,
            "story reset: campaign, tier, colossus and aftermath memory cleared",
        )

    def set_auto(
        self, store: DirectorStore, world_token: int | str, enabled: bool, *, now: int
    ) -> BeatOutcome:
        progress = self.progress(store, world_token)
        if enabled and progress.chapter == 0:
            return BeatOutcome(False, False, "start the story before `story auto on`")
        if progress.auto == enabled:
            return BeatOutcome(
                False, False, f"story auto is already {'on' if enabled else 'off'}"
            )
        self._save(store, world_token, replace(progress, auto=enabled), now=now)
        return BeatOutcome(
            True, False,
            "story auto on: beats advance by themselves (clustered nights, "
            "then silence)" if enabled else "story auto off: manual stepping only",
        )

    # -- waits, nights, pacing --------------------------------------------

    def observe_night(
        self, store: DirectorStore, world_token: int | str, night: bool
    ) -> None:
        """Count day→night edges per world for `game_nights` waits."""

        token = str(world_token)
        was_night = self._night_flags.get(token, night)
        self._night_flags[token] = night
        if night and not was_night:
            store.bump_campaign_counter(CAMPAIGN_NIGHTS_META_PREFIX, world_token)

    def _wait_met(
        self,
        store: DirectorStore,
        world_token: int | str,
        progress: Progress,
        beat: Beat,
        *,
        now: int,
    ) -> bool:
        if beat.wait_manual:
            return False
        if beat.wait_real_hours is not None:
            return now - progress.opened_at >= beat.wait_real_hours * 3600
        if beat.wait_game_nights is not None:
            nights = store.campaign_counter(CAMPAIGN_NIGHTS_META_PREFIX, world_token)
            return nights - progress.nights_at_open >= beat.wait_game_nights
        if beat.wait_victories is not None:
            return store.servant_high_water(world_token) >= beat.wait_victories
        return False

    def _wait_hint(
        self,
        store: DirectorStore,
        world_token: int | str,
        progress: Progress,
        beat: Beat,
        *,
        now: int,
    ) -> str:
        if beat.wait_manual:
            return "manual"
        if beat.wait_real_hours is not None:
            left = max(0, int(progress.opened_at + beat.wait_real_hours * 3600 - now))
            return f"{left // 3600}h{(left % 3600) // 60:02d}m left"
        if beat.wait_game_nights is not None:
            nights = store.campaign_counter(CAMPAIGN_NIGHTS_META_PREFIX, world_token)
            passed = nights - progress.nights_at_open
            return f"{passed}/{beat.wait_game_nights} nights"
        victories = store.servant_high_water(world_token)
        return f"{victories}/{beat.wait_victories} victories"

    def _effective_pacing(self, progress: Progress) -> Pacing:
        """The current chapter's pacing override, else the campaign default."""

        if 1 <= progress.chapter <= len(self.campaign.chapters):
            override = self.campaign.chapters[progress.chapter - 1].pacing
            if override is not None:
                return override
        return self.campaign.pacing

    def _pacing_allows(
        self,
        store: DirectorStore,
        world_token: int | str,
        progress: Progress,
        *,
        now: int,
    ) -> bool:
        """Clustered nights, then silence. Nothing fires two nights in a row
        after a cluster; a lone stray beat only needs a shorter gap. The
        required silence is jittered per gap when the file authors a range
        (HD-1c: a fixed interval is a forecastable interval)."""

        raw = store.campaign_cluster_raw(world_token)
        if not raw:
            return True
        try:
            data = json.loads(raw)
            count = int(data.get("count", 0))
            last_at = int(data.get("last_at", 0))
        except (TypeError, ValueError, json.JSONDecodeError):
            return True
        pacing = self._effective_pacing(progress)
        if now - last_at <= pacing.cluster_window_seconds:
            return count < pacing.cluster_beats
        silence = pacing.required_silence_seconds(f"{world_token}:{last_at}")
        required = silence if count >= 2 else min(silence, 12 * 3600)
        return now - last_at >= required

    def _record_cluster_beat(
        self,
        store: DirectorStore,
        world_token: int | str,
        progress: Progress,
        *,
        now: int,
    ) -> None:
        raw = store.campaign_cluster_raw(world_token)
        count, last_at = 0, 0
        if raw:
            try:
                data = json.loads(raw)
                count = int(data.get("count", 0))
                last_at = int(data.get("last_at", 0))
            except (TypeError, ValueError, json.JSONDecodeError):
                count, last_at = 0, 0
        window = self._effective_pacing(progress).cluster_window_seconds
        count = count + 1 if now - last_at <= window else 1
        store.save_campaign_cluster(
            world_token,
            json.dumps({"count": count, "last_at": now}, sort_keys=True,
                       separators=(",", ":")),
            now=now,
        )

    # -- targets and lines -------------------------------------------------

    def _resolve_target(
        self,
        store: DirectorStore,
        world_token: int | str,
        beat: Beat,
        online: list[str],
        *,
        manual: bool,
        now: int,
    ) -> tuple[str | None, str, dict[str, object]]:
        """Resolve the beat's target selector to an online player.

        Returns (target, hold-reason, payload-notes). Autonomous `random`
        picks honour the tenure gate (M1); a manual OP step bypasses it with
        a log. An offline `last_victim` falls back to a random eligible
        player (M3) instead of silently stalling the chain forever.
        """

        selector = beat.target or "random"
        safe_online = [name for name in online if PLAYER_NAME_RE.fullmatch(name)]

        def pick_random(reason_when_empty: str) -> tuple[str | None, str]:
            if not safe_online:
                return None, reason_when_empty
            if manual:
                choice = self.rng.choice(safe_online)
                if not store.subject_is_tenured(world_token, choice, now=now):
                    print(
                        "[heraldor] tenure gate bypassed by operator: "
                        f"{choice} has little recorded presence"
                    )
                return choice, ""
            eligible = store.tenured_subjects(world_token, safe_online, now=now)
            if not eligible:
                return None, "no tenured player is online (tenure gate)"
            return self.rng.choice(eligible), ""

        if selector == "random":
            target, reason = pick_random("no player is online")
            return target, reason, {}
        if selector == "last_victim":
            victim = store.last_directed_subject(world_token)
            if victim is None:
                return None, "no previous scene victim exists yet", {}
            for name in safe_online:
                if name.casefold() == victim:
                    return name, "", {}
            # M3: the victim is gone; the story falls back instead of
            # stalling the chain silently until an operator notices.
            fallback, reason = pick_random("no player is online")
            if fallback is None:
                return (
                    None,
                    f"last victim {victim} is offline and {reason}",
                    {},
                )
            print(
                f"[heraldor] kampanya: last_victim {victim} çevrimdışı; "
                f"rastgele hedefe düşüldü: {fallback}"
            )
            return fallback, "", {"target_fallback": "last_victim_offline"}
        for name in safe_online:
            if name.casefold() == selector.casefold():
                return name, "", {}
        return None, f"target {selector} is offline", {}

    def _pick_line(self, beat: Beat, target: str, event_id: str) -> str:
        if beat.line is not None:
            return beat.line
        seeded = random.Random(event_id)
        if beat.pool == "dossier":
            lines = self.campaign.dossier.get(target) or self.campaign.pools["generic"]
        else:
            lines = self.campaign.pools.get(beat.pool or "generic") or (
                self.campaign.pools["generic"]
            )
        return seeded.choice(list(lines))

    # -- execution ---------------------------------------------------------

    @staticmethod
    def _beat_event_id(
        world_token: int | str,
        progress: Progress,
        *,
        rehearsal: bool,
        generation: int = 0,
    ) -> str:
        if rehearsal:
            return str(uuid.uuid4())
        # L4: the reset generation salts season-2 ids so a replayed beat
        # position never collides with season 1's delivered rows. Generation
        # 0 keeps the historical seed for worlds that never reset.
        if generation:
            seed = (
                f"campaign:{world_token}:gen{generation}:{progress.chapter}:"
                f"{progress.beat}:{progress.attempt}"
            )
        else:
            seed = (
                f"campaign:{world_token}:{progress.chapter}:{progress.beat}:"
                f"{progress.attempt}"
            )
        # A UUID both satisfies the runtime's strict UuidArgument and gives
        # the runtime-side ledger the same at-most-once key on retries.
        return str(uuid.uuid5(CONTROL_EVENT_NAMESPACE, seed))

    def execute_current_beat(
        self,
        store: DirectorStore,
        world_token: int | str,
        executor,
        *,
        operator: str,
        rehearsal: bool,
        manual: bool,
        now: int,
    ) -> BeatOutcome:
        progress = self.progress(store, world_token)
        if progress.chapter == 0:
            return BeatOutcome(False, False, "story has not started; use `story start`")
        if self.finished(progress):
            return BeatOutcome(False, False, "story is finished; use `story reset` or `story goto`")
        position = self.current(progress)
        assert position is not None
        chapter, beat = position

        if beat.type == "wait":
            if rehearsal:
                return BeatOutcome(
                    True, False, f"next beat is a wait: {self.describe_beat(beat)}"
                )
            if manual or self._wait_met(store, world_token, progress, beat, now=now):
                moved = self._advance(store, world_token, progress, now=now)
                return BeatOutcome(
                    True, True,
                    f"wait {'skipped' if manual else 'satisfied'}; "
                    + self._position_text(moved),
                )
            return BeatOutcome(
                False, False,
                f"still waiting: {self._wait_hint(store, world_token, progress, beat, now=now)}",
            )

        if beat.type == "servant_wave" and not rehearsal and store.campaign_completed(
            world_token
        ):
            # HD-7a: servants retire permanently once the finale has played.
            # Rehearsals stay legal; `story reset` starts a sanctioned season 2.
            return BeatOutcome(
                False, False,
                "servants are retired after the finale; `story reset` starts "
                "a new season",
            )

        target: str | None = None
        target_notes: dict[str, object] = {}
        if beat.type in {"scene", "whisper", "servant_wave"}:
            target, reason, target_notes = self._resolve_target(
                store, world_token, beat, executor.online_players(),
                manual=manual, now=now,
            )
            if target is None:
                return BeatOutcome(False, False, f"beat is not ready: {reason}")

        generation = store.campaign_counter(
            CAMPAIGN_GENERATION_META_PREFIX, world_token
        )
        event_id = self._beat_event_id(
            world_token, progress, rehearsal=rehearsal, generation=generation
        )
        payload: dict[str, object] = {
            "world_token": str(world_token),
            "planner": "campaign",
            "chapter": chapter.id,
            "beat": progress.beat,
            "label": beat.label,
            "beat_type": beat.type,
            "operator": operator,
        }
        payload.update(target_notes)
        if target is not None:
            payload["target"] = target
        line: str | None = None
        style: str | None = None
        if beat.type in {"whisper", "global", "discord"}:
            line = self._pick_line(beat, target or "", event_id)
            payload["line"] = line
        if beat.type == "global":
            style = beat.style or GLOBAL_STYLE_BY_TIER.get(chapter.tier, "named")
            payload["style"] = style
        if beat.type == "scene":
            payload["profile"] = beat.profile
            payload["runtime_event_id"] = event_id
            if beat.ttl_ticks is not None:
                payload["ttl_ticks"] = beat.ttl_ticks

        if rehearsal:
            return self._rehearse_beat(executor, beat, target, line, operator, event_id)

        if not store.reserve_campaign_beat(
            event_id,
            kind=f"campaign_{beat.type}",
            subject=target,
            payload=payload,
            now=now,
        ):
            # The exact beat attempt was already reserved once (e.g. crash
            # between reserve and terminal state). Salt the next try.
            self._save(
                store, world_token, replace(progress, attempt=progress.attempt + 1),
                now=now,
            )
            return BeatOutcome(
                False, False, "beat attempt was already recorded; try again"
            )
        if not store.mark_attempting(event_id, now=now):
            return BeatOutcome(False, False, "beat could not be claimed")

        delivered: bool | None
        detail = ""
        try:
            if beat.type == "scene":
                assert target is not None and beat.profile is not None
                delivered, detail = executor.scene(
                    target, beat.profile, event_id, False, beat.ttl_ticks
                )
            elif beat.type == "whisper":
                assert target is not None and line is not None
                delivered = bool(executor.whisper(target, line))
            elif beat.type == "global":
                assert line is not None
                delivered = bool(executor.global_line(line, style or "named"))
            elif beat.type == "discord":
                assert line is not None
                delivered, detail = executor.discord(line)
            else:
                assert target is not None
                ok, detail = executor.servant(target, True)
                delivered = bool(ok)
        except Exception as exc:  # transport uncertainty is never a retry
            delivered = None
            detail = str(exc)

        store.finish_attempt(
            event_id,
            delivered=delivered,
            error=None if delivered else (detail or None),
            now=now,
        )
        if delivered or delivered is None:
            moved = self._advance(store, world_token, progress, now=now)
            if not manual:
                self._record_cluster_beat(store, world_token, progress, now=now)
            state = "delivered" if delivered else "uncertain; not replayed"
            return BeatOutcome(
                True, True,
                f"beat '{beat.label}' {state}; " + self._position_text(moved),
            )
        self._save(
            store, world_token, replace(progress, attempt=progress.attempt + 1),
            now=now,
        )
        return BeatOutcome(
            False, False, f"beat '{beat.label}' failed: {detail or 'unknown'}"
        )

    def _rehearse_beat(
        self,
        executor,
        beat: Beat,
        target: str | None,
        line: str | None,
        operator: str,
        event_id: str,
    ) -> BeatOutcome:
        """Zero state writes: play what can be played, preview the rest."""

        if beat.type == "scene":
            assert target is not None and beat.profile is not None
            delivered, detail = executor.scene(target, beat.profile, event_id, True)
            if delivered:
                return BeatOutcome(
                    True, False, f"rehearsed scene {beat.profile} for {target}"
                )
            return BeatOutcome(False, False, f"scene rehearsal failed: {detail}")
        if beat.type == "servant_wave":
            assert target is not None
            ok, detail = executor.servant(target, False)
            if ok:
                return BeatOutcome(
                    True, False, f"rehearsed servant encounter for {target}"
                )
            return BeatOutcome(False, False, f"servant rehearsal failed: {detail}")
        preview = {
            "whisper": f"would whisper to {target}: {line}",
            "global": f"would announce: {line}",
            "discord": f"would post to Discord: {line}",
        }[beat.type]
        executor.notify(operator, preview)
        return BeatOutcome(True, False, preview)

    def _position_text(self, progress: Progress) -> str:
        if self.finished(progress):
            return "story is now finished"
        chapter = self.campaign.chapters[progress.chapter - 1]
        beat = chapter.beats[progress.beat]
        return (
            f"next: chapter {progress.chapter} '{chapter.title}' "
            f"beat {progress.beat + 1} [{self.describe_beat(beat)}]"
        )

    # -- autonomy ----------------------------------------------------------

    def autonomous_tick(
        self,
        store: DirectorStore,
        world_token: int | str,
        executor,
        *,
        now: int,
    ) -> str | None:
        """Advance at most one thing. Waits resolve freely; actionable beats
        respect night preference and the quiet-cluster pacing."""

        progress = self.progress(store, world_token)
        if progress.chapter == 0 or self.finished(progress):
            return None
        # Nights are counted whenever the story is running, so `game_nights`
        # waits and `story status` stay truthful even in manual mode.
        night = bool(executor.is_night())
        self.observe_night(store, world_token, night)
        if not progress.auto:
            return None
        position = self.current(progress)
        if position is None:
            return None
        _chapter, beat = position

        if beat.type == "wait":
            if self._wait_met(store, world_token, progress, beat, now=now):
                self._advance(store, world_token, progress, now=now)
                return f"wait satisfied: {beat.label}"
            return None

        if beat.day_only:
            # HD-5d: a deliberate daylight beat waits for actual daylight —
            # the one-per-season "the rules you inferred were yours" moment.
            if night:
                return None
        elif not beat.any_time and not night:
            return None
        if not self._pacing_allows(store, world_token, progress, now=now):
            return None
        outcome = self.execute_current_beat(
            store,
            world_token,
            executor,
            operator="campaign",
            rehearsal=False,
            manual=False,
            now=now,
        )
        return outcome.message if outcome.advanced else None
