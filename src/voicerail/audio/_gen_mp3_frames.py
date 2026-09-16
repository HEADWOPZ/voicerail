"""Dev helper: bake short MPEG frames for the no-ffmpeg MP3 fallback.

Run from a machine with ffmpeg:  python -m voicerail.audio._gen_mp3_frames
"""

from __future__ import annotations

import math
import subprocess
import tempfile
import wave
from pathlib import Path


SAMPLE_RATE = 22050
FRAME_SAMPLES = 576  # MPEG-2 Layer III granule; we encode 2 granules = 1152
WINDOW = 1152


def _sine_wav(path: Path, freq: float, amplitude: float) -> None:
    samples = bytearray()
    for i in range(WINDOW):
        t = i / SAMPLE_RATE
        # Hann window so frames concatenate without clicks.
        w = 0.5 - 0.5 * math.cos(2 * math.pi * i / (WINDOW - 1))
        value = int(max(-32767, min(32767, amplitude * w * math.sin(2 * math.pi * freq * t) * 32767)))
        samples += int(value).to_bytes(2, "little", signed=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        handle.writeframes(bytes(samples))


def _encode(wav_path: Path, mp3_path: Path) -> bytes:
    cmd = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(wav_path),
        "-codec:a",
        "libmp3lame",
        "-b:a",
        "64k",
        "-ac",
        "1",
        "-ar",
        str(SAMPLE_RATE),
        "-write_xing",
        "0",
        "-id3v2_version",
        "0",
        str(mp3_path),
    ]
    subprocess.run(cmd, check=True)
    data = mp3_path.read_bytes()
    # Strip a leading ID3 tag if ffmpeg still wrote one.
    if data.startswith(b"ID3"):
        size = (data[6] << 21) | (data[7] << 14) | (data[8] << 7) | data[9]
        data = data[10 + size :]
    return data


def main() -> None:
    freqs = [0, 90, 110, 140, 180, 220, 280, 360, 480, 640, 880, 1200]
    amps = [0.0, 0.22, 0.45, 0.75]
    frames: dict[str, bytes] = {}
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for freq in freqs:
            for amp in amps:
                if freq == 0 and amp != 0.0:
                    continue
                if freq != 0 and amp == 0.0:
                    continue
                wav_path = root / f"{freq}_{amp}.wav"
                mp3_path = root / f"{freq}_{amp}.mp3"
                _sine_wav(wav_path, float(freq), float(amp))
                payload = _encode(wav_path, mp3_path)
                frames[f"{freq}:{amp}"] = payload
                print(f"{freq}:{amp} -> {len(payload)} bytes")

    out = Path(__file__).with_name("_mp3_frames.py")
    lines = [
        '"""Auto-generated MPEG-2 Layer III tiles. Do not edit by hand."""',
        "",
        "from __future__ import annotations",
        "",
        f"SAMPLE_RATE = {SAMPLE_RATE}",
        f"WINDOW = {WINDOW}",
        "",
        "FRAMES: dict[str, bytes] = {",
    ]
    for key, payload in frames.items():
        lines.append(f"    {key!r}: {payload!r},")
    lines.append("}")
    lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
