"""Optional on-device backends. Never calls a cloud TTS API."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from voicerail.audio.pcm import AudioClip
from voicerail.audio.wav import read_wav
from voicerail.engine.base import EngineInfo, TTSEngine
from voicerail.engine.mock import MockEngine
from voicerail.presets import Preset
from voicerail.voices import VoiceProfile


class LocalEngineError(RuntimeError):
    pass


def detect_local_backend() -> str | None:
    if shutil.which("piper"):
        return "piper"
    if shutil.which("espeak-ng"):
        return "espeak-ng"
    if shutil.which("espeak"):
        return "espeak"
    return None


class LocalEngine(TTSEngine):
    """Thin wrapper around Piper or eSpeak. Falls over with a clear error."""

    id = "local"

    def __init__(self, backend: str | None = None) -> None:
        self.backend = backend or detect_local_backend()

    def info(self) -> EngineInfo:
        backend = self.backend or detect_local_backend()
        available = backend is not None
        if backend == "piper":
            detail = "Piper CLI detected. Neural local TTS, still on-device."
        elif backend in {"espeak-ng", "espeak"}:
            detail = f"{backend} detected. Formant TTS binary, on-device, no GPU."
        else:
            detail = (
                "No local binary found. Install Piper (preferred) or espeak-ng, "
                "or set VOICERAIL_ENGINE=mock. VoiceRail will not call cloud TTS."
            )
        return EngineInfo(
            id="local",
            label=f"Local wrapper ({backend or 'unavailable'})",
            offline=True,
            gpu_required=False,
            available=available,
            detail=detail,
        )

    def synthesize(self, text: str, voice: VoiceProfile, preset: Preset) -> AudioClip:
        backend = self.backend or detect_local_backend()
        if backend is None:
            raise LocalEngineError(
                "VOICERAIL_ENGINE=local but neither piper nor espeak-ng is on PATH. "
                "Install one of them, or use VOICERAIL_ENGINE=mock / auto."
            )
        if backend == "piper":
            return _synthesize_piper(text, voice, preset)
        return _synthesize_espeak(text, voice, preset, binary=backend)


class AutoEngine(TTSEngine):
    """Prefer a local binary; otherwise the mock path (CI-safe)."""

    id = "auto"

    def __init__(self) -> None:
        backend = detect_local_backend()
        self._inner: TTSEngine = LocalEngine(backend) if backend else MockEngine()

    def info(self) -> EngineInfo:
        inner = self._inner.info()
        return EngineInfo(
            id="auto",
            label=f"Auto ({inner.id})",
            offline=True,
            gpu_required=False,
            available=True,
            detail=f"Resolved to {inner.id}. {inner.detail}",
        )

    def synthesize(self, text: str, voice: VoiceProfile, preset: Preset) -> AudioClip:
        return self._inner.synthesize(text, voice, preset)


def load_engine(name: str) -> TTSEngine:
    if name == "mock":
        return MockEngine()
    if name == "local":
        return LocalEngine()
    if name == "auto":
        return AutoEngine()
    raise ValueError(f"Unknown engine {name!r}")


def _synthesize_piper(text: str, voice: VoiceProfile, preset: Preset) -> AudioClip:
    model = _piper_model(voice)
    if model is None:
        raise LocalEngineError(
            "Piper is installed but no ONNX voice model is configured. "
            "Set VOICERAIL_PIPER_MODEL to a local .onnx path. "
            "The sample you cloned is still on disk and was not uploaded."
        )
    with tempfile.TemporaryDirectory(prefix="voicerail-piper-") as tmp:
        out = Path(tmp) / "out.wav"
        cmd = ["piper", "--model", model, "--output_file", str(out)]
        length_scale = max(0.55, min(1.8, 1.0 / preset.rate))
        cmd.extend(["--length_scale", f"{length_scale:.2f}"])
        result = subprocess.run(
            cmd,
            input=text,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0 or not out.is_file():
            raise LocalEngineError(
                f"Piper failed ({result.returncode}): {result.stderr.strip() or result.stdout}"
            )
        return read_wav(out)


def _synthesize_espeak(
    text: str, voice: VoiceProfile, preset: Preset, binary: str
) -> AudioClip:
    wpm = int(max(80, min(260, 165 * preset.rate)))
    # eSpeak pitch is 0-99; map typical F0 into that band.
    pitch = int(max(5, min(80, (voice.base_f0 * preset.f0_scale - 70) * 0.55)))
    with tempfile.TemporaryDirectory(prefix="voicerail-espeak-") as tmp:
        out = Path(tmp) / "out.wav"
        cmd = [
            binary,
            "-w",
            str(out),
            "-s",
            str(wpm),
            "-p",
            str(pitch),
            "-v",
            "en",
            text,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0 or not out.is_file():
            raise LocalEngineError(
                f"{binary} failed ({result.returncode}): {result.stderr.strip() or result.stdout}"
            )
        return read_wav(out)


def _piper_model(voice: VoiceProfile) -> str | None:
    import os

    env = os.environ.get("VOICERAIL_PIPER_MODEL")
    if env and Path(env).is_file():
        return env
    extra = voice.extra or {}
    model = extra.get("piper_model")
    if model and Path(str(model)).is_file():
        return str(model)
    return None
