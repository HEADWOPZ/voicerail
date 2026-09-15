"""On-disk layout. Everything stays under the local VoiceRail home."""

from __future__ import annotations

import os
from pathlib import Path


def default_home() -> Path:
    override = os.environ.get("VOICERAIL_HOME")
    if override:
        return Path(override).expanduser()
    xdg = os.environ.get("XDG_DATA_HOME")
    if xdg:
        return Path(xdg).expanduser() / "voicerail"
    return Path.home() / ".voicerail"


def ensure_layout(home: Path) -> dict[str, Path]:
    voices = home / "voices"
    exports = home / "exports"
    cache = home / "cache"
    for path in (voices, exports, cache):
        path.mkdir(parents=True, exist_ok=True)
    return {"home": home, "voices": voices, "exports": exports, "cache": cache}
