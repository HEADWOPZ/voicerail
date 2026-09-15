from __future__ import annotations

import pytest

from voicerail.engine.mock import MockEngine
from voicerail.presets import PRESETS, get_preset
from voicerail.voices import DEFAULT_KLM


def test_three_shipped_presets() -> None:
    assert set(PRESETS) == {"ct_hot_take", "protocol_explainer", "security_psa"}


def test_preset_aliases() -> None:
    assert get_preset("hot-take").id == "ct_hot_take"
    assert get_preset("loom").id == "protocol_explainer"
    assert get_preset("psa").id == "security_psa"


def test_unknown_preset_errors() -> None:
    with pytest.raises(ValueError, match="Unknown preset"):
        get_preset("radio_dj")


def test_hot_take_is_shorter_than_security_psa() -> None:
    engine = MockEngine()
    text = "Revoke the signer. Rotate the key. Tell the room."
    hot = engine.synthesize(text, DEFAULT_KLM, get_preset("ct_hot_take"))
    psa = engine.synthesize(text, DEFAULT_KLM, get_preset("security_psa"))
    assert hot.duration_seconds < psa.duration_seconds
