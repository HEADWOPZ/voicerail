"""Local voice profiles. Clone samples never leave this machine."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from voicerail.audio.pcm import estimate_f0
from voicerail.audio.wav import read_wav

DEFAULT_VOICE_ID = "klm"
SCHEMA_VERSION = 1


@dataclass
class VoiceProfile:
    id: str
    label: str
    base_f0: float
    brightness: float = 1.0
    intensity: float = 0.82
    source_wav: str | None = None
    duration_seconds: float | None = None
    rms: float | None = None
    notes: str = ""
    engine_hint: str = "mock"
    created_at: str = ""
    clone_status: str = "factory"
    clone_disclaimer: str = ""
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["schema"] = SCHEMA_VERSION
        return payload

    @classmethod
    def from_dict(cls, data: dict) -> VoiceProfile:
        known = {key: data[key] for key in cls.__dataclass_fields__ if key in data}
        return cls(**known)


DEFAULT_KLM = VoiceProfile(
    id=DEFAULT_VOICE_ID,
    label="Kevin Lance Murray",
    base_f0=108.0,
    brightness=1.02,
    intensity=0.80,
    notes="Factory baritone register for KLM. Replace by cloning a local WAV.",
    engine_hint="mock",
    clone_status="factory",
    clone_disclaimer=(
        "Factory profile. Neural speaker weights are not embedded. "
        "Run clone_from_wav on a local 16-bit WAV to lock the mock register "
        "to your sample's pitch and energy."
    ),
)


class VoiceStore:
    def __init__(self, directory: Path) -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.ensure_default()

    def path_for(self, voice_id: str) -> Path:
        safe = _safe_id(voice_id)
        return self.directory / f"{safe}.json"

    def ensure_default(self) -> VoiceProfile:
        path = self.path_for(DEFAULT_VOICE_ID)
        if not path.exists():
            profile = VoiceProfile(
                **{**asdict(DEFAULT_KLM), "created_at": _now()},
            )
            self.save(profile)
            return profile
        return self.get(DEFAULT_VOICE_ID)

    def save(self, profile: VoiceProfile) -> VoiceProfile:
        path = self.path_for(profile.id)
        path.write_text(json.dumps(profile.to_dict(), indent=2) + "\n", encoding="utf-8")
        return profile

    def get(self, voice_id: str) -> VoiceProfile:
        path = self.path_for(voice_id)
        if not path.is_file():
            known = ", ".join(item.id for item in self.list()) or "(none)"
            raise FileNotFoundError(f"Voice {voice_id!r} is not registered. Known voices: {known}")
        data = json.loads(path.read_text(encoding="utf-8"))
        return VoiceProfile.from_dict(data)

    def list(self) -> list[VoiceProfile]:
        profiles = []
        for path in sorted(self.directory.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            profiles.append(VoiceProfile.from_dict(data))
        return profiles


def clone_from_wav(
    wav_path: Path,
    store: VoiceStore,
    name: str | None = None,
    notes: str = "",
) -> VoiceProfile:
    """Stub clone: derive pitch/energy from a local WAV and store a profile.

    This is intentionally not a neural voice-conversion pass. The mock engine
    then speaks in the measured register. A future local backend (Piper voice,
    XTTS-v2, or RVC) can read the same profile and ``source_wav``.
    """
    path = Path(wav_path).expanduser().resolve()
    clip = read_wav(path)
    f0 = estimate_f0(clip) or 108.0
    f0 = max(70.0, min(260.0, f0))
    rms = clip.rms
    brightness = 0.85 + min(0.5, (rms / 8000.0))
    intensity = 0.62 + min(0.32, rms / 14000.0)
    voice_id = _safe_id(name or path.stem)
    profile = VoiceProfile(
        id=voice_id,
        label=name or path.stem,
        base_f0=round(f0, 2),
        brightness=round(brightness, 3),
        intensity=round(intensity, 3),
        source_wav=str(path),
        duration_seconds=round(clip.duration_seconds, 3),
        rms=round(rms, 2),
        notes=notes,
        engine_hint="mock",
        created_at=_now(),
        clone_status="stub_acoustic",
        clone_disclaimer=(
            "Acoustic stub clone. VoiceRail measured pitch and energy from the "
            "WAV and stored them locally. It did not train speaker embeddings "
            "and did not upload the sample. Swap VOICERAIL_ENGINE=local and "
            "install Piper/XTTS when you want neural timbre; the profile path "
            "is the hook those backends will read."
        ),
        extra={"sample_rate": clip.sample_rate, "frames": len(clip.samples)},
    )
    return store.save(profile)


def _safe_id(value: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in value.strip())
    cleaned = "-".join(part for part in cleaned.split("-") if part)
    if not cleaned:
        raise ValueError("Voice name must contain letters or digits")
    return cleaned[:48]


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
