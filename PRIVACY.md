# VoiceRail privacy

VoiceRail is a **local** voice tool. The product promise is that Claude, Cursor, and Hermes can narrate a thread, a loom script, or a Shorts VO **without shipping audio to a vendor**.

## What never leaves this machine

- Scripts passed to `speak`
- WAV samples passed to `clone_from_wav`
- Exported `.wav` / `.mp3` files
- Voice profiles under `VOICERAIL_HOME` (default `~/.voicerail`)

There is no cloud TTS fallback. There is no crash reporter. There is no usage telemetry. The MCP server speaks **stdio only** — the host process (Claude Desktop, Cursor, Hermes) already has the text; VoiceRail does not open an inference socket.

## What is stored locally

| Path | Contents |
| --- | --- |
| `$VOICERAIL_HOME/voices/*.json` | Voice profiles (pitch, energy, path to the source WAV) |
| `$VOICERAIL_HOME/exports/` | Default render destination when you omit `--output` |
| `$VOICERAIL_HOME/cache/` | Reserved for local engine scratch |

Delete the home directory to wipe VoiceRail's state. The source WAV you cloned is **not** copied unless you put it there yourself.

## Engines

| Engine | Network | GPU | Notes |
| --- | --- | --- | --- |
| `mock` (default) | none | none | Formant synthesizer. Required CI path. |
| `local` | none | none | Piper or eSpeak-ng on `PATH`. Errors if missing — it will not "helpfully" call ElevenLabs. |
| `auto` | none | none | Local binary if present, otherwise mock. |

`clone_from_wav` is an **acoustic stub** in this MVP: it measures pitch and energy from your WAV and stores a JSON profile. It does **not** upload the sample and it does **not** train neural speaker embeddings. That is documented on the tool itself so an agent cannot pretend it performed a cloud clone.

## What VoiceRail will not do

- Send audio or text to a hosted voice API
- Require a GPU for the supported mock path
- Bundle someone else's voice weights
- Phone home for "model updates"

If you wire a future XTTS / RVC backend, keep the weights and the sample directory on disk. Do not add a URL.

## Pairing with AlphaClip Forge

VoiceRail is the voice layer. AlphaClip Forge is the clip layer. Both are meant to stay on-device: Forge cuts the take, VoiceRail narrates it, the file never crosses the WAN.

## Contact

Issues: [github.com/HEADWOPZ/voicerail](https://github.com/HEADWOPZ/voicerail)
