"""GPU-free formant synthesizer. Deterministic. Always available.

This is the CI / air-gap engine. It is not a neural clone — it is a
source-filter voice that speaks in a measured register so agents can
narrate threads without a GPU or a network.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

from voicerail.audio.pcm import AudioClip, floats_to_clip
from voicerail.engine.base import EngineInfo, TTSEngine
from voicerail.presets import Preset
from voicerail.voices import VoiceProfile

SAMPLE_RATE = 22050

# Classic three-formant targets (Hz). Enough to make vowels distinct.
_VOWELS = {
    "a": (730, 1090, 2440),
    "e": (530, 1840, 2480),
    "i": (270, 2290, 3010),
    "o": (570, 840, 2410),
    "u": (300, 870, 2240),
}

_CONSONANT_KIND = {
    "w": "glide",
    "y": "glide",
    "r": "glide",
    "l": "glide",
    "m": "nasal",
    "n": "nasal",
    "ng": "nasal",
    "v": "fricative",
    "f": "fricative",
    "s": "fricative",
    "z": "fricative",
    "h": "fricative",
    "th": "fricative",
    "sh": "fricative",
    "b": "stop",
    "d": "stop",
    "g": "stop",
    "p": "stop",
    "t": "stop",
    "k": "stop",
    "c": "stop",
    "q": "stop",
    "x": "fricative",
    "j": "glide",
}


@dataclass
class _Resonator:
    freq: float
    bandwidth: float
    y1: float = 0.0
    y2: float = 0.0

    def step(self, excitation: float, sample_rate: int) -> float:
        radius = math.exp(-math.pi * self.bandwidth / sample_rate)
        omega = 2.0 * math.pi * self.freq / sample_rate
        a1 = 2.0 * radius * math.cos(omega)
        a2 = -(radius * radius)
        y = excitation + a1 * self.y1 + a2 * self.y2
        self.y2 = self.y1
        self.y1 = y
        return y


class MockEngine(TTSEngine):
    id = "mock"

    def info(self) -> EngineInfo:
        return EngineInfo(
            id="mock",
            label="Mock formant TTS",
            offline=True,
            gpu_required=False,
            available=True,
            detail=(
                "On-device source-filter synthesizer. No model weights, no GPU, "
                "no network. Required CI path. Clone_from_wav only retunes pitch "
                "and energy — it does not copy a speaker's timbre."
            ),
        )

    def synthesize(self, text: str, voice: VoiceProfile, preset: Preset) -> AudioClip:
        phrase = _normalize(text)
        if not phrase:
            phrase = "…"
        f0 = max(70.0, min(260.0, voice.base_f0 * preset.f0_scale))
        units = _to_units(phrase)
        frames: list[float] = []
        phase = 0.0
        noise = 0.17
        resonators = [
            _Resonator(730, 90),
            _Resonator(1090, 110),
            _Resonator(2440, 170),
        ]
        unit_index = 0
        for unit in units:
            unit_index += 1
            duration = _duration_ms(unit, preset.rate, preset.pause_scale)
            n = max(1, int(SAMPLE_RATE * duration / 1000.0))
            # Gentle declination + deterministic micro-variation.
            local_f0 = f0 * (1.0 - 0.045 * (unit_index / max(1, len(units))))
            local_f0 *= 1.0 + 0.025 * math.sin(unit_index * 1.618)
            target = unit.formants
            for i in range(n):
                mix = i / max(1, n - 1)
                for resonator, dest in zip(resonators, target):
                    resonator.freq += (dest - resonator.freq) * 0.18
                if unit.kind == "pause":
                    frames.append(0.0)
                    continue
                phase += local_f0 / SAMPLE_RATE
                if phase >= 1.0:
                    phase -= 1.0
                # LF-ish glottal pulse: narrow duty cycle + a little aspiration.
                pulse = 1.0 if phase < 0.12 else 0.0
                noise = (noise * 1103515245 + 12345) % 2**31
                noise_n = (noise / 2**30) - 1.0
                if unit.kind == "fricative":
                    excitation = 0.55 * noise_n
                elif unit.kind == "stop":
                    excitation = pulse * (1.0 if mix < 0.18 else 0.08) + 0.08 * noise_n
                elif unit.kind == "nasal":
                    excitation = 0.65 * pulse + 0.05 * noise_n
                else:
                    excitation = pulse + 0.04 * noise_n
                voiced = 0.0
                gains = (0.55, 0.38 * preset.brightness, 0.16 * preset.brightness)
                for resonator, gain in zip(resonators, gains):
                    voiced += gain * resonator.step(excitation, SAMPLE_RATE)
                # Very light de-click envelope.
                env = 1.0
                attack = int(0.004 * SAMPLE_RATE)
                if i < attack:
                    env = i / max(1, attack)
                elif i > n - attack:
                    env = (n - i) / max(1, attack)
                frames.append(voiced * env * voice.intensity * preset.intensity)

        return floats_to_clip(frames, SAMPLE_RATE, peak=0.84)


def _normalize(text: str) -> str:
    cleaned = text.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    return cleaned.strip()


@dataclass(frozen=True)
class _Unit:
    kind: str
    formants: tuple[float, float, float]


def _to_units(text: str) -> list[_Unit]:
    units: list[_Unit] = []
    i = 0
    lower = text.lower()
    while i < len(lower):
        ch = lower[i]
        nxt = lower[i + 1] if i + 1 < len(lower) else ""
        if ch in " \n\t":
            units.append(_Unit("pause", (400, 800, 2000)))
        elif ch in ".,;:":
            units.append(_Unit("pause", (400, 800, 2000)))
            units.append(_Unit("pause", (400, 800, 2000)))
        elif ch in "!?":
            units.append(_Unit("pause", (400, 800, 2000)))
            units.append(_Unit("pause", (400, 800, 2000)))
            units.append(_Unit("pause", (400, 800, 2000)))
        elif ch in "aeiou":
            units.append(_Unit("vowel", _VOWELS[ch]))
        elif ch == "y" and (not units or units[-1].kind != "vowel"):
            units.append(_Unit("vowel", _VOWELS["i"]))
        elif ch + nxt in ("th", "sh", "ng"):
            units.append(_Unit(_CONSONANT_KIND[ch + nxt], (450, 1700, 2600)))
            i += 1
        elif ch.isalpha():
            kind = _CONSONANT_KIND.get(ch, "stop")
            units.append(_Unit(kind, (500, 1500, 2500)))
        elif ch.isdigit():
            units.extend(_to_units(_digit_word(ch)))
        i += 1
    if not units:
        units.append(_Unit("pause", (400, 800, 2000)))
    return units


def _digit_word(ch: str) -> str:
    return {
        "0": "zero",
        "1": "one",
        "2": "two",
        "3": "three",
        "4": "four",
        "5": "five",
        "6": "six",
        "7": "seven",
        "8": "eight",
        "9": "nine",
    }[ch]


def _duration_ms(unit: _Unit, rate: float, pause_scale: float) -> float:
    rate = max(0.45, rate)
    if unit.kind == "pause":
        return 95.0 * pause_scale
    if unit.kind == "vowel":
        return 78.0 / rate
    if unit.kind == "fricative":
        return 52.0 / rate
    if unit.kind == "nasal":
        return 58.0 / rate
    if unit.kind == "glide":
        return 48.0 / rate
    return 36.0 / rate
