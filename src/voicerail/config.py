"""Environment-driven settings. No remote endpoints."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from voicerail.paths import default_home, ensure_layout

ENGINE_CHOICES = ("mock", "local", "auto")
FORMAT_CHOICES = ("wav", "mp3")
DEFAULT_VOICE = "klm"
DEFAULT_PRESET = "protocol_explainer"
DEFAULT_FORMAT = "wav"


@dataclass(frozen=True)
class Settings:
    home: Path
    engine: str
    default_voice: str
    default_preset: str
    default_format: str
    voices_dir: Path
    exports_dir: Path
    cache_dir: Path

    @classmethod
    def load(cls, home: Path | None = None) -> Settings:
        root = Path(home).expanduser() if home else default_home()
        layout = ensure_layout(root)
        engine = os.environ.get("VOICERAIL_ENGINE", "mock").strip().lower()
        if engine not in ENGINE_CHOICES:
            raise ValueError(
                f"VOICERAIL_ENGINE={engine!r} is not supported. "
                f"Use one of: {', '.join(ENGINE_CHOICES)}"
            )
        fmt = os.environ.get("VOICERAIL_FORMAT", DEFAULT_FORMAT).strip().lower()
        if fmt not in FORMAT_CHOICES:
            raise ValueError(
                f"VOICERAIL_FORMAT={fmt!r} is not supported. Use wav or mp3."
            )
        return cls(
            home=layout["home"],
            engine=engine,
            default_voice=os.environ.get("VOICERAIL_DEFAULT_VOICE", DEFAULT_VOICE),
            default_preset=os.environ.get("VOICERAIL_DEFAULT_PRESET", DEFAULT_PRESET),
            default_format=fmt,
            voices_dir=layout["voices"],
            exports_dir=layout["exports"],
            cache_dir=layout["cache"],
        )
