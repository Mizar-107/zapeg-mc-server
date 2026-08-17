#!/usr/bin/env python3
"""Allowlisted, output-only Discord voice relay for Heraldor story events."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import re
import signal
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from heraldor_director import (
    AUDIO_EVENT_TYPE,
    DirectorStateLock,
    DirectorStore,
    AudioDelivery,
    voice_lock_path,
)


CLIP_ID_RE = re.compile(r"^[a-z0-9_]{1,64}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
MAX_ASSET_BYTES = 8 * 1024 * 1024
MAX_CLIP_SECONDS = 30.0
FORBIDDEN_PAYLOAD_FIELDS = frozenset(
    {"path", "filename", "url", "channel", "channel_id", "executable", "options"}
)


@dataclass(frozen=True)
class ClipSpec:
    clip_id: str
    path: Path
    sha256: str
    duration_seconds: float


@dataclass(frozen=True)
class RelayConfig:
    db_path: Path
    snapshot_path: Path
    token_file: Path
    guild_id: int
    live_channel_id: int
    rehearsal_channel_id: int | None
    poll_seconds: float
    connect_timeout_seconds: float
    shared_bot: bool = False


def _positive_snowflake(name: str, *, required: bool = True) -> int | None:
    raw = os.environ.get(name, "").strip()
    if not raw and not required:
        return None
    if not re.fullmatch(r"[1-9]\d{5,21}", raw):
        raise ValueError(f"{name} must be a positive Discord snowflake")
    return int(raw)


def _environment_bool(name: str, *, default: bool = False) -> bool:
    raw = os.environ.get(name, str(default)).strip().lower()
    if raw == "true":
        return True
    if raw == "false":
        return False
    raise ValueError(f"{name} must be true or false")


def relay_config_from_env() -> RelayConfig:
    poll_seconds = float(os.environ.get("HERALDOR_VOICE_POLL_SECONDS", "2"))
    connect_timeout = float(
        os.environ.get("HERALDOR_VOICE_CONNECT_TIMEOUT_SECONDS", "15")
    )
    if not 0.5 <= poll_seconds <= 30:
        raise ValueError("HERALDOR_VOICE_POLL_SECONDS must be between 0.5 and 30")
    if not 5 <= connect_timeout <= 30:
        raise ValueError(
            "HERALDOR_VOICE_CONNECT_TIMEOUT_SECONDS must be between 5 and 30"
        )
    guild_id = int(_positive_snowflake("HERALDOR_DISCORD_GUILD_ID"))
    live_channel_id = int(
        _positive_snowflake("HERALDOR_DISCORD_VOICE_CHANNEL_ID")
    )
    rehearsal_channel_id = _positive_snowflake(
        "HERALDOR_DISCORD_TEST_VOICE_CHANNEL_ID", required=False
    )
    if rehearsal_channel_id == live_channel_id:
        raise ValueError("Discord rehearsal and live voice channels must be different")
    return RelayConfig(
        db_path=Path(os.environ.get("HERALDOR_DB_PATH", "/state/heraldor.sqlite3")),
        snapshot_path=Path(
            os.environ.get(
                "HERALDOR_SNAPSHOT_PATH", "/state/backup/heraldor.sqlite3"
            )
        ),
        token_file=Path(
            os.environ.get(
                "HERALDOR_DISCORD_TOKEN_FILE",
                "/run/secrets/heraldor_discord_bot_token",
            )
        ),
        guild_id=guild_id,
        live_channel_id=live_channel_id,
        rehearsal_channel_id=rehearsal_channel_id,
        poll_seconds=poll_seconds,
        connect_timeout_seconds=connect_timeout,
        shared_bot=_environment_bool("HERALDOR_DISCORD_SHARED_BOT"),
    )


def _gateway_presence_options(discord_module: Any, *, shared_bot: bool) -> dict[str, Any]:
    # In shared mode DCI owns the bot's visible presence. Omitting an initial
    # presence prevents this second Gateway session from setting it invisible.
    if shared_bot:
        return {}
    return {"status": discord_module.Status.invisible}


def _probe_and_decode_asset(asset: Path, declared_duration: float) -> float:
    probe = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "a",
            "-show_entries",
            "stream=codec_name,sample_rate,channels:format=duration",
            "-of",
            "json",
            str(asset),
        ],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    if probe.returncode != 0:
        raise ValueError(f"ffprobe rejected clip asset: {asset.name}")
    try:
        metadata = json.loads(probe.stdout)
        streams = metadata["streams"]
        duration = float(metadata["format"]["duration"])
        stream = streams[0]
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError(f"ffprobe returned invalid clip metadata: {asset.name}") from exc
    if len(streams) != 1:
        raise ValueError(f"clip must contain exactly one audio stream: {asset.name}")
    if (
        stream.get("codec_name") != "opus"
        or int(stream.get("sample_rate", 0)) != 48000
        or int(stream.get("channels", 0)) != 2
    ):
        raise ValueError(f"clip media is not 48 kHz stereo Opus: {asset.name}")
    if abs(duration - declared_duration) > 0.05:
        raise ValueError(f"clip duration does not match its manifest: {asset.name}")

    decode = subprocess.run(
        ["ffmpeg", "-v", "error", "-nostdin", "-i", str(asset), "-f", "null", "-"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        timeout=15,
    )
    if decode.returncode != 0:
        raise ValueError(f"ffmpeg could not fully decode clip asset: {asset.name}")
    return duration


def load_clip_catalog(
    manifest_path: Path,
    audio_root: Path,
    *,
    verify_media: bool = True,
) -> dict[str, ClipSpec]:
    root = audio_root.resolve(strict=True)
    manifest = manifest_path.resolve(strict=True)
    if manifest.parent != root:
        raise ValueError("clip manifest must live directly inside the fixed audio root")
    document = json.loads(manifest.read_text(encoding="utf-8"))
    if document.get("schema_version") != 1 or not isinstance(document.get("clips"), dict):
        raise ValueError("unsupported clip manifest")

    catalog: dict[str, ClipSpec] = {}
    for clip_id, raw in document["clips"].items():
        if not isinstance(clip_id, str) or not CLIP_ID_RE.fullmatch(clip_id):
            raise ValueError(f"invalid clip ID: {clip_id!r}")
        if not isinstance(raw, dict):
            raise ValueError(f"invalid manifest entry: {clip_id}")
        filename = raw.get("filename")
        expected_hash = str(raw.get("sha256", "")).lower()
        duration = float(raw.get("duration_seconds", 0))
        if not isinstance(filename, str) or Path(filename).name != filename:
            raise ValueError(f"clip filename must be a basename: {clip_id}")
        if not SHA256_RE.fullmatch(expected_hash):
            raise ValueError(f"invalid SHA-256 for clip: {clip_id}")
        if raw.get("codec") != "opus" or raw.get("sample_rate") != 48000:
            raise ValueError(f"clip is not approved 48 kHz Opus: {clip_id}")
        if raw.get("channels") != 2:
            raise ValueError(f"clip is not approved stereo audio: {clip_id}")
        if not 0 < duration <= MAX_CLIP_SECONDS:
            raise ValueError(f"clip duration is outside the safe limit: {clip_id}")

        asset = root / filename
        if asset.is_symlink() or not asset.is_file() or asset.resolve().parent != root:
            raise ValueError(f"clip asset escapes or is missing from audio root: {clip_id}")
        size = asset.stat().st_size
        if size <= 0 or size > MAX_ASSET_BYTES:
            raise ValueError(f"clip asset size is outside the safe limit: {clip_id}")
        actual_hash = hashlib.sha256(asset.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            raise ValueError(f"clip SHA-256 mismatch: {clip_id}")
        if verify_media:
            duration = _probe_and_decode_asset(asset, duration)
        catalog[clip_id] = ClipSpec(clip_id, asset, actual_hash, duration)

    if not catalog:
        raise ValueError("clip manifest is empty")
    return catalog


def load_catalog_from_env() -> dict[str, ClipSpec]:
    root = Path(os.environ.get("HERALDOR_AUDIO_ROOT", "/clips"))
    manifest = Path(
        os.environ.get("HERALDOR_CLIP_MANIFEST", str(root / "clips.json"))
    )
    return load_clip_catalog(manifest, root)


def read_bot_token(path: Path) -> str:
    try:
        token = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise RuntimeError(f"Discord token secret cannot be read: {path}") from exc
    if not 30 <= len(token) <= 512 or any(ch.isspace() for ch in token):
        raise RuntimeError("Discord token secret has an invalid shape")
    return token


def resolve_delivery(
    delivery: AudioDelivery,
    catalog: dict[str, ClipSpec],
    *,
    now: int | None = None,
) -> ClipSpec:
    payload = delivery.payload
    if FORBIDDEN_PAYLOAD_FIELDS.intersection(payload):
        raise ValueError("audio event contains a forbidden routing field")
    if payload.get("event_id") != delivery.event_id:
        raise ValueError("audio event ID does not match its outbox row")
    if payload.get("type") != AUDIO_EVENT_TYPE:
        raise ValueError("audio event type is not allowlisted")
    if payload.get("rehearsal") is not delivery.rehearsal:
        raise ValueError("audio rehearsal flag does not match its event")
    clip_id = payload.get("clip_id")
    if not isinstance(clip_id, str) or clip_id not in catalog:
        raise ValueError("audio clip ID is not allowlisted")
    try:
        expires_at = int(payload["expires_at"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("audio event has no valid expiry") from exc
    if expires_at <= int(time.time() if now is None else now):
        raise TimeoutError("audio event expired before playback")
    return catalog[clip_id]


def _safe_error(exc: BaseException, token: str) -> str:
    text = f"{type(exc).__name__}: {exc}"
    if token:
        text = text.replace(token, "[redacted]")
    return text[:500]


async def _play_delivery(
    client: Any,
    discord: Any,
    store: DirectorStore,
    catalog: dict[str, ClipSpec],
    config: RelayConfig,
    delivery: AudioDelivery,
    token: str,
) -> None:
    try:
        clip = resolve_delivery(delivery, catalog)
    except TimeoutError as exc:
        store.finish_audio(
            delivery.event_id, status="suppressed_expired", error=str(exc)
        )
        return
    except Exception as exc:
        store.finish_audio(
            delivery.event_id,
            status="rejected_clip",
            error=_safe_error(exc, token),
        )
        return

    channel_id = (
        config.rehearsal_channel_id if delivery.rehearsal else config.live_channel_id
    )
    if channel_id is None:
        store.finish_audio(
            delivery.event_id,
            status="rejected_destination",
            error="no dedicated rehearsal voice channel is configured",
        )
        return

    channel = client.get_channel(channel_id)
    if (
        channel is None
        or not isinstance(channel, discord.VoiceChannel)
        or channel.guild.id != config.guild_id
    ):
        store.finish_audio(
            delivery.event_id,
            status="rejected_destination",
            error="configured destination is not a voice channel in the fixed guild",
        )
        return

    def audible_humans() -> list[Any]:
        return [
            member
            for member in channel.members
            if not member.bot
            and member.voice is not None
            and not member.voice.deaf
            and not member.voice.self_deaf
        ]

    listeners = audible_humans()
    if not listeners:
        store.finish_audio(
            delivery.event_id,
            status="suppressed_empty_channel",
            error="configured voice channel had no human listener",
        )
        return

    voice = None
    source = None
    playback_started = False
    try:
        existing = channel.guild.voice_client
        if existing is not None:
            await existing.disconnect(force=True)
        voice = await channel.connect(
            timeout=config.connect_timeout_seconds,
            reconnect=False,
            self_deaf=True,
            self_mute=False,
        )
        if not audible_humans():
            store.finish_audio(
                delivery.event_id,
                status="suppressed_empty_channel",
                error="the last audible human left during the voice handshake",
            )
            return
        encoded_source = discord.FFmpegOpusAudio(str(clip.path), codec="copy")

        class ExhaustionTrackingSource(discord.AudioSource):
            """Distinguish a complete source from a clean-looking truncation."""

            def __init__(self) -> None:
                self.exhausted = False
                self.cleaned = False
                self._current_error = None
                self._cleanup_lock = threading.Lock()

            def read(self) -> bytes:
                data = encoded_source.read()
                self._current_error = getattr(encoded_source, "_current_error", None)
                if not data and self._current_error is None:
                    self.exhausted = True
                return data

            def is_opus(self) -> bool:
                return True

            def cleanup(self) -> None:
                with self._cleanup_lock:
                    if not self.cleaned:
                        self.cleaned = True
                        encoded_source.cleanup()

        source = ExhaustionTrackingSource()
        loop = asyncio.get_running_loop()
        finished: asyncio.Future[None] = loop.create_future()

        def after(error: BaseException | None) -> None:
            def complete() -> None:
                if finished.done():
                    return
                if error:
                    finished.set_exception(error)
                else:
                    finished.set_result(None)

            loop.call_soon_threadsafe(complete)

        voice.play(source, after=after)
        playback_started = True
        await asyncio.wait_for(finished, timeout=clip.duration_seconds + 10)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        store.finish_audio(
            delivery.event_id,
            status="ambiguous" if playback_started else "failed",
            error=_safe_error(exc, token),
        )
    else:
        if not source.exhausted:
            store.finish_audio(
                delivery.event_id,
                status="ambiguous",
                error="voice player ended before the allowlisted source reached EOF",
            )
        else:
            store.finish_audio(delivery.event_id, status="delivered")
            print(
                f"[heraldor-voice] delivered {clip.clip_id} to channel {channel_id} "
                f"for event {delivery.event_id}"
            )
    finally:
        if voice is not None:
            try:
                await voice.disconnect(force=True)
            except Exception as exc:
                print(
                    "[heraldor-voice] disconnect warning: "
                    + _safe_error(exc, token)
                )
        if source is not None:
            source.cleanup()


async def _run_gateway(
    config: RelayConfig,
    catalog: dict[str, ClipSpec],
    store: DirectorStore,
    token: str,
) -> None:
    import discord

    intents = discord.Intents.none()
    intents.guilds = True
    intents.voice_states = True

    class RelayClient(discord.Client):
        worker: asyncio.Task[None] | None = None

        async def setup_hook(self) -> None:
            self.worker = asyncio.create_task(self.relay_loop(), name="heraldor-voice")

        async def on_ready(self) -> None:
            print(
                f"[heraldor-voice] ready as bot {self.user.id}; "
                f"guild={config.guild_id}, live_channel={config.live_channel_id}, "
                f"test_channel={config.rehearsal_channel_id or 'disabled'}"
            )

        async def relay_loop(self) -> None:
            await self.wait_until_ready()
            while not self.is_closed():
                if not self.is_ready():
                    await asyncio.sleep(config.poll_seconds)
                    continue
                try:
                    delivery = store.claim_next_audio()
                    if delivery is None:
                        await asyncio.sleep(config.poll_seconds)
                        continue
                    await _play_delivery(
                        self, discord, store, catalog, config, delivery, token
                    )
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    print(
                        "[heraldor-voice] worker error: " + _safe_error(exc, token)
                    )
                    await asyncio.sleep(config.poll_seconds)

        async def close(self) -> None:
            if self.worker and self.worker is not asyncio.current_task():
                self.worker.cancel()
                try:
                    await self.worker
                except asyncio.CancelledError:
                    pass
            for voice in list(self.voice_clients):
                try:
                    await voice.disconnect(force=True)
                except Exception:
                    pass
            await super().close()

    client = RelayClient(
        intents=intents,
        max_messages=None,
        **_gateway_presence_options(discord, shared_bot=config.shared_bot),
    )
    loop = asyncio.get_running_loop()
    for signum in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(signum, lambda: asyncio.create_task(client.close()))
        except (NotImplementedError, RuntimeError):
            pass
    await client.start(token, reconnect=True)


def run_daemon() -> None:
    config = relay_config_from_env()
    catalog = load_catalog_from_env()
    token = read_bot_token(config.token_file)
    print(
        f"[heraldor-voice] catalog verified: {', '.join(sorted(catalog))}; "
        "output-only gateway, message intents disabled"
    )
    with (
        DirectorStateLock(voice_lock_path(config.db_path)),
        DirectorStore(
            config.db_path,
            snapshot_path=config.snapshot_path,
            recover_interrupted_attempts=False,
        ) as store,
    ):
        recovered = store.recover_interrupted_audio()
        if recovered:
            print(
                f"[heraldor-voice] marked {recovered} interrupted playback(s) ambiguous"
            )
        asyncio.run(_run_gateway(config, catalog, store, token))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Heraldor Discord voice relay")
    parser.add_argument(
        "command", nargs="?", choices=("run", "validate"), default="run"
    )
    args = parser.parse_args(argv)
    if args.command == "validate":
        catalog = load_catalog_from_env()
        for clip_id, clip in sorted(catalog.items()):
            print(
                f"{clip_id}: {clip.duration_seconds:.3f}s, sha256={clip.sha256}, "
                f"file={clip.path.name}"
            )
        return
    run_daemon()


if __name__ == "__main__":
    main()
