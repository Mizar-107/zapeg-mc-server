#!/usr/bin/env python3
"""
Heraldor — ZapeG'in karanlık varlığı (v2: persistent director).

Herobrine türü bir varlık ama bizimki: adı Heraldor. Kimse ondan bahsetmez,
o herkesi izler. Bu servis rastgele ve NADİR olaylar üretir:

  whisper  — rastgele bir oyuncuya, sadece onun gördüğü fısıltı (+ ürkütücü ses)
  global   — herkese kısa, şifreli bir cümle (çok nadir)
  discord  — Discord kanalına imzasız/tekinsiz mesaj (webhook; en nadiri)
  shadows  — [VARSAYILAN KAPALI] gece yarısı, rastgele bir oyuncunun yanına
             30 saniyeliğine "Heraldor'un Gölgesi" adlı 3 vex (kendiliğinden yok
             olur — korkutur, eşya/ev zararı yok)

KubeJS'in gizli skor tahtasındaki ``Heraldor'un Hizmetkârı`` zaferleri ayrıca
izlenir. SQLite yüksek-su işareti ve tek-seferlik hikâye bayrağı sayesinde
yeniden başlatmalar aynı eşiği tekrar çalıştırmaz.

Gece (oyun saati 13000–23000) fısıltı olasılığı 3 katına çıkar. Satırlar
gömülü havuzlardan ve kampanya dosyasından gelir; LLM yolu kaldırıldı.
Asla oyuncu girdisi komut olarak çalıştırılmaz.

Hikâye sürüşü: npc/campaign-heraldor.yml + /zapeg-lore story komutları
(heraldor_campaign.py). Kampanya birincil sürücüdür; eski faz ağacı tek
katman kampanya durumuna indirildi.
"""
import argparse
import json
import os
import random
import re
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from mcrcon import MCRcon

from heraldor_campaign import CampaignEngine, CampaignError, load_campaign
from heraldor_director import (
    COLOSSUS_PROFILE,
    CONTROL_SCENE_PROFILE_PHASES,
    CONTROL_TOKEN_MAX_FUTURE_SECONDS,
    MANUAL_DISCORD_MIN_GAP_SECONDS,
    SCENE_RUNTIME_DISPATCH,
    STALK_HINT_PROFILES,
    ControlRequest,
    DirectorStateLock,
    DirectorStore,
    Reservation,
    effective_scene_phase,
    resolve_scene_dispatch,
    extract_control_request_token,
    parse_control_request,
    parse_death_site,
    parse_last_minion_kill,
    parse_pos_output,
    parse_score_output,
    restore_snapshot,
    scene_ttl_ticks,
)

RCON_HOST = os.environ.get("RCON_HOST", "mc")
RCON_PORT = int(os.environ.get("RCON_PORT", "25575"))
RCON_PASSWORD_OVERRIDE = os.environ.get("RCON_PASSWORD", "").strip()
RCON_ENV_FILE = Path(os.environ.get("RCON_ENV_FILE", "/run/secrets/mc-rcon.env"))
WEBHOOK = os.environ.get("HERALDOR_WEBHOOK", "").strip()
EVENTS = os.environ.get("HERALDOR_EVENTS", "false").lower() == "true"
VOICE_ENABLED = os.environ.get("HERALDOR_VOICE_ENABLED", "false").lower() == "true"
CHECK_INTERVAL = max(10, int(os.environ.get("CHECK_INTERVAL", "300")))
MINION_POLL_INTERVAL = max(5, int(os.environ.get("MINION_POLL_INTERVAL", "10")))
CONTROL_POLL_INTERVAL = max(1, int(os.environ.get("CONTROL_POLL_INTERVAL", "2")))
# Otonom sahne planlayıcısı (gece nöbetleri) varsayılan KAPALI; sahibi açar.
SCHEDULER_ENABLED = os.environ.get("HERALDOR_SCENE_SCHEDULER", "false").lower() == "true"
SCHEDULER_INTERVAL = max(20, int(os.environ.get("SCHEDULER_INTERVAL", "60")))
STALK_SAMPLE_INTERVAL = max(15, int(os.environ.get("STALK_SAMPLE_INTERVAL", "45")))
DEATH_POLL_INTERVAL = max(10, int(os.environ.get("DEATH_POLL_INTERVAL", "30")))
# In-game "discord whisper" bridge action: one world-tokened cooldown so the
# channel can never be spammed, even by an enthusiastic operator.
DISCORD_MANUAL_GAP_SECONDS = max(
    30,
    int(
        os.environ.get(
            "HERALDOR_DISCORD_MANUAL_GAP_SECONDS", str(MANUAL_DISCORD_MIN_GAP_SECONDS)
        )
    ),
)
DB_PATH = Path(os.environ.get("HERALDOR_DB_PATH", "/state/heraldor.sqlite3"))
SNAPSHOT_PATH = Path(
    os.environ.get("HERALDOR_SNAPSHOT_PATH", "/state/backup/heraldor.sqlite3")
)
CAMPAIGN_PATH = Path(
    os.environ.get(
        "HERALDOR_CAMPAIGN_PATH",
        str(Path(__file__).resolve().parent / "campaign-heraldor.yml"),
    )
)
SERVANT_OBJECTIVE = "zapeg_hsvc"
SERVANT_SCORE_HOLDER = "#total"
SERVANT_WORLD_OBJECTIVE = "zh_svc_world"
SERVANT_WORLD_HOLDER = "#world"
DEATH_OBJECTIVE = "zh_death"
PLAYER_NAME_RE = re.compile(r"^[A-Za-z0-9_]{1,16}$")
CONTROL_STORAGE = "zapeg:heraldor"


@dataclass(frozen=True)
class ControlOutcome:
    event_id: str
    status: str
    message: str

