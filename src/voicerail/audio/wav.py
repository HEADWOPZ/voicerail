"""Read/write 16-bit PCM WAV with the stdlib only."""

from __future__ import annotations

import wave
from array import array
from pathlib import Path

from voicerail.audio.pcm import AudioClip


def write_wav(clip: AudioClip, path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(clip.channels)
        handle.setsampwidth(2)
        handle.setframerate(clip.sample_rate)
        handle.writeframes(clip.to_bytes())
    return path


def read_wav(path: Path) -> AudioClip:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"WAV not found: {path}")
    with wave.open(str(path), "rb") as handle:
        channels = handle.getnchannels()
        width = handle.getsampwidth()
        rate = handle.getframerate()
        frames = handle.readframes(handle.getnframes())
    if width != 2:
        raise ValueError(
            f"{path} is {width * 8}-bit PCM. VoiceRail clone_from_wav wants 16-bit WAV."
        )
    samples = array("h")
    samples.frombytes(frames)
    if channels == 1:
        return AudioClip(samples, rate, 1)
    if channels < 1:
        raise ValueError(f"{path} has no audio channels")
    # Downmix interleaved multi-channel to mono.
    mono = array("h")
    total = len(samples) // channels
    for i in range(total):
        acc = 0
        base = i * channels
        for ch in range(channels):
            acc += samples[base + ch]
        mono.append(int(acc / channels))
    return AudioClip(mono, rate, 1)
