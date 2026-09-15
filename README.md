# VoiceRail

**Local voice-clone MCP for Kevin Lance Murray / CT creators.**

Clone a register on-device. Let Claude, Cursor, or Hermes narrate threads, loom scripts, and Shorts VO **without shipping audio to the cloud**. Complements [AlphaClip Forge](https://github.com/HEADWOPZ) — Forge cuts the clip, VoiceRail speaks it.

Mock mode is first-class. It always works, needs no GPU, and is what CI runs.

## Why this exists

Cloud TTS is convenient and leaky. A thread VO, a protocol loom, or a wallet-safety PSA should not leave the desk. VoiceRail is a small Python MCP server plus a CLI:

1. **Mock engine** — GPU-free formant synthesizer (required, tested, default)
2. **Local wrapper** — Piper or eSpeak-ng when you install them; never a hosted API
3. **MCP tools** — `speak`, `clone_from_wav`, plus presets / voices / privacy
4. **Presets** — CT hot take · protocol explainer · security PSA
5. **Export** — WAV always; MP3 via ffmpeg/lame or the bundled fallback encoder

## Install

```bash
python -m pip install -e ".[dev]"
```

Python 3.10+. Optional: `ffmpeg` (better MP3) and `piper` or `espeak-ng` (local engine).

```bash
voicerail speak "Liquidity is a story. The bridge is the bug." \
  --preset ct_hot_take --format wav -o /tmp/take.wav
```

## MCP (Claude / Cursor / Hermes)

```bash
voicerail mcp
```

Cursor / Claude Desktop snippet (`examples/mcp.json`):

```json
{
  "mcpServers": {
    "voicerail": {
      "command": "voicerail",
      "args": ["mcp"],
      "env": {
        "VOICERAIL_ENGINE": "mock"
      }
    }
  }
}
```

### Tools

| Tool | What it does |
| --- | --- |
| `speak` | Render text to `wav` or `mp3` with a preset + voice |
| `clone_from_wav` | Register a local 16-bit WAV as a voice profile |
| `list_presets` | Catalog of delivery presets |
| `list_voices` | Profiles stored under `VOICERAIL_HOME` |
| `privacy_status` | Confirms offline / no telemetry / no cloud TTS |

Prompts ship for `narrate_thread`, `loom_script`, and `shorts_security_psa`.

### `clone_from_wav` is a stub — on purpose

The MVP does **not** train XTTS / RVC speaker weights. It reads the WAV on disk, estimates pitch and energy, and writes a JSON profile. The mock engine then speaks in that register.

That is honest: agents get a working clone hook, CI stays GPU-free, and the sample never uploads. A future local backend (Piper voice, XTTS-v2, RVC) is expected to read the same profile and `source_wav`. See [PRIVACY.md](PRIVACY.md).

## Presets

| Id | Feel | Use |
| --- | --- | --- |
| `ct_hot_take` | Faster, brighter, short pauses | Threads, quote-tweet VO, dunks |
| `protocol_explainer` | Slower, lower, room to breathe | Loom, docs, architecture |
| `security_psa` | Lowest pitch, deliberate | Phishing, key-safety, incident notes |

Presets **scale** a voice. A hotter take still sounds like the same speaker.

Factory voice: `klm` (Kevin Lance Murray) — baritone register at ~108 Hz. Replace it:

```bash
voicerail clone ~/booth/klm.wav --name klm
```

## Engines

| `VOICERAIL_ENGINE` | Behavior |
| --- | --- |
| `mock` (default) | Formant TTS. No models. No GPU. CI path. |
| `local` | Piper if present, else eSpeak-ng. Errors if neither — no cloud fallback. |
| `auto` | Local binary or mock. |

```bash
export VOICERAIL_HOME=~/.voicerail
export VOICERAIL_ENGINE=mock
export VOICERAIL_DEFAULT_PRESET=protocol_explainer
export VOICERAIL_PIPER_MODEL=/path/to/en_US-lessac-medium.onnx   # optional
```

## CLI

```bash
voicerail speak "Revoke the signer." -p security_psa -f mp3 -o psa.mp3
voicerail clone ./sample.wav -n klm
voicerail presets
voicerail voices
voicerail privacy
voicerail mcp
```

`python -m voicerail` is the same entry point.

## Tests

```bash
VOICERAIL_ENGINE=mock pytest
```

The suite is mock-only. It does not download weights and does not need a GPU.

## Layout

```
src/voicerail/
  mcp_server.py     FastMCP stdio server
  service.py        shared speak / clone / export
  engine/mock.py    GPU-free synthesizer
  engine/local.py   Piper / eSpeak wrapper
  audio/            wav + mp3 writers
  presets.py        the three delivery presets
  voices.py         local profile store + stub clone
```

## License

[MIT](LICENSE) © 2026 Kevin Lance Murray / HEADWOPZ