# Olasılıklar: her CHECK_INTERVAL'da zar atılır (gündüz değerleri)
P_WHISPER = float(os.environ.get("P_WHISPER", "0.002"))
P_GLOBAL = float(os.environ.get("P_GLOBAL", "0.0005"))
P_DISCORD = float(os.environ.get("P_DISCORD", "0.0003"))
P_SHADOWS = float(os.environ.get("P_SHADOWS", "0.0002"))

WHISPERS = [
    "arkana bakma.",
    "kazma sesini duyuyorum. hep duyuyorum.",
    "o meşaleyi ben söndürmedim.",
    "burayı kazmamalıydın.",
    "yalnız değilsin. hiç olmadın.",
    "gölgen benim yanımda kalıyor artık.",
    "kapıyı açık bıraktın.",
    "yatağın soğuk. benimki gibi.",
    "adımı söyleme.",
    "seni sayıyorum.",
]

GLOBALS_ = [
    "O kule benimdi.",
    "Kaybettiğiniz her eşya bana geliyor.",
    "Kaç kişi olduğunuzu saydım. Bir fazla çıktık.",
    "Beni hatırlayanlar artık uyumuyor.",
    "Işıklarınız güzelmiş. Şimdilik.",
    "Uyuyunca daha sessiz oluyorsunuz.",
]

DISCORDS = [
    "sunucu hiç kapanmıyor sanıyorsunuz. ben hiç uyumuyorum.",
    "birinizin gölgesi kendisinden önce geldi.",
    "bu kanalı da görüyorum.",
    "biriniz bu gece geç saate kadar oynayacak. biliyorum.",
    "🕯",
]

OBFUS = "kelimeler kayboluyor"  # §k ile bozulan kısım


def rcon_password() -> str:
    """Explicit override, otherwise the live secret generated by itzg/mc."""
    if RCON_PASSWORD_OVERRIDE:
        return RCON_PASSWORD_OVERRIDE
    try:
        for raw in RCON_ENV_FILE.read_text(encoding="utf-8").splitlines():
            key, sep, value = raw.partition("=")
            if sep and key.strip() == "password" and value.strip():
                return value.strip().strip("\"'")
    except OSError as exc:
        raise RuntimeError(f"RCON parola dosyası okunamadı: {RCON_ENV_FILE}") from exc
    raise RuntimeError(f"RCON parolası bulunamadı: {RCON_ENV_FILE}")


def rcon_many(commands: list[str]) -> list[str]:
    with MCRcon(RCON_HOST, rcon_password(), port=RCON_PORT) as r:
        return [r.command(command) for command in commands]


def rcon(cmd: str) -> str:
    return rcon_many([cmd])[0]


def online_players() -> list:
    try:
        out = rcon("list")
        if ":" in out:
            names = out.split(":", 1)[1].strip()
            return [
                name
                for raw in names.split(",")
                if (name := raw.strip()) and PLAYER_NAME_RE.fullmatch(name)
            ]
    except Exception as e:
        print(f"[heraldor] list hata: {e}")
    return []


def is_night() -> bool:
    try:
        out = rcon("time query daytime")  # "The time is 14500"
        t = int("".join(ch for ch in out if ch.isdigit()) or 0)
        return 13000 <= t <= 23000
    except Exception:
        return False


def _control_event_shape(request: ControlRequest) -> tuple[str, str, bool]:
    if request.action in {"scene_rehearse", "scene_trigger"}:
        return "director_scene", "directed", request.action == "scene_rehearse"
    if request.action == "cancel":
        return "director_cancel", "operator", False
    if request.action == "discord_post":
        return "director_discord", "operator", False
    if request.action == "voice_rehearse":
        return "director_voice_rehearse", "operator", False
    return "director_story", "operator", False


def _reject_control(
    director: DirectorStore,
    request: ControlRequest,
    reason: str,
    *,
    status: str = "rejected",
    now: int,
) -> ControlOutcome:
    kind, category, rehearsal = _control_event_shape(request)
    existing = director.control_event_status(request.event_id)
    if existing == "reserved":
        director.finish_reserved_control(
            request.event_id, status=status, error=reason, now=now
        )
    elif existing is None:
        director.record_control_event(
            request,
            kind=kind,
            category=category,
            status=status,
            subject=request.target,
            rehearsal=rehearsal,
            error=reason,
            now=now,
        )
    terminal = director.control_event_status(request.event_id) or status
    return ControlOutcome(request.event_id, terminal, reason)


