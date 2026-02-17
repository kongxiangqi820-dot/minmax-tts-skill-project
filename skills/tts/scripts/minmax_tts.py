#!/usr/bin/env python3
"""MiniMax Text-to-Speech helper.

Convert text into audio by calling MiniMax T2A HTTP API.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.request


DEFAULT_ENDPOINT = "https://api.minimax.io/v1/t2a_v2"
DEFAULT_MODEL = "speech-2.8-hd"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Call MiniMax TTS and save audio file.")
    parser.add_argument("--text", help="Text content to synthesize.")
    parser.add_argument("--text-file", help="Read text from file.")
    parser.add_argument("--voice-id", required=True, help="MiniMax voice ID.")
    parser.add_argument("--output", required=True, help="Output audio file path.")
    parser.add_argument("--format", default="mp3", choices=["mp3", "wav", "flac", "pcm"])
    parser.add_argument("--model", default=DEFAULT_MODEL, help="MiniMax TTS model.")
    parser.add_argument("--sample-rate", type=int, default=32000)
    parser.add_argument("--bitrate", type=int, default=128000)
    parser.add_argument("--channel", type=int, default=1)
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--volume", type=float, default=1.0)
    parser.add_argument("--pitch", type=int, default=0)
    parser.add_argument("--language-boost", default="auto")
    parser.add_argument("--output-format", default="hex", choices=["hex", "url"])
    parser.add_argument("--endpoint", default=os.getenv("MINMAX_TTS_ENDPOINT", DEFAULT_ENDPOINT))
    parser.add_argument("--api-key", default=os.getenv("MINMAX_API_KEY", ""))
    parser.add_argument("--timeout", type=int, default=60)
    return parser.parse_args()


def read_text(args: argparse.Namespace) -> str:
    if bool(args.text) == bool(args.text_file):
        raise ValueError("Provide exactly one of --text or --text-file.")

    if args.text:
        text = args.text.strip()
    else:
        text = Path(args.text_file).read_text(encoding="utf-8").strip()

    if not text:
        raise ValueError("Input text is empty.")
    return text


def build_payload(text: str, args: argparse.Namespace) -> dict:
    return {
        "model": args.model,
        "text": text,
        "stream": False,
        "language_boost": args.language_boost,
        "voice_setting": {
            "voice_id": args.voice_id,
            "speed": args.speed,
            "vol": args.volume,
            "pitch": args.pitch,
        },
        "audio_setting": {
            "sample_rate": args.sample_rate,
            "bitrate": args.bitrate,
            "format": args.format,
            "channel": args.channel,
        },
        "output_format": args.output_format,
    }


def call_minimax(payload: dict, args: argparse.Namespace) -> dict:
    if not args.api_key:
        raise ValueError("Missing API key. Set MINMAX_API_KEY or pass --api-key.")

    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        args.endpoint,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {args.api_key}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=args.timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw)
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"HTTP {exc.code}: {details}") from exc


def decode_audio_field(audio_value: str) -> bytes:
    try:
        return bytes.fromhex(audio_value)
    except ValueError:
        return base64.b64decode(audio_value)


def save_audio(resp: dict, args: argparse.Namespace) -> Path:
    base_resp = resp.get("base_resp", {})
    status_code = base_resp.get("status_code", 0)
    if status_code != 0:
        status_msg = base_resp.get("status_msg", "unknown error")
        raise RuntimeError(f"MiniMax error: status_code={status_code}, status_msg={status_msg}")

    data = resp.get("data") or {}
    audio = data.get("audio")
    if not audio:
        raise RuntimeError("Response missing data.audio.")

    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.output_format == "url":
        with urllib.request.urlopen(audio, timeout=args.timeout) as downloaded:
            content = downloaded.read()
    else:
        content = decode_audio_field(audio)

    output_path.write_bytes(content)
    return output_path


def main() -> int:
    args = parse_args()
    try:
        text = read_text(args)
        payload = build_payload(text, args)
        resp = call_minimax(payload, args)
        output_path = save_audio(resp, args)
        result = {
            "ok": True,
            "output_path": str(output_path),
            "voice_id": args.voice_id,
            "format": args.format,
            "bytes": output_path.stat().st_size,
        }
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
