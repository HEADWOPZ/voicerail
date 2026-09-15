"""High-level API shared by the CLI and the MCP server."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from voicerail import __version__
from voicerail.audio.mp3 import encoder_status, write_mp3
from voicerail.audio.wav import write_wav
from voicerail.config import FORMAT_CHOICES, Settings
from voicerail.engine.local import load_engine
from voicerail.presets import get_preset, list_presets
from voicerail.voices import VoiceStore, clone_from_wav


@dataclass
class SpeakResult:
    path: str
    format: str
    duration_seconds: float
    sample_rate: int
    bytes: int
    engine: str
    voice: str
    preset: str
    offline: bool
    gpu_required: bool
    text_chars: int
    created_at: str

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class VoiceRail:
    def __init__(
        self,
        home: Path | None = None,
        engine: str | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.settings = settings or Settings.load(home)
        engine_name = engine or self.settings.engine
        self.engine = load_engine(engine_name)
        self.voices = VoiceStore(self.settings.voices_dir)

    def speak(
        self,
        text: str,
        preset: str | None = None,
        voice: str | None = None,
        fmt: str | None = None,
        output_path: str | Path | None = None,
    ) -> SpeakResult:
        if text is None or not str(text).strip():
            raise ValueError("speak() needs text — nothing to narrate")
        body = str(text).strip()
        if len(body) > 12_000:
            raise ValueError("speak() refuses scripts over 12,000 characters in one call")
        preset_obj = get_preset(preset or self.settings.default_preset)
        voice_obj = self.voices.get(voice or self.settings.default_voice)
        fmt_name = (fmt or self.settings.default_format).strip().lower()
        if fmt_name not in FORMAT_CHOICES:
            raise ValueError(f"format must be wav or mp3, got {fmt_name!r}")

        clip = self.engine.synthesize(body, voice_obj, preset_obj)
        dest = _resolve_output(output_path, self.settings.exports_dir, fmt_name, preset_obj.id)
        if fmt_name == "wav":
            write_wav(clip, dest)
        else:
            write_mp3(clip, dest)

        info = self.engine.info()
        return SpeakResult(
            path=str(dest.resolve()),
            format=fmt_name,
            duration_seconds=round(clip.duration_seconds, 3),
            sample_rate=clip.sample_rate,
            bytes=dest.stat().st_size,
            engine=info.id,
            voice=voice_obj.id,
            preset=preset_obj.id,
            offline=info.offline,
            gpu_required=info.gpu_required,
            text_chars=len(body),
            created_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        )

    def clone_from_wav(
        self,
        wav_path: str | Path,
        name: str | None = None,
        notes: str = "",
    ) -> dict:
        profile = clone_from_wav(Path(wav_path), self.voices, name=name, notes=notes)
        payload = profile.to_dict()
        payload["privacy"] = (
            "Sample analyzed locally. Nothing was uploaded. Neural timbre "
            "transfer is not part of this stub — see clone_disclaimer."
        )
        return payload

    def list_presets(self) -> list[dict]:
        return list_presets()

    def list_voices(self) -> list[dict]:
        return [profile.to_dict() for profile in self.voices.list()]

    def privacy_status(self) -> dict:
        info = self.engine.info()
        return {
            "product": "VoiceRail",
            "version": __version__,
            "offline": True,
            "audio_leaves_machine": False,
            "telemetry": False,
            "cloud_tts": False,
            "gpu_required": info.gpu_required,
            "engine": info.to_dict() if hasattr(info, "to_dict") else {
                "id": info.id,
                "label": info.label,
                "offline": info.offline,
                "gpu_required": info.gpu_required,
                "available": info.available,
                "detail": info.detail,
            },
            "home": str(self.settings.home),
            "voices_dir": str(self.settings.voices_dir),
            "exports_dir": str(self.settings.exports_dir),
            "mp3": encoder_status(),
            "promise": (
                "speak and clone_from_wav run on this machine. VoiceRail does "
                "not open a network socket for inference and does not ship WAV "
                "samples to a vendor. Pair with AlphaClip Forge for on-device clips."
            ),
        }


def _resolve_output(
    output_path: str | Path | None,
    exports_dir: Path,
    fmt: str,
    preset_id: str,
) -> Path:
    if output_path:
        dest = Path(output_path).expanduser()
        if dest.suffix.lower() not in {".wav", ".mp3"}:
            dest = dest.with_suffix(f".{fmt}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        return dest
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dest = exports_dir / f"voicerail-{preset_id}-{stamp}.{fmt}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    return dest
