from __future__ import annotations

import pytest

from voicerail.engine.local import LocalEngine, LocalEngineError, load_engine
from voicerail.engine.mock import MockEngine
from voicerail.presets import get_preset
from voicerail.voices import DEFAULT_KLM


def test_load_engine_mock() -> None:
    engine = load_engine("mock")
    assert isinstance(engine, MockEngine)


def test_load_engine_unknown() -> None:
    with pytest.raises(ValueError):
        load_engine("elevenlabs")


def test_local_engine_errors_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    from voicerail.engine import local as localmod

    monkeypatch.setattr(localmod, "detect_local_backend", lambda: None)
    engine = LocalEngine(backend=None)
    engine.backend = None
    info = engine.info()
    assert info.available is False
    assert info.offline is True
    with pytest.raises(LocalEngineError, match="piper"):
        engine.synthesize("hello", DEFAULT_KLM, get_preset("protocol_explainer"))


def test_auto_engine_always_available() -> None:
    engine = load_engine("auto")
    clip = engine.synthesize("auto path", DEFAULT_KLM, get_preset("ct_hot_take"))
    assert clip.duration_seconds > 0
    assert engine.info().available is True
    assert engine.info().gpu_required is False
