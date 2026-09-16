"""Delivery presets for CT / loom / security VO.

Presets scale a voice profile — they never upload, and they never replace
the cloned register. A hotter take still sounds like the same speaker.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Preset:
    id: str
    label: str
    description: str
    f0_scale: float
    rate: float
    pause_scale: float
    brightness: float
    intensity: float
    style_notes: str
    use_when: str

    def to_dict(self) -> dict:
        return asdict(self)


PRESETS: dict[str, Preset] = {
    "ct_hot_take": Preset(
        id="ct_hot_take",
        label="CT hot take",
        description=(
            "Punchy Crypto Twitter energy — faster, brighter, shorter pauses. "
            "Built for threads, quote-tweet VO, and 15-second reply clips."
        ),
        f0_scale=1.14,
        rate=1.24,
        pause_scale=0.52,
        brightness=1.28,
        intensity=0.88,
        style_notes="Lead with the take. No throat-clearing. End on the line they will screenshot.",
        use_when="Narrating a thread, dunk, or market-structure hot take.",
    ),
    "protocol_explainer": Preset(
        id="protocol_explainer",
        label="Protocol explainer",
        description=(
            "Calm loom / tutorial cadence — slower, lower, room to breathe. "
            "Built for architecture walkthroughs and docs narration."
        ),
        f0_scale=0.94,
        rate=0.86,
        pause_scale=1.32,
        brightness=0.92,
        intensity=0.72,
        style_notes="Define the term once. Then show the flow. Pause after each step.",
        use_when="Loom scripts, README walkthroughs, protocol explainers.",
    ),
    "security_psa": Preset(
        id="security_psa",
        label="Security PSA",
        description=(
            "Measured incident voice — lowest pitch, deliberate cadence. "
            "Built for phishing warnings, key-safety, and exploit-adjacent PSAs."
        ),
        f0_scale=0.80,
        rate=0.76,
        pause_scale=1.58,
        brightness=0.74,
        intensity=0.80,
        style_notes="State the risk, the action, then stop. Do not hedge the warning.",
        use_when="Security PSAs, incident notes, wallet-safety Shorts.",
    ),
}

DEFAULT_PRESET_ID = "protocol_explainer"


def get_preset(preset_id: str | None) -> Preset:
    if not preset_id:
        return PRESETS[DEFAULT_PRESET_ID]
    key = preset_id.strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "hot_take": "ct_hot_take",
        "ct": "ct_hot_take",
        "explainer": "protocol_explainer",
        "loom": "protocol_explainer",
        "psa": "security_psa",
        "security": "security_psa",
    }
    key = aliases.get(key, key)
    if key not in PRESETS:
        known = ", ".join(PRESETS)
        raise ValueError(f"Unknown preset {preset_id!r}. Choose one of: {known}")
    return PRESETS[key]


def list_presets() -> list[dict]:
    return [preset.to_dict() for preset in PRESETS.values()]
