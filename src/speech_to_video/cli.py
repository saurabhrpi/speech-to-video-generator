import argparse
import sys

from .services.video_service import VideoService


def _cmd_transcribe(args) -> int:
    system = VideoService()
    result = system.openai_client.transcribe(args.audio)
    print(result.get("text", ""))
    return 0


def _cmd_generate(args) -> int:
    system = VideoService()
    result = system.generate_video(prompt=args.prompt, duration=args.duration, quality=args.quality)
    print(result)
    return 0 if result.get("success") else 1


def _cmd_speech_to_video(args) -> int:
    system = VideoService()
    result = system.speech_to_video_with_audio(audio_path=args.audio, duration=args.duration, quality=args.quality)
    print(result)
    return 0 if result.get("success") else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Speech to Video CLI (WAN 2.1 Turbo pipeline)")
    sub = parser.add_subparsers(dest="command", required=True)

    p1 = sub.add_parser("transcribe", help="Transcribe an audio file")
    p1.add_argument("--audio", required=True, help="Path to audio file")
    p1.set_defaults(func=_cmd_transcribe)

    p2 = sub.add_parser("generate", help="Generate video from a prompt")
    p2.add_argument("--prompt", required=True, help="Prompt text")
    p2.add_argument("--duration", type=int, default=10)
    p2.add_argument("--quality", choices=["high", "medium"], default="high")
    p2.set_defaults(func=_cmd_generate)

    p3 = sub.add_parser("speech-to-video", help="Transcribe and generate video from speech")
    p3.add_argument("--audio", required=True, help="Path to audio file")
    p3.add_argument("--duration", type=int, default=60)
    p3.add_argument("--quality", choices=["high", "medium"], default="high")
    p3.set_defaults(func=_cmd_speech_to_video)

    return parser


def main(argv=None) -> int:
    argv = argv or sys.argv[1:]
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())