def process_control_request(
    director: DirectorStore,
    request: ControlRequest,
    *,
    observed_world_token: int | str,
    now: int | None = None,
) -> ControlOutcome:
    """Validate, persist and execute one strict high-level Director request."""

    timestamp = int(director.clock() if now is None else now)
    existing = director.control_event_status(request.event_id)
    if existing == "attempting":
        # A single daemon owns the state lock, so an attempt found at the start
        # of a later mailbox poll is an unresolved prior call, never concurrent.
        director.finish_attempt(
            request.event_id,
            delivered=None,
            error="prior control attempt ended without a terminal result",
            now=timestamp,
        )
        existing = director.control_event_status(request.event_id)
    if existing and existing != "reserved":
        # Retry a previously failed snapshot write before acknowledging and
        # removing the exact mailbox value.
        director.backup_snapshot()
        return ControlOutcome(
            request.event_id,
            existing,
            f"request already {existing}; it was not replayed",
        )
    if request.expires_at <= timestamp:
        return _reject_control(
            director,
            request,
            "request expired before the Director accepted it",
            status="suppressed_expired",
            now=timestamp,
        )
    if request.expires_at > timestamp + CONTROL_TOKEN_MAX_FUTURE_SECONDS:
        return _reject_control(
            director,
            request,
            "request expiry is outside the allowed window",
            now=timestamp,
        )
    if str(observed_world_token) != request.world_token:
        return _reject_control(
            director,
            request,
            "request belongs to a different Minecraft world",
            now=timestamp,
        )

    state = director.campaign_state(request.world_token)
    kind, category, rehearsal = _control_event_shape(request)

    if request.action == "story":
        return process_story_request(director, request, timestamp)

    if request.action == "voice_rehearse":
        # The in-game equivalent of host-side `admin voice-rehearse`: it only
        # ever queues a test-channel rehearsal; live voice stays governed by
        # its own gates. Rehearsals never advance story state.
        audio_event_id = director.enqueue_audio_rehearsal(now=timestamp)
        record = director.record_control_event(
            request,
            kind=kind,
            category=category,
            status="delivered",
            payload={"audio_event_id": audio_event_id, "rehearsal_only": True},
            now=timestamp,
        )
        return ControlOutcome(
            record.event_id,
            record.status,
            "voice rehearsal queued; it can only play in the test channel",
        )

    if request.action == "discord_post":
        # One-way webhook whisper as "Heraldor": fail-closed without a
        # configured webhook, paced by a world-tokened cooldown, and the
        # posted line is audited in the control event payload.
        if not WEBHOOK:
            return _reject_control(
                director,
                request,
                "Discord webhook is not configured",
                now=timestamp,
            )
        remaining = director.manual_discord_cooldown_remaining(
            request.world_token,
            gap_seconds=DISCORD_MANUAL_GAP_SECONDS,
            now=timestamp,
        )
        if remaining > 0:
            return _reject_control(
                director,
                request,
                f"Discord whisper is on cooldown for {remaining}s",
                now=timestamp,
            )
        # The nonce seeds the line, so a replayed token can never pick a
        # different message than the one already audited.
        line = DISCORDS[int(request.nonce, 16) % len(DISCORDS)]
        record = director.record_control_event(
            request,
            kind=kind,
            category=category,
            status="reserved",
            payload={"line": line},
            now=timestamp,
        )
        if record.status != "reserved":
            return ControlOutcome(
                record.event_id,
                record.status,
                f"request already {record.status}; it was not replayed",
            )
        if not director.mark_attempting(record.event_id, now=timestamp):
            terminal = director.control_event_status(record.event_id) or "ambiguous"
            return ControlOutcome(record.event_id, terminal, "request could not be claimed")
        try:
            discord_post_line(line)
        except Exception as exc:
            error = f"Discord post outcome was uncertain: {exc}"
            director.finish_attempt(record.event_id, delivered=None, error=error)
            return ControlOutcome(record.event_id, "ambiguous", error)
        director.finish_attempt(record.event_id, delivered=True, error=None)
        director.record_manual_discord_post(request.world_token, now=timestamp)
        return ControlOutcome(record.event_id, "delivered", "Discord whisper posted")

    # OP story drive: rehearse and trigger are usable immediately, including
    # from dormant. A delivered live trigger raises the stored campaign tier
    # to the profile's floor; rehearsals never touch any state.

    payload: dict[str, object] = {}
    command = "zapegscene cancel-all"
    if request.action in {"scene_rehearse", "scene_trigger"}:
        command, payload = build_scene_command(
            director,
            action=request.action,
            world_token=request.world_token,
            target=request.target or "",
            profile_argument=request.argument,
            event_id=request.event_id,
            phase=state.phase,
        )
    record = director.record_control_event(
        request,
        kind=kind,
        category=category,
        status="reserved",
        payload=payload,
        subject=request.target,
        rehearsal=rehearsal,
        now=timestamp,
    )
    if record.status != "reserved":
        return ControlOutcome(
            record.event_id,
            record.status,
            f"request already {record.status}; it was not replayed",
        )
    if not director.mark_attempting(record.event_id, now=timestamp):
        terminal = director.control_event_status(record.event_id) or "ambiguous"
        return ControlOutcome(record.event_id, terminal, "request could not be claimed")

    try:
        output = str(rcon(command)).strip()
    except Exception as exc:
        error = f"runtime response was uncertain: {exc}"
        director.finish_attempt(record.event_id, delivered=None, error=error)
        return ControlOutcome(record.event_id, "ambiguous", error)

    success = (
        output.startswith("scene dispatched event=")
        if request.action != "cancel"
        else output in {"scene cancelled", "active=0"}
    )
    director.finish_attempt(
        record.event_id,
        delivered=success,
        error=None if success else f"runtime rejected request: {output}",
    )
    if success:
        if request.action == "scene_trigger" and request.target:
            record_delivered_live_scene(
                director, request.world_token, request.argument, request.target
            )
        return ControlOutcome(record.event_id, "delivered", output)
    return ControlOutcome(
        record.event_id, "failed", f"runtime rejected request: {output[:180]}"
    )


