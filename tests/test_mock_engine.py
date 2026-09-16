from __future__ import annotations

from voicerail.engine.mock import MockEngine
from voicerail.presets import get_preset
from voicerail.voices import DEFAULT_KLM


def test_mock_engine_is_offline_and_gpu_free() -> None:
    info = MockEngine().info()
    assert info.available is True
    assert info.offline is True
    assert info.gpu_required is False


def test_longer_text_is_longer_audio() -> None:
    engine = MockEngine()
    voice = DEFAULT_KLM
    preset = get_preset("protocol_explainer")
    short = engine.synthesize("gm", voice, preset)
    long = engine.synthesize("good morning to the timeline and the protocol desk", voice, preset)
    assert long.duration_seconds > short.duration_seconds * 2
    assert short.peak > 0
    assert long.peak > 0


def test_different_text_different_pcm() -> None:
    engine = MockEngine()
    voice = DEFAULT_KLM
    preset = get_preset("ct_hot_take")
    a = engine.synthesize("liquidity is a story", voice, preset)
    b = engine.synthesize("the bridge is the bug", voice, preset)
    assert a.to_bytes() != b.to_bytes()


def test_empty_text_still_returns_clip() -> None:
    clip = MockEngine().synthesize("   ", DEFAULT_KLM, get_preset("security_psa"))
    assert clip.duration_seconds > 0
