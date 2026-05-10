"""Smoke test for extract_first_frame (AIV-13).

Validates:
1. Local-file path -> PNG with dimensions matching source.
2. URL path (via in-process http.server) -> PNG with dimensions matching source.
3. Optional thumbnail resize -> PNG at the requested size.

Usage:
    .venv/bin/python scripts/test_extract_first_frame.py
"""
from __future__ import annotations

import http.server
import os
import re
import socketserver
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.speech_to_video.utils.video import extract_first_frame  # noqa: E402
from imageio_ffmpeg import get_ffmpeg_exe  # noqa: E402
from PIL import Image  # noqa: E402

SAMPLE_VIDEO = ROOT / "debug" / "Dance_Video.mp4"


def video_dimensions(path):
    proc = subprocess.run(
        [get_ffmpeg_exe(), "-i", str(path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stderr = proc.stderr.decode("utf-8", errors="replace")
    m = re.search(r"Stream.*?Video.*?(\d{2,5})x(\d{2,5})", stderr)
    if not m:
        raise RuntimeError(f"Could not parse dimensions:\n{stderr}")
    return int(m.group(1)), int(m.group(2))


def png_dimensions(path):
    with Image.open(path) as img:
        return img.size


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args, **kwargs):
        pass


def main():
    if not SAMPLE_VIDEO.exists():
        print(f"FAIL: sample video not found at {SAMPLE_VIDEO}")
        return 1

    src_w, src_h = video_dimensions(SAMPLE_VIDEO)
    print(f"Source: {SAMPLE_VIDEO.relative_to(ROOT)}  {src_w}x{src_h}")

    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "local.png")
        extract_first_frame(str(SAMPLE_VIDEO), out)
        w, h = png_dimensions(out)
        assert (w, h) == (src_w, src_h), f"local: {w}x{h} != {src_w}x{src_h}"
        print(f"PASS [local]     {w}x{h}")

        os.chdir(ROOT)
        httpd = socketserver.TCPServer(("127.0.0.1", 0), QuietHandler)
        port = httpd.server_address[1]
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        try:
            url = f"http://127.0.0.1:{port}/debug/Dance_Video.mp4"
            out = os.path.join(tmp, "url.png")
            extract_first_frame(url, out)
            w, h = png_dimensions(out)
            assert (w, h) == (src_w, src_h), f"url: {w}x{h} != {src_w}x{src_h}"
            print(f"PASS [url]       {w}x{h}")
        finally:
            httpd.shutdown()

        out = os.path.join(tmp, "thumb.png")
        extract_first_frame(str(SAMPLE_VIDEO), out, thumbnail_size=(320, 180))
        w, h = png_dimensions(out)
        assert (w, h) == (320, 180), f"thumbnail: {w}x{h} != 320x180"
        print(f"PASS [thumb]     {w}x{h}")

    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