def build_scene_command(
    director: DirectorStore,
    *,
    action: str,
    world_token: int | str,
    target: str,
    profile_argument: str,
    event_id: str,
    phase: str,
    ttl_override: int | None = None,
) -> tuple[str, dict[str, object]]:
    """One `/zapegscene` builder shared by the OP bridge and campaign beats.

    Handles alias→family stage dispatch, the colossus's stored stage (read
    here, advanced only after delivery), phase-scaled TTLs and the optional
    stalking-memory anchor hint (staged commands cannot carry a hint).
    """

    runtime_profile, alias_stage = resolve_scene_dispatch(profile_argument)
    payload: dict[str, object] = {
        "profile": profile_argument,
        "target": target,
        "runtime_profile": runtime_profile,
    }
    dispatch_stage: int | None = None
    if profile_argument == COLOSSUS_PROFILE and target:
        stage = director.colossus_stage(world_token, target)
        payload["colossus_stage"] = stage
        dispatch_stage = stage
    elif profile_argument in SCENE_RUNTIME_DISPATCH:
        dispatch_stage = alias_stage
        payload["scene_stage"] = alias_stage

    if action == "scene_rehearse":
        payload["runtime_event_id_policy"] = "runtime_generated"
        command = f"zapegscene rehearse {target} {runtime_profile}"
        if dispatch_stage is not None:
            command += f" {dispatch_stage}"
        return command, payload

    ttl_ticks = ttl_override or scene_ttl_ticks(
        runtime_profile, effective_scene_phase(phase, profile_argument)
    )
    payload["runtime_event_id"] = event_id
    scene_hint: tuple[int, int] | None = None
    if dispatch_stage is None and runtime_profile in STALK_HINT_PROFILES and target:
        scene_hint = director.stalk_hint(world_token, target)
        if scene_hint is not None:
            payload["hint_x"] = scene_hint[0]
            payload["hint_z"] = scene_hint[1]
    if dispatch_stage is not None:
        command = (
            f"zapegscene trigger {target} {event_id} "
            f"{runtime_profile} stage {dispatch_stage} {ttl_ticks}"
        )
    else:
        command = (
            f"zapegscene trigger {target} {event_id} {runtime_profile} {ttl_ticks}"
        )
        if scene_hint is not None:
            command += f" {scene_hint[0]} {scene_hint[1]}"
    return command, payload


def record_delivered_live_scene(
    director: DirectorStore,
    world_token: int | str,
    profile_argument: str,
    target: str,
) -> None:
    """Post-delivery campaign memory: tier floor and the colossus approach."""

    if profile_argument == COLOSSUS_PROFILE:
        # Only a delivered live trigger brings it closer; rehearsals and
        # rejected dispatches leave the stored stage untouched.
        director.advance_colossus_stage(world_token, target)
    floor = CONTROL_SCENE_PROFILE_PHASES.get(profile_argument)
    if floor:
        director.promote_campaign_tier(world_token, floor)


class CampaignRuntime:
    """The loaded campaign file, or the exact reason it failed to load."""

    def __init__(self, path: Path = CAMPAIGN_PATH) -> None:
        self.path = path
        self.engine: CampaignEngine | None = None
        self.load_error: str | None = None
        try:
            self.engine = CampaignEngine(load_campaign(path))
        except CampaignError as exc:
            self.load_error = str(exc)
            print(f"[heraldor] kampanya dosyası geçersiz; hikâye kapalı: {exc}")


_CAMPAIGN: CampaignRuntime | None = None


def campaign_runtime() -> CampaignRuntime:
    global _CAMPAIGN
    if _CAMPAIGN is None:
        _CAMPAIGN = CampaignRuntime()
    return _CAMPAIGN


class RconCampaignExecutor:
    """Campaign beat side effects over RCON; the engine stays transport-free."""

    def __init__(self, director: DirectorStore, world_token: int | str) -> None:
        self.director = director
        self.world_token = world_token

    def online_players(self) -> list:
        return online_players()

    def is_night(self) -> bool:
        return is_night()

    def scene(
        self,
        target: str,
        profile_argument: str,
        event_id: str,
        rehearsal: bool,
        ttl_override: int | None = None,
    ) -> tuple[bool | None, str]:
        phase = self.director.campaign_state(self.world_token).phase
        command, _payload = build_scene_command(
            self.director,
            action="scene_rehearse" if rehearsal else "scene_trigger",
            world_token=self.world_token,
            target=target,
            profile_argument=profile_argument,
            event_id=event_id,
            phase=phase,
            ttl_override=ttl_override,
        )
        try:
            output = str(rcon(command)).strip()
        except Exception as exc:
            return None, f"runtime response was uncertain: {exc}"
        success = output.startswith("scene dispatched event=")
        if success and not rehearsal:
            record_delivered_live_scene(
                self.director, self.world_token, profile_argument, target
            )
        return success, output

    def whisper(self, target: str, line: str) -> bool:
        whisper(target, line)
        return True

    def global_line(self, line: str) -> bool:
        global_msg(line)
        return True

    def discord(self, line: str) -> tuple[bool | None, str]:
        if not WEBHOOK:
            return False, "Discord webhook is not configured"
        remaining = self.director.manual_discord_cooldown_remaining(
            self.world_token, gap_seconds=DISCORD_MANUAL_GAP_SECONDS
        )
        if remaining > 0:
            return False, f"Discord whisper is on cooldown for {remaining}s"
        try:
            discord_post_line(line)
        except Exception as exc:
            return None, f"Discord post outcome was uncertain: {exc}"
        self.director.record_manual_discord_post(self.world_token)
        return True, ""

    def servant(self, target: str, live: bool) -> tuple[bool, str]:
        mode = "awaken" if live else "rehearse"
        output = str(rcon(f"zapeg-lore servant {mode} {target}")).strip()
        return output.startswith("Awakened"), output

    def notify(self, operator: str, text: str) -> None:
        message = f"[Heraldor] {text}"
        if operator == "console" or not PLAYER_NAME_RE.fullmatch(operator):
            print(f"[heraldor] {message}")
            return
        payload = json.dumps({"text": message, "color": "gray"}, ensure_ascii=False)
        try:
            rcon(f"tellraw {operator} {payload}")
        except Exception as exc:
            print(f"[heraldor] prova önizlemesi iletilemedi: {exc}")


