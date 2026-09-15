from __future__ import annotations

from pathlib import Path

import pytest

from voicerail.audio.mp3 import encoder_status, write_mp3
from voicerail.audio.wav import read_wav
from voicerail.service import VoiceRail


def test_wav_roundtrip(rail: VoiceRail, tmp_path: Path) -> None:
    dest = tmp_path / "take.wav"
    result = rail.speak("VoiceRail stays on the box.", fmt="wav", output_path=dest)
    assert dest.is_file()
    assert dest.stat().st_size > 1000
    clip = read_wav(dest)
    assert clip.sample_rate == 22050
    assert clip.duration_seconds > 0.3
    assert result.format == "wav"
    assert result.offline is True
    assert result.gpu_required is False


def test_mp3_export_writes_mpeg_sync(rail: VoiceRail, tmp_path: Path) -> None:
    dest = tmp_path / "take.mp3"
    result = rail.speak(
        "Do not paste your seed into a website.",
        preset="security_psa",
        fmt="mp3",
        output_path=dest,
    )
    data = dest.read_bytes()
    assert dest.stat().st_size > 200
    assert data.startswith(b"ID3") or data[:2] in {b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"} or data[0] == 0xFF
    assert result.format == "mp3"


def test_fallback_encoder_produces_mp3_without_binaries(
    rail: VoiceRail, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import voicerail.audio.mp3 as mp3mod

    monkeypatch.setattr(mp3mod, "_encode_with_ffmpeg", lambda clip, path: False)
    monkeypatch.setattr(mp3mod, "_encode_with_lame", lambda clip, path: False)
    dest = tmp_path / "lite.mp3"
    clip_result = rail.speak("fallback tile encoder", fmt="wav", output_path=tmp_path / "x.wav")
    from voicerail.audio.wav import read_wav

    clip = read_wav(Path(clip_result.path))
    write_mp3(clip, dest)
    assert dest.stat().st_size > 200
    assert dest.read_bytes()[0] == 0xFF


def test_encoder_status_mentions_fallback() -> None:
    status = encoder_status()
    assert status["fallback"] is True
