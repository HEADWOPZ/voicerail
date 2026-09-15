from __future__ import annotations

from pathlib import Path

import pytest

from voicerail.engine.mock import MockEngine
from voicerail.presets import get_preset
from voicerail.service import VoiceRail


def test_clone_from_wav_stores_profile(rail: VoiceRail, sample_wav: Path) -> None:
    profile = rail.clone_from_wav(sample_wav, name="klm-desk", notes="booth take")
    assert profile["id"] == "klm-desk"
    assert profile["clone_status"] == "stub_acoustic"
    assert profile["source_wav"] == str(sample_wav.resolve())
    assert 70.0 <= profile["base_f0"] <= 260.0
    assert "not upload" in profile["clone_disclaimer"].lower() or "did not upload" in profile["clone_disclaimer"]
    ids = {item["id"] for item in rail.list_voices()}
    assert "klm-desk" in ids
    assert "klm" in ids


def test_clone_changes_register(rail: VoiceRail, sample_wav: Path) -> None:
    rail.clone_from_wav(sample_wav, name="high-sample")
    factory = rail.voices.get("klm")
    cloned = rail.voices.get("high-sample")
    engine = MockEngine()
    preset = get_preset("protocol_explainer")
    a = engine.synthesize("revoke the allowance", factory, preset)
    b = engine.synthesize("revoke the allowance", cloned, preset)
    # Same script, different register — PCM must move.
    assert a.to_bytes() != b.to_bytes()


def test_clone_missing_file(rail: VoiceRail, tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        rail.clone_from_wav(tmp_path / "nope.wav", name="ghost")
