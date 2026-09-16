"""In-memory mono PCM. No third-party audio stack required."""

from __future__ import annotations

import math
from array import array
from dataclasses import dataclass


@dataclass
class AudioClip:
    samples: array
    sample_rate: int
    channels: int = 1

    def __post_init__(self) -> None:
        if self.channels != 1:
            raise ValueError("VoiceRail ships mono clips only")
        if self.sample_rate <= 0:
            raise ValueError("sample_rate must be positive")
        if not isinstance(self.samples, array) or self.samples.typecode != "h":
            self.samples = array("h", (int(_clamp_i16(v)) for v in self.samples))

    @property
    def duration_seconds(self) -> float:
        if self.sample_rate == 0:
            return 0.0
        return len(self.samples) / float(self.sample_rate)

    @property
    def peak(self) -> int:
        return max((abs(s) for s in self.samples), default=0)

    @property
    def rms(self) -> float:
        if not self.samples:
            return 0.0
        acc = 0
        for sample in self.samples:
            acc += sample * sample
        return math.sqrt(acc / len(self.samples))

    def to_bytes(self) -> bytes:
        return self.samples.tobytes()


def _clamp_i16(value: float) -> int:
    if value > 32767:
        return 32767
    if value < -32768:
        return -32768
    return int(round(value))


def floats_to_clip(frames: list[float], sample_rate: int, peak: float = 0.86) -> AudioClip:
    if not frames:
        return AudioClip(array("h"), sample_rate)
    max_abs = max(abs(x) for x in frames) or 1.0
    scale = (32767.0 * peak) / max_abs
    samples = array("h", (_clamp_i16(x * scale) for x in frames))
    return AudioClip(samples, sample_rate)


def estimate_f0(clip: AudioClip, min_hz: float = 70.0, max_hz: float = 280.0) -> float | None:
    """Autocorrelation pitch estimate. Returns None on silence or noise."""
    n = len(clip.samples)
    if n < clip.sample_rate // 10:
        return None
    start = n // 4
    end = start + min(n // 2, clip.sample_rate)
    window = clip.samples[start:end]
    if not window:
        return None
    mean = sum(window) / len(window)
    centered = [s - mean for s in window]
    energy = sum(x * x for x in centered)
    if energy < 1e-6:
        return None
    min_lag = max(1, int(clip.sample_rate / max_hz))
    max_lag = min(len(centered) // 2, int(clip.sample_rate / min_hz))
    best_lag = 0
    best_corr = 0.0
    for lag in range(min_lag, max_lag + 1):
        corr = 0.0
        limit = len(centered) - lag
        for i in range(limit):
            corr += centered[i] * centered[i + lag]
        if corr > best_corr:
            best_corr = corr
            best_lag = lag
    if best_lag == 0 or best_corr < 0.15 * energy:
        return None
    return clip.sample_rate / float(best_lag)