def process_story_request(
    director: DirectorStore, request: ControlRequest, timestamp: int
) -> ControlOutcome:
    """`/zapeg-lore story …`: the single campaign control surface."""

    kind, category, _rehearsal = _control_event_shape(request)
    runtime = campaign_runtime()
    if runtime.engine is None:
        return _reject_control(
            director,
            request,
            f"campaign file is invalid: {runtime.load_error}",
            now=timestamp,
        )
    engine = runtime.engine
    world = request.world_token
    subcommand = request.argument

    if subcommand == "status":
        message = engine.status_text(director, world, now=timestamp)
        record = director.record_control_event(
            request,
            kind=kind,
            category=category,
            status="delivered",
            payload={"story": "status"},
            now=timestamp,
        )
        return ControlOutcome(record.event_id, record.status, message)

    if subcommand in {"start", "goto", "reset", "auto_on", "auto_off"}:
        if subcommand == "start":
            outcome = engine.start(director, world, now=timestamp)
        elif subcommand == "goto":
            outcome = engine.goto(director, world, request.target or "", now=timestamp)
        elif subcommand == "reset":
            outcome = engine.reset(director, world, now=timestamp)
        else:
            outcome = engine.set_auto(
                director, world, subcommand == "auto_on", now=timestamp
            )
        if not outcome.ok:
            return _reject_control(director, request, outcome.message, now=timestamp)
        record = director.record_control_event(
            request,
            kind=kind,
            category=category,
            status="delivered",
            payload={"story": subcommand, "message": outcome.message},
            now=timestamp,
        )
        return ControlOutcome(record.event_id, record.status, outcome.message)

    # `next` and `rehearse` run side effects; the beat rows carry their own
    # at-most-once ids, and this control row records the operator's attempt.
    record = director.record_control_event(
        request,
        kind=kind,
        category=category,
        status="reserved",
        payload={"story": subcommand},
        now=timestamp,
    )
    if record.status != "reserved":
        return ControlOutcome(
            record.event_id,
            record.status,
            f"request already {record.status}; it was not replayed",
        )
    if not director.mark_attempting(record.event_id, now=timestamp):
        terminal = director.control_event_status(record.event_id) or "ambiguous"
        return ControlOutcome(record.event_id, terminal, "request could not be claimed")
    executor = RconCampaignExecutor(director, world)
    outcome = engine.execute_current_beat(
        director,
        world,
        executor,
        operator=request.operator,
        rehearsal=subcommand == "rehearse",
        manual=True,
        now=timestamp,
    )
    director.finish_attempt(
        record.event_id,
        delivered=outcome.ok,
        error=None if outcome.ok else outcome.message,
        now=timestamp,
    )
    return ControlOutcome(
        record.event_id, "delivered" if outcome.ok else "failed", outcome.message
    )


def campaign_cycle(director: DirectorStore, world_token: int | None) -> None:
    """Autonomous story advancement; inert until `story auto on`."""

    if world_token is None:
        return
    runtime = campaign_runtime()
    if runtime.engine is None:
        return
    executor = RconCampaignExecutor(director, world_token)
    fired = runtime.engine.autonomous_tick(
        director, world_token, executor, now=int(director.clock())
    )
    if fired:
        print(f"[heraldor] kampanya ilerledi: {fired}")


def _clear_control_request(request: ControlRequest) -> None:
    encoded = json.dumps(request.token, ensure_ascii=True)
    rcon(
        f"execute if data storage {CONTROL_STORAGE} "
        f"{{control_request:{encoded}}} run data remove storage "
        f"{CONTROL_STORAGE} control_request"
    )


def _reply_to_control_operator(request: ControlRequest, outcome: ControlOutcome) -> None:
    text = f"[Heraldor] {outcome.message} ({outcome.status})"
    if request.operator == "console":
        print(f"[heraldor] {text}")
        return
    if not PLAYER_NAME_RE.fullmatch(request.operator):
        return
    color = (
        "red"
        if outcome.status in {"failed", "rejected", "ambiguous", "suppressed_expired"}
        else "gray"
    )
    payload = json.dumps({"text": text, "color": color}, ensure_ascii=False)
    try:
        rcon(f"tellraw {request.operator} {payload}")
    except Exception as exc:
        print(f"[heraldor] Director yanıtı oyuncuya iletilemedi: {exc}")


def poll_control_request(director: DirectorStore) -> ControlOutcome | None:
    world_command = (
        f"scoreboard players get {SERVANT_WORLD_HOLDER} {SERVANT_WORLD_OBJECTIVE}"
    )
    world_before_output, storage_output, world_after_output = rcon_many(
        [
            world_command,
            f"data get storage {CONTROL_STORAGE} control_request",
            world_command,
        ]
    )
    world_before = parse_score_output(world_before_output, SERVANT_WORLD_OBJECTIVE)
    world_after = parse_score_output(world_after_output, SERVANT_WORLD_OBJECTIVE)
    if world_before is None or world_before != world_after:
        return None

    token = extract_control_request_token(storage_output)
    if token is None:
        return None
    try:
        request = parse_control_request(token)
    except ValueError as exc:
        # Never remove a value we cannot parse and audit exactly. The host can
        # inspect and conditionally clear this one slot using the runbook.
        print(f"[heraldor] Director posta kutusu geçersiz; güvenli kapandı: {exc}")
        return None

    outcome = process_control_request(
        director,
        request,
        observed_world_token=world_before,
    )
    try:
        _clear_control_request(request)
    except Exception as exc:
        # The deterministic SQLite row is the replay barrier. If the exact
        # mailbox value remains, the next poll acknowledges it without replay.
        print(f"[heraldor] Director isteği onay kutusundan silinemedi: {exc}")
    _reply_to_control_operator(request, outcome)
    print(
        f"[heraldor] Director request={request.event_id} action={request.action} "
        f"operator={request.operator} status={outcome.status}"
    )
    return outcome


