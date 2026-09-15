"""MP3 export. Prefers ffmpeg/lame (real encode). Falls back to a valid CBR writer."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from voicerail.audio.pcm import AudioClip
from voicerail.audio.wav import write_wav


class Mp3EncodeError(RuntimeError):
    pass


def write_mp3(clip: AudioClip, path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if _encode_with_ffmpeg(clip, path):
        return path
    if _encode_with_lame(clip, path):
        return path
    _encode_fallback(clip, path)
    return path


def encoder_status() -> dict:
    return {
        "ffmpeg": bool(shutil.which("ffmpeg")),
        "lame": bool(shutil.which("lame")),
        "fallback": True,
        "note": (
            "WAV always works. MP3 uses ffmpeg or lame when present; "
            "otherwise VoiceRail writes a standards-compliant CBR MP3 via the built-in encoder."
        ),
    }


def _encode_with_ffmpeg(clip: AudioClip, path: Path) -> bool:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return False
    with tempfile.TemporaryDirectory(prefix="voicerail-mp3-") as tmp:
        wav_path = Path(tmp) / "clip.wav"
        write_wav(clip, wav_path)
        cmd = [
            ffmpeg,
            "-y",
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            str(wav_path),
            "-codec:a",
            "libmp3lame",
            "-q:a",
            "4",
            "-ac",
            "1",
            str(path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0 or not path.is_file() or path.stat().st_size < 32:
            return False
    return True


def _encode_with_lame(clip: AudioClip, path: Path) -> bool:
    lame = shutil.which("lame")
    if not lame:
        return False
    with tempfile.TemporaryDirectory(prefix="voicerail-lame-") as tmp:
        wav_path = Path(tmp) / "clip.wav"
        write_wav(clip, wav_path)
        cmd = [lame, "--quiet", "-m", "m", str(wav_path), str(path)]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0 or not path.is_file() or path.stat().st_size < 32:
            return False
    return True


def _encode_fallback(clip: AudioClip, path: Path) -> None:
    """Write a valid MPEG-1 Layer III CBR file from mono PCM.

    This is a deliberately small encoder so CI and air-gapped boxes can still
    export ``.mp3`` without ffmpeg. Quality is below libmp3lame; the container
    is a real MP3 (sync words, side info, Huffman-coded spectral lines).
    """
    from voicerail.audio._mp3_lite import encode_mpeg1_layer3

    data = encode_mpeg1_layer3(clip)
    path.write_bytes(data)
    if path.stat().st_size < 32:
        raise Mp3EncodeError("MP3 fallback encoder produced an empty file")
