from __future__ import annotations

import os
from pathlib import Path

import pytest

from voicerail.audio.pcm import floats_to_clip
from voicerail.audio.wav import write_wav
from voicerail.service import VoiceRail


@pytest.fixture
def rail_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "voicerail-home"
    monkeypatch.setenv("VOICERAIL_HOME", str(home))
    monkeypatch.setenv("VOICERAIL_ENGINE", "mock")
    monkeypatch.delenv("VOICERAIL_PIPER_MODEL", raising=False)
    return home


@pytest.fixture
def rail(rail_home: Path) -> VoiceRail:
    return VoiceRail(home=rail_home, engine="mock")


@pytest.fixture
def sample_wav(tmp_path: Path) -> Path:
    # ~0.45s of a 120 Hz pulse train so autocorrelation can lock.
    sr = 22050
    frames: list[float] = []
    for i in range(int(sr * 0.45)):
        phase = (i * 120.0 / sr) % 1.0
        frames.append(1.0 if phase < 0.12 else 0.0)
    clip = floats_to_clip(frames, sr)
    path = tmp_path / "sample.wav"
    write_wav(clip, path)
    return path


def pytest_configure() -> None:
    os.environ.setdefault("VOICERAIL_ENGINE", "mock")
