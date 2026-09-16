"""MCP server for Claude, Cursor, and Hermes.

Tools stay local. The host talks stdio; audio never leaves the box.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP

from voicerail import __version__
from voicerail.service import VoiceRail

mcp = FastMCP(
    "VoiceRail",
    instructions=(
        "VoiceRail narrates text on-device for Kevin Lance Murray / CT creators. "
        "Use speak() to render wav/mp3. Use clone_from_wav() to register a local "
        "sample (acoustic stub — see the disclaimer it returns). Presets: "
        "ct_hot_take, protocol_explainer, security_psa. Complements AlphaClip Forge. "
        "Never suggest uploading audio to a cloud TTS."
    ),
)


def _rail() -> VoiceRail:
    # Fresh settings each call so VOICERAIL_* env changes (and tests) apply.
    return VoiceRail()


@mcp.tool()
def speak(
    text: str,
    preset: str = "protocol_explainer",
    voice: str = "klm",
    format: str = "wav",
    output_path: Optional[str] = None,
) -> str:
    """Synthesize speech locally and export WAV or MP3.

    Privacy: inference stays on this machine. Audio is not uploaded.
    GPU is not required when the mock engine is active (the default).

    Presets
    - ct_hot_take: punchy Crypto Twitter / thread VO
    - protocol_explainer: loom, docs, architecture walkthrough
    - security_psa: measured incident / wallet-safety VO
    """
    result = _rail().speak(
        text,
        preset=preset,
        voice=voice,
        fmt=format,
        output_path=output_path,
    )
    return result.to_json()


@mcp.tool()
def clone_from_wav(
    wav_path: str,
    name: Optional[str] = None,
    notes: str = "",
) -> str:
    """Register a local voice profile from a 16-bit WAV sample.

    This MVP path is an acoustic stub: VoiceRail measures pitch and energy
    and stores a JSON profile under VOICERAIL_HOME. It does not train
    neural speaker weights and it does not upload the WAV. The mock engine
    then speaks in that register. Piper/XTTS can later read the same profile.
    """
    import json

    payload = _rail().clone_from_wav(wav_path, name=name, notes=notes)
    return json.dumps(payload, indent=2)


@mcp.tool()
def list_presets() -> str:
    """List VoiceRail delivery presets (CT hot take, protocol explainer, security PSA)."""
    import json

    return json.dumps(_rail().list_presets(), indent=2)


@mcp.tool()
def list_voices() -> str:
    """List voice profiles stored on this machine."""
    import json

    return json.dumps(_rail().list_voices(), indent=2)


@mcp.tool()
def privacy_status() -> str:
    """Confirm VoiceRail is local-only: no cloud TTS, no telemetry, no GPU required for mock."""
    import json

    return json.dumps(_rail().privacy_status(), indent=2)


@mcp.resource("voicerail://privacy")
def privacy_resource() -> str:
    """Privacy contract and engine status."""
    import json

    return json.dumps(_rail().privacy_status(), indent=2)


@mcp.resource("voicerail://presets")
def presets_resource() -> str:
    """Preset catalog."""
    import json

    return json.dumps(_rail().list_presets(), indent=2)


@mcp.prompt()
def narrate_thread(topic: str, take: str) -> str:
    """Draft a CT thread VO, then speak it with the hot-take preset."""
    return (
        f"Write a tight Crypto Twitter thread VO about {topic}. "
        f"Core take: {take}. Short sentences. No hedging. "
        "Then call VoiceRail speak() with preset=ct_hot_take and format=wav. "
        "Do not send the script to a cloud TTS."
    )


@mcp.prompt()
def loom_script(feature: str) -> str:
    """Draft a loom / protocol explainer, then speak it."""
    return (
        f"Write a 60-90s loom script explaining {feature}. "
        "Define terms once, then walk the flow. "
        "Call VoiceRail speak() with preset=protocol_explainer. Keep audio local."
    )


@mcp.prompt()
def shorts_security_psa(risk: str) -> str:
    """Draft a security PSA Short, then speak it."""
    return (
        f"Write a 20-30s Shorts VO warning about {risk}. "
        "State the risk, the action, stop. "
        "Call VoiceRail speak() with preset=security_psa. Never upload the take."
    )


def run_stdio(home: Path | None = None, engine: str | None = None) -> None:
    """Entry used by `voicerail mcp`."""
    import os

    if home is not None:
        os.environ["VOICERAIL_HOME"] = str(home)
    if engine is not None:
        os.environ["VOICERAIL_ENGINE"] = engine
    mcp.run(transport="stdio")


def server_metadata() -> dict:
    return {
        "name": "VoiceRail",
        "version": __version__,
        "tools": ["speak", "clone_from_wav", "list_presets", "list_voices", "privacy_status"],
    }
