"""VoiceRail command line — speak, clone, list, or serve MCP on stdio."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from voicerail import __version__
from voicerail.service import VoiceRail


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0
    try:
        return args.func(args)
    except Exception as exc:  # noqa: BLE001 — CLI boundary
        print(f"voicerail: {exc}", file=sys.stderr)
        return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="voicerail",
        description=(
            "Local voice-clone MCP. Narrate CT threads, loom scripts, and "
            "Shorts VO without shipping audio to the cloud."
        ),
    )
    parser.add_argument("--version", action="version", version=f"voicerail {__version__}")
    parser.add_argument(
        "--home",
        default=None,
        help="Override VOICERAIL_HOME (voices + exports stay here)",
    )
    parser.add_argument(
        "--engine",
        default=None,
        choices=("mock", "local", "auto"),
        help="Inference engine. mock is the GPU-free CI path (default).",
    )
    sub = parser.add_subparsers(dest="command")

    speak = sub.add_parser("speak", help="Synthesize text to wav or mp3")
    speak.add_argument("text", help="Script to narrate")
    speak.add_argument(
        "-p",
        "--preset",
        default=None,
        help="ct_hot_take | protocol_explainer | security_psa",
    )
    speak.add_argument("-v", "--voice", default=None, help="Registered voice id (default: klm)")
    speak.add_argument(
        "-f",
        "--format",
        dest="fmt",
        default=None,
        choices=("wav", "mp3"),
        help="Export format (default: wav)",
    )
    speak.add_argument("-o", "--output", default=None, help="Output path")
    speak.set_defaults(func=_cmd_speak)

    clone = sub.add_parser("clone", help="Register a local WAV as a voice profile (acoustic stub)")
    clone.add_argument("wav", help="Path to a 16-bit WAV sample")
    clone.add_argument("-n", "--name", default=None, help="Voice id / label")
    clone.add_argument("--notes", default="", help="Optional note stored with the profile")
    clone.set_defaults(func=_cmd_clone)

    presets = sub.add_parser("presets", help="List delivery presets")
    presets.set_defaults(func=_cmd_presets)

    voices = sub.add_parser("voices", help="List registered voices")
    voices.set_defaults(func=_cmd_voices)

    privacy = sub.add_parser("privacy", help="Show the local-only privacy status")
    privacy.set_defaults(func=_cmd_privacy)

    mcp = sub.add_parser("mcp", help="Run the MCP server on stdio (Claude / Cursor / Hermes)")
    mcp.set_defaults(func=_cmd_mcp)

    return parser


def _rail(args: argparse.Namespace) -> VoiceRail:
    home = Path(args.home).expanduser() if args.home else None
    return VoiceRail(home=home, engine=args.engine)


def _cmd_speak(args: argparse.Namespace) -> int:
    result = _rail(args).speak(
        args.text,
        preset=args.preset,
        voice=args.voice,
        fmt=args.fmt,
        output_path=args.output,
    )
    print(result.to_json())
    return 0


def _cmd_clone(args: argparse.Namespace) -> int:
    payload = _rail(args).clone_from_wav(args.wav, name=args.name, notes=args.notes)
    print(json.dumps(payload, indent=2))
    return 0


def _cmd_presets(args: argparse.Namespace) -> int:
    print(json.dumps(_rail(args).list_presets(), indent=2))
    return 0


def _cmd_voices(args: argparse.Namespace) -> int:
    print(json.dumps(_rail(args).list_voices(), indent=2))
    return 0


def _cmd_privacy(args: argparse.Namespace) -> int:
    print(json.dumps(_rail(args).privacy_status(), indent=2))
    return 0


def _cmd_mcp(args: argparse.Namespace) -> int:
    from voicerail.mcp_server import run_stdio

    run_stdio(home=Path(args.home).expanduser() if args.home else None, engine=args.engine)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
