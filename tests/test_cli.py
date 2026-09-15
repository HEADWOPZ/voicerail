from __future__ import annotations

import json
from pathlib import Path

import pytest

from voicerail.cli import main


def test_cli_speak(rail_home: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    dest = tmp_path / "cli.wav"
    code = main(["--home", str(rail_home), "--engine", "mock", "speak", "cli path", "-o", str(dest)])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["engine"] == "mock"
    assert Path(payload["path"]).is_file()


def test_cli_presets(rail_home: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["--home", str(rail_home), "presets"])
    assert code == 0
    names = {item["id"] for item in json.loads(capsys.readouterr().out)}
    assert names == {"ct_hot_take", "protocol_explainer", "security_psa"}


def test_cli_privacy(rail_home: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["--home", str(rail_home), "--engine", "mock", "privacy"])
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["audio_leaves_machine"] is False


def test_cli_clone(rail_home: Path, sample_wav: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = main(
        ["--home", str(rail_home), "clone", str(sample_wav), "-n", "booth", "--notes", "dry"]
    )
    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["id"] == "booth"
    assert payload["clone_status"] == "stub_acoustic"
