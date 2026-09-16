from __future__ import annotations

import json
from pathlib import Path

import pytest

from voicerail.mcp_server import (
    clone_from_wav,
    list_presets,
    list_voices,
    mcp,
    privacy_status,
    server_metadata,
    speak,
)


def test_server_metadata_lists_required_tools() -> None:
    meta = server_metadata()
    assert "speak" in meta["tools"]
    assert "clone_from_wav" in meta["tools"]


@pytest.mark.asyncio
async def test_fastmcp_registers_tools() -> None:
    tools = await mcp.list_tools()
    names = {tool.name for tool in tools}
    assert {"speak", "clone_from_wav", "list_presets", "list_voices", "privacy_status"} <= names


def test_speak_tool(rail_home: Path, tmp_path: Path) -> None:
    dest = tmp_path / "mcp.wav"
    raw = speak(
        "Narrate the thread on-device.",
        preset="ct_hot_take",
        format="wav",
        output_path=str(dest),
    )
    payload = json.loads(raw)
    assert dest.is_file()
    assert payload["preset"] == "ct_hot_take"
    assert payload["offline"] is True


def test_clone_tool(rail_home: Path, sample_wav: Path) -> None:
    raw = clone_from_wav(str(sample_wav), name="mcp-voice", notes="from test")
    payload = json.loads(raw)
    assert payload["id"] == "mcp-voice"
    assert "stub" in payload["clone_status"]


def test_list_helpers(rail_home: Path) -> None:
    presets = json.loads(list_presets())
    assert len(presets) == 3
    voices = json.loads(list_voices())
    assert any(item["id"] == "klm" for item in voices)
    status = json.loads(privacy_status())
    assert status["cloud_tts"] is False