def whisper(player: str, line: str | None = None) -> None:
    line = line or random.choice(WHISPERS)
    payload = json.dumps(
        [
            "",
            {"text": line + " ", "color": "dark_gray", "italic": True},
            {"text": OBFUS, "color": "dark_gray", "obfuscated": True},
        ],
        ensure_ascii=False,
    )
    rcon(f"tellraw {player} {payload}")
    snd = random.choice(
        ["minecraft:ambient.cave", "minecraft:entity.enderman.stare", "minecraft:block.sculk_sensor.clicking"]
    )
    rcon(f"execute at {player} run playsound {snd} hostile {player} ~ ~ ~ 0.7 0.5")
    print(f"[heraldor] whisper -> {player}: {line}")


def global_msg(line: str | None = None) -> None:
    line = line or random.choice(GLOBALS_)
    payload = json.dumps(
        [
            "",
            {"text": "Heraldor", "color": "dark_red", "bold": True},
            {"text": " " + line, "color": "gray", "italic": True},
        ],
        ensure_ascii=False,
    )
    rcon(f"tellraw @a {payload}")
    rcon(
        "execute as @a at @s run playsound "
        "minecraft:ambient.basalt_deltas.mood hostile @s ~ ~ ~ 0.5 0.6"
    )
    print(f"[heraldor] global: {line}")


def discord_post_line(line: str) -> None:
    """One-way webhook post as 'Heraldor'; fails closed when unconfigured."""

    if not WEBHOOK:
        raise RuntimeError("Discord webhook is not configured")
    req = urllib.request.Request(
        WEBHOOK,
        data=json.dumps({"content": line, "username": "Heraldor"}).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "heraldor/2.0"},
    )
    urllib.request.urlopen(req, timeout=15).read()


def discord_msg() -> None:
    line = random.choice(DISCORDS)
    discord_post_line(line)
    print(f"[heraldor] discord: {line}")


def shadows(player: str) -> None:
    """Gece yarısı 30 sn'lik vex tacizi — kendiliğinden yok olur, grief yok."""
    name = json.dumps({"text": "Heraldor'un Gölgesi", "color": "dark_gray"}, ensure_ascii=False)
    name_snbt = json.dumps(name, ensure_ascii=False)
    for _ in range(3):
        rcon(
            f"execute at {player} run summon minecraft:vex ~ ~1 ~ "
            f"{{CustomName:{name_snbt},LifeTicks:600,Silent:1b}}"
        )
    rcon(f"execute at {player} run playsound minecraft:entity.vex.charge hostile {player} ~ ~ ~ 1 0.6")
    payload = json.dumps(
        [{"text": "gölgelerim seni buldu.", "color": "dark_gray", "italic": True}],
        ensure_ascii=False,
    )
    rcon(f"tellraw {player} {payload}")
    print(f"[heraldor] shadows -> {player}")


def dispatch_ambient(director: DirectorStore, reservation: Reservation) -> None:
    """Attempt an irreversible side effect once; crashes become ambiguous."""

    if not director.mark_attempting(reservation.event_id):
        return
    try:
        if reservation.kind == "whisper" and reservation.subject:
            whisper(reservation.subject)
        elif reservation.kind == "global":
            global_msg()
        elif reservation.kind == "discord":
            discord_msg()
        elif reservation.kind == "shadows" and reservation.subject:
            shadows(reservation.subject)
        else:
            raise RuntimeError(f"geçersiz olay: {reservation.kind}")
    except Exception as exc:
        director.finish_attempt(reservation.event_id, delivered=None, error=str(exc))
        print(f"[heraldor] {reservation.kind} gönderilemedi: {exc}")
    else:
        director.finish_attempt(reservation.event_id, delivered=True)


def ambient_cycle(
    director: DirectorStore, world_token: int | str | None = None
) -> None:
    """Roll all rare candidates, but permit at most one event per cycle."""

    if world_token is None:
        return
    campaign = director.campaign_state(world_token)
    if campaign.phase == "dormant":
        return

    players = online_players()
    night = is_night() if players else False
    multiplier = 3.0 if night else 1.0
    candidates: list[tuple[str, str | None]] = []

    if players and random.random() < P_WHISPER * multiplier:
        candidates.append(("whisper", random.choice(players)))
    if players and random.random() < P_GLOBAL * multiplier:
        candidates.append(("global", None))
    if WEBHOOK and random.random() < P_DISCORD:
        candidates.append(("discord", None))
    if EVENTS and players and night and random.random() < P_SHADOWS:
        candidates.append(("shadows", random.choice(players)))

    if not candidates:
        return
    kind, subject = random.choice(candidates)
    reservation = director.reserve_ambient(
        kind, subject=subject, world_token=world_token
    )
    if reservation:
        dispatch_ambient(director, reservation)


