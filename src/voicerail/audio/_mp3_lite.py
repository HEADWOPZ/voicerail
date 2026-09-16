"""No-binary MP3 writer. Concatenates pre-encoded MPEG-2 Layer III tiles."""

from __future__ import annotations

from array import array

from voicerail.audio._mp3_frames import FRAMES, SAMPLE_RATE, WINDOW
from voicerail.audio.pcm import AudioClip

_FREQS = sorted({int(float(key.split(":")[0])) for key in FRAMES})
_AMPS = sorted({float(key.split(":")[1]) for key in FRAMES if not key.startswith("0:")})


def encode_mpeg1_layer3(clip: AudioClip) -> bytes:
    mono = _resample(clip.samples, clip.sample_rate, SAMPLE_RATE)
    if not mono:
        mono = array("h", [0] * WINDOW)
    # Pad to a whole number of frames so players do not clip the tail.
    remainder = len(mono) % WINDOW
    if remainder:
        mono.extend([0] * (WINDOW - remainder))
    chunks: list[bytes] = []
    for offset in range(0, len(mono), WINDOW):
        window = mono[offset : offset + WINDOW]
        chunks.append(_tile_for(window))
    return b"".join(chunks)


def _resample(samples: array, src_rate: int, dst_rate: int) -> array:
    if src_rate == dst_rate:
        return array("h", samples)
    if not samples:
        return array("h")
    ratio = dst_rate / float(src_rate)
    out_len = max(1, int(round(len(samples) * ratio)))
    out = array("h")
    last = len(samples) - 1
    for i in range(out_len):
        pos = i / ratio
        left = int(pos)
        if left >= last:
            out.append(samples[last])
            continue
        frac = pos - left
        value = samples[left] * (1.0 - frac) + samples[left + 1] * frac
        out.append(int(value))
    return out


def _tile_for(window: array) -> bytes:
    peak = max((abs(s) for s in window), default=0)
    amp = peak / 32767.0
    if amp < 0.02:
        return FRAMES["0:0.0"]
    freq = _zero_cross_freq(window)
    nearest_freq = min(_FREQS[1:], key=lambda candidate: abs(candidate - freq))
    nearest_amp = min(_AMPS, key=lambda candidate: abs(candidate - amp))
    key = f"{nearest_freq}:{nearest_amp}"
    return FRAMES.get(key, FRAMES["0:0.0"])


def _zero_cross_freq(window: array) -> float:
    crossings = 0
    prev = window[0]
    for sample in window[1:]:
        if (prev >= 0 > sample) or (prev < 0 <= sample):
            crossings += 1
        prev = sample
    seconds = len(window) / float(SAMPLE_RATE)
    if seconds <= 0:
        return 110.0
    return max(70.0, min(1400.0, (crossings / 2.0) / seconds))
