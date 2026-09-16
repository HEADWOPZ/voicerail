from __future__ import annotations

from pathlib import Path

import pytest

from voicerail.service import VoiceRail


def test_speak_refuses_empty(rail: VoiceRail) -> None:
    with pytest.raises(ValueError, match="needs text"):
        rail.speak("   ")


def test_speak_refuses_huge_script(rail: VoiceRail) -> None:
    with pytest.raises(ValueError, match="12,000"):
        rail.speak("x" * 12_001)


def test_privacy_status_is_local(rail: VoiceRail) -> None:
    status = rail.privacy_status()
    assert status["offline"] is True
    assert status["audio_leaves_machine"] is False
    assert status["telemetry"] is False
    assert status["cloud_tts"] is False
    assert status["gpu_required"] is False
    assert status["engine"]["id"] == "mock"


def test_default_output_lands_in_home(rail: VoiceRail, rail_home: Path) -> None:
    result = rail.speak("exports stay home")
    path = Path(result.path)
    assert rail_home in path.parents or path.is_relative_to(rail_home)
    assert path.suffix == ".wav"