def poll_servant_score(director: DirectorStore):
    world_command = (
        f"scoreboard players get {SERVANT_WORLD_HOLDER} {SERVANT_WORLD_OBJECTIVE}"
    )
    world_before_output, score_output, world_after_output = rcon_many(
        [
            world_command,
            f"scoreboard players get {SERVANT_SCORE_HOLDER} {SERVANT_OBJECTIVE}",
            world_command,
        ]
    )
    world_before = parse_score_output(world_before_output, SERVANT_WORLD_OBJECTIVE)
    world_after = parse_score_output(world_after_output, SERVANT_WORLD_OBJECTIVE)
    score = parse_score_output(score_output, SERVANT_OBJECTIVE)
    if score is None or world_before is None or world_before != world_after:
        return None

    result = director.ingest_servant_score(score, world_token=world_before)
    if result.victory_event_ids:
        print(
            f"[heraldor] hizmetkâr zaferleri işlendi: "
            f"{result.previous_high_water} -> {result.high_water}"
        )
        # Servant aftermath: the killer's next scene is always footsteps_01.
        # The world stores only the latest kill, so a burst between polls
        # attributes the newest one — the ordinals still close the gap.
        try:
            kill_output = str(
                rcon(f"data get storage {CONTROL_STORAGE} last_minion_kill")
            )
            kill = parse_last_minion_kill(kill_output)
        except Exception as exc:
            kill = None
            print(f"[heraldor] hizmetkâr katili okunamadı: {exc}")
        if kill is not None:
            killer, sequence, kill_world = kill
            if (
                kill_world == world_before
                and result.previous_high_water < sequence <= result.high_water
            ):
                director.record_servant_aftermath(
                    world_before, killer, sequence
                )
                print(
                    f"[heraldor] hizmetkâr sonrası kaydedildi: {killer} "
                    f"için sıradaki sahne her zaman footsteps_01"
                )
    if result.story_event_id:
        output_state = result.story_output_status or "çıkış durumu bilinmiyor"
        print(
            "[heraldor] hikâye eşiği kaydedildi: "
            f"{result.story_event_id}; ses kimliği=servants_after_three_v1; "
            f"{output_state}"
        )
    return result, score, world_before


def poll_stalk_samples(
    director: DirectorStore, world_token: int | None
) -> None:
    """Sample online players' positions into the coarse stalking memory.

    Only runs while the campaign is live; the store itself collapses every
    fix into a 32-block cell and purges other worlds on sight.
    """

    if world_token is None:
        return
    campaign = director.campaign_state(world_token)
    if campaign.phase == "dormant":
        return
    players = online_players()
    if not players:
        return
    outputs = rcon_many([f"data get entity {name} Pos" for name in players])
    for name, output in zip(players, outputs):
        position = parse_pos_output(str(output))
        if position is None:
            continue
        director.record_stalk_visit(world_token, name, position[0], position[2])


def poll_death_log(director: DirectorStore, world_token: int | None) -> None:
    """Ingest the per-player death counter and the last death site."""

    if world_token is None:
        return
    for name in online_players():
        try:
            score_output = str(
                rcon(f"scoreboard players get {name} {DEATH_OBJECTIVE}")
            )
            score = parse_score_output(score_output, DEATH_OBJECTIVE)
            if score is None:
                continue
            if score <= director.death_high_water(world_token, name):
                continue
            site_output = str(
                rcon(f"data get storage {CONTROL_STORAGE} death_{name}")
            )
            site = parse_death_site(site_output)
            result = director.ingest_death(world_token, name, score, site)
        except Exception as exc:
            print(f"[heraldor] ölüm kaydı okunamadı ({name}): {exc}")
            continue
        if result.death_event_ids:
            print(
                f"[heraldor] ölüm kuyruğu işlendi: {name} "
                f"{result.previous_high_water} -> {result.high_water}"
            )
        if result.regression or result.quarantined:
            print(
                f"[heraldor] ölüm skoru şüpheli ({name}); güvenli kapandı: "
                f"kayıt={result.high_water}, görülen={score}"
            )


def scene_scheduler_cycle(
    director: DirectorStore, world_token: int | None
) -> None:
    """The autonomous night-of-activity planner; disabled unless enabled."""

    if not SCHEDULER_ENABLED or world_token is None:
        return
    players = online_players()
    if not players:
        return
    plan = director.plan_and_reserve_scene(world_token, players)
    if plan is None:
        return
    command = (
        f"zapegscene trigger {plan.subject} {plan.event_id} "
        f"{plan.profile} {plan.ttl_ticks}"
    )
    if plan.hint is not None:
        command += f" {plan.hint[0]} {plan.hint[1]}"
    if not director.mark_attempting(plan.event_id):
        return
    try:
        output = str(rcon(command)).strip()
    except Exception as exc:
        director.finish_attempt(
            plan.event_id,
            delivered=None,
            error=f"runtime response was uncertain: {exc}",
        )
        print(f"[heraldor] planlanan sahne belirsiz kaldı: {exc}")
        return
    success = output.startswith("scene dispatched event=")
    director.finish_attempt(
        plan.event_id,
        delivered=success,
        error=None if success else f"runtime rejected request: {output}",
    )
    print(
        f"[heraldor] planlanan sahne ({plan.reason}): {plan.profile} -> "
        f"{plan.subject}; durum={'gönderildi' if success else 'reddedildi'}"
    )


def _world_token_from_servant_poll(polled) -> int | None:
    """Never carry a prior world's token through an unstable/failed poll."""

    return int(polled[2]) if polled else None


