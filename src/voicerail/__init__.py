"""VoiceRail — local voice-clone MCP for CT creators."""

from __future__ import annotations

__version__ = "0.1.0"
__all__ = ["__version__", "VoiceRail"]


def __getattr__(name: str):
    if name == "VoiceRail":
        from voicerail.service import VoiceRail

        return VoiceRail
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