def run_daemon() -> None:
    campaign = campaign_runtime()
    print(
        f"[heraldor] uyanıyor — ambient={CHECK_INTERVAL}s, minion={MINION_POLL_INTERVAL}s, "
        f"director={CONTROL_POLL_INTERVAL}s, "
        f"stalk={STALK_SAMPLE_INTERVAL}s, death={DEATH_POLL_INTERVAL}s, "
        f"scheduler={'açık/' + str(SCHEDULER_INTERVAL) + 's' if SCHEDULER_ENABLED else 'kapalı'}, "
        f"webhook={'var' if WEBHOOK else 'yok'}, events={EVENTS}, "
        f"voice={VOICE_ENABLED}, "
        f"kampanya={'geçersiz' if campaign.engine is None else str(CAMPAIGN_PATH.name)}, "
        f"db={DB_PATH}"
    )
    with (
        DirectorStateLock(Path(str(DB_PATH) + ".lock")),
        DirectorStore(
            DB_PATH,
            snapshot_path=SNAPSHOT_PATH,
            audio_sink_enabled=VOICE_ENABLED,
        ) as director,
    ):
        director.backup_snapshot()
        next_ambient = time.monotonic() + CHECK_INTERVAL
        next_minion_poll = time.monotonic()
        next_control_poll = time.monotonic()
        next_stalk_sample = time.monotonic() + STALK_SAMPLE_INTERVAL
        next_death_poll = time.monotonic() + DEATH_POLL_INTERVAL
        next_scheduler = time.monotonic() + SCHEDULER_INTERVAL
        active_world_token: int | None = None
        last_score_anomaly: tuple[str, int, int] | None = None

        while True:
            # Control has priority when schedules coincide, so a queued pause
            # cannot be overtaken by threshold output during startup/recovery.
            now = time.monotonic()
            if now >= next_control_poll:
                next_control_poll = now + CONTROL_POLL_INTERVAL
                try:
                    poll_control_request(director)
                except Exception as exc:
                    print(f"[heraldor] Director posta kutusu okunamadı: {exc}")

            now = time.monotonic()
            if now >= next_minion_poll:
                next_minion_poll = now + MINION_POLL_INTERVAL
                try:
                    polled = poll_servant_score(director)
                    active_world_token = _world_token_from_servant_poll(polled)
                    if polled and (polled[0].regression or polled[0].quarantined):
                        result, observed_score, _world_token = polled
                        kind = "regression" if result.regression else "implausible_jump"
                        anomaly = (kind, result.high_water, observed_score)
                        if anomaly != last_score_anomaly:
                            label = "geriledi" if result.regression else "mantıksız sıçradı"
                            print(
                                f"[heraldor] hizmetkâr skoru {label}; güvenli biçimde "
                                f"karantinaya alındı: kayıt={anomaly[1]}, görülen={anomaly[2]}"
                            )
                            last_score_anomaly = anomaly
                    elif polled:
                        last_score_anomaly = None
                except Exception as exc:
                    active_world_token = _world_token_from_servant_poll(None)
                    print(f"[heraldor] hizmetkâr skoru okunamadı: {exc}")

            now = time.monotonic()
            if now >= next_stalk_sample:
                next_stalk_sample = now + STALK_SAMPLE_INTERVAL
                try:
                    poll_stalk_samples(director, active_world_token)
                except Exception as exc:
                    print(f"[heraldor] takip belleği örneklemi hata: {exc}")

            now = time.monotonic()
            if now >= next_death_poll:
                next_death_poll = now + DEATH_POLL_INTERVAL
                try:
                    poll_death_log(director, active_world_token)
                except Exception as exc:
                    print(f"[heraldor] ölüm kuyruğu döngüsü hata: {exc}")

            now = time.monotonic()
            if now >= next_scheduler:
                next_scheduler = now + SCHEDULER_INTERVAL
                # The campaign is the primary driver; the env-gated idle
                # scheduler only fills quiet between chapters.
                try:
                    campaign_cycle(director, active_world_token)
                except Exception as exc:
                    print(f"[heraldor] kampanya döngüsü hata: {exc}")
                try:
                    scene_scheduler_cycle(director, active_world_token)
                except Exception as exc:
                    print(f"[heraldor] sahne planlayıcısı hata: {exc}")

            now = time.monotonic()
            if now >= next_ambient:
                next_ambient = now + CHECK_INTERVAL
                try:
                    ambient_cycle(director, active_world_token)
                except Exception as exc:
                    print(f"[heraldor] atmosfer döngüsü hata: {exc}")

            delay = (
                min(
                    next_ambient,
                    next_minion_poll,
                    next_control_poll,
                    next_stalk_sample,
                    next_death_poll,
                    next_scheduler,
                )
                - time.monotonic()
            )
            time.sleep(max(0.25, min(delay, 5.0)))


def run_admin(command: str) -> None:
    if command == "restore-snapshot":
        restore_snapshot(DB_PATH, SNAPSHOT_PATH)
        print(f"[heraldor] tutarlı yedek canlı DB'ye geri yüklendi: {SNAPSHOT_PATH}")
        return
    if command == "campaign-validate":
        try:
            campaign = load_campaign(CAMPAIGN_PATH)
        except CampaignError as exc:
            raise SystemExit(f"[heraldor] kampanya dosyası GEÇERSİZ: {exc}")
        print(f"[heraldor] kampanya geçerli: {CAMPAIGN_PATH}")
        for index, chapter in enumerate(campaign.chapters, start=1):
            print(
                f"  {index}. {chapter.id} ({chapter.tier}) — "
                f"{len(chapter.beats)} beat: {chapter.title}"
            )
        return

    # Admin readers may run beside the daemon; they must never classify the
    # daemon's currently-attempting side effect as a crashed one.
    with DirectorStore(
        DB_PATH,
        snapshot_path=SNAPSHOT_PATH,
        recover_interrupted_attempts=False,
    ) as director:
        if command == "status":
            print(json.dumps(director.status(), ensure_ascii=False, indent=2))
        elif command == "snapshot":
            director.backup_snapshot()
            print(f"[heraldor] tutarlı yedek yazıldı: {SNAPSHOT_PATH}")
        elif command == "voice-rehearse":
            event_id = director.enqueue_audio_rehearsal()
            print(
                "[heraldor] ses provası sıraya alındı; iki dakika içinde yalnız "
                f"test kanalında çalabilir: {event_id}"
            )
        else:
            raise ValueError(f"bilinmeyen admin komutu: {command}")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Heraldor persistent director")
    subparsers = parser.add_subparsers(dest="mode")
    admin = subparsers.add_parser("admin", help="host-only state inspection")
    admin.add_argument(
        "command",
        choices=(
            "status",
            "snapshot",
            "restore-snapshot",
            "voice-rehearse",
            "campaign-validate",
        ),
    )
    args = parser.parse_args(argv)

    if args.mode == "admin":
        run_admin(args.command)
    else:
        run_daemon()


if __name__ == "__main__":
    main()
