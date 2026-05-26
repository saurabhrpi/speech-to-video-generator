"""Topaz Video API client — upscale a driving video on Topaz's cloud (S78).

Replaces the slow Replicate Real-ESRGAN path. Runs on Topaz's GPUs (NOT the
local M1). Built against the official OpenAPI schema (video-12-25-updated.yaml).

Standard flow (chosen over /video/express because POST create returns a FREE
cost estimate before any credits are spent):
  1. POST   /video/                      -> {requestId, estimates:{cost:[lo,hi] credits, time:[lo,hi] s}}  (FREE, no credits)
  2. PATCH  /video/{id}/accept           -> {uploadId, urls:[...]} (reserves credits; multi-part PUT URLs)
  3. PUT    urls[i]                       -> upload byte-range i; ETag returned in response header
  4. PATCH  /video/{id}/complete-upload/ -> {uploadResults:[{partNum,eTag}]} ; starts processing
  5. GET    /video/{id}/status           -> poll until status=="complete"; download at download.url

Auth: X-API-Key from TOPAZ_API_KEY (.env). Base: https://api.topazlabs.com
Status enum (lowercase): requested|accepted|initializing|preprocessing|
processing|postprocessing|complete|canceling|canceled|failed.

Usage:
  # FREE estimate only (no credits spent):
  .venv/bin/python scripts/upscale_topaz.py --input <file.mp4> --scale 2 --stop-after create
  # Full run:
  .venv/bin/python scripts/upscale_topaz.py --input <file.mp4> --output <out.mp4> --scale 2 --model prob-4
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env", override=True)

import imageio_ffmpeg  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

BASE = "https://api.topazlabs.com"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
USD_PER_CREDIT = 0.12  # Starter pay-as-you-go; just for display


def _api_key() -> str:
    k = os.environ.get("TOPAZ_API_KEY") or os.environ.get("TOPAZ_API_Key")
    if not k:
        print("FAIL  TOPAZ_API_KEY not in .env", file=sys.stderr)
        sys.exit(2)
    return k


def _headers(json_body: bool = True) -> dict:
    h = {"X-API-Key": _api_key(), "Accept": "application/json"}
    if json_body:
        h["Content-Type"] = "application/json"
    return h


def probe(path: Path) -> dict:
    out = subprocess.run([FFMPEG, "-hide_banner", "-i", str(path)],
                         capture_output=True, text=True).stderr
    m_res = re.search(r"(\d{2,5})x(\d{2,5})", out)
    m_fps = re.search(r"([\d.]+) fps", out)
    m_dur = re.search(r"Duration: (\d+):(\d+):([\d.]+)", out)
    if not (m_res and m_fps and m_dur):
        raise RuntimeError(f"could not parse ffmpeg probe:\n{out[-500:]}")
    w, h = int(m_res.group(1)), int(m_res.group(2))
    fps = float(m_fps.group(1))
    hh, mm, ss = m_dur.groups()
    duration = int(hh) * 3600 + int(mm) * 60 + float(ss)
    cnt = subprocess.run([FFMPEG, "-i", str(path), "-map", "0:v:0", "-c", "copy",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    fr = re.findall(r"frame=\s*(\d+)", cnt)
    frame_count = int(fr[-1]) if fr else int(round(duration * fps))
    ext = path.suffix.lstrip(".").lower()
    return {"width": w, "height": h, "fps": fps, "duration": duration,
            "frame_count": frame_count, "size": path.stat().st_size,
            "container": ext if ext in ("mp4", "mov", "mkv") else "mp4"}


def _even(n: int) -> int:
    return n if n % 2 == 0 else n + 1


def create_request(src: dict, scale: float, model: str) -> dict:
    body = {
        "source": {
            "container": src["container"],
            "size": src["size"],
            "duration": src["duration"],
            "frameCount": src["frame_count"],
            "frameRate": src["fps"],
            "resolution": {"width": src["width"], "height": src["height"]},
        },
        "filters": [{"model": model}],
        "output": {
            "resolution": {"width": _even(int(src["width"] * scale)),
                           "height": _even(int(src["height"] * scale))},
            "frameRate": src["fps"],
            "audioCodec": "AAC",
            "audioTransfer": "Copy",
            "videoEncoder": "H264",
            "videoProfile": "High",
            "dynamicCompressionLevel": "High",
            "container": "mp4",
        },
    }
    log.info("POST /video/ body:\n%s", json.dumps(body, indent=2))
    r = requests.post(f"{BASE}/video/", headers=_headers(), json=body, timeout=60)
    log.info("create -> HTTP %s\n%s", r.status_code, r.text[:1500])
    r.raise_for_status()
    return r.json()


def accept(rid: str) -> tuple[str, list]:
    r = requests.patch(f"{BASE}/video/{rid}/accept", headers=_headers(), timeout=60)
    log.info("accept -> HTTP %s\n%s", r.status_code, r.text[:1200])
    r.raise_for_status()
    d = r.json()
    urls = d.get("urls") or []
    if not urls:
        raise RuntimeError(f"no upload urls in accept response: {d}")
    return d.get("uploadId"), urls


def upload(file_path: Path, urls: list) -> list:
    data = file_path.read_bytes()
    n = len(urls)
    chunk = -(-len(data) // n)  # ceil
    results = []
    for i, url in enumerate(urls, 1):
        seg = data[(i - 1) * chunk: i * chunk]
        r = requests.put(url, data=seg, headers={"Content-Type": "video/mp4"}, timeout=600)
        etag = (r.headers.get("ETag") or r.headers.get("etag") or "").strip('"')
        log.info("PUT part %d/%d (%d bytes) -> HTTP %s  ETag=%s", i, n, len(seg), r.status_code, etag)
        r.raise_for_status()
        results.append({"partNum": i, "eTag": etag})
    return results


def complete_upload(rid: str, results: list) -> None:
    body = {"uploadResults": results}
    # NOTE: trailing slash on this path per the OpenAPI schema
    r = requests.patch(f"{BASE}/video/{rid}/complete-upload/", headers=_headers(), json=body, timeout=60)
    log.info("complete-upload -> HTTP %s\n%s", r.status_code, r.text[:600])
    r.raise_for_status()


def poll(rid: str, max_wait: int = 2400, interval: int = 15) -> str:
    start = time.time()
    while time.time() - start < max_wait:
        r = requests.get(f"{BASE}/video/{rid}/status", headers=_headers(), timeout=60)
        if r.status_code != 200:
            log.warning("status -> HTTP %s %s", r.status_code, r.text[:300])
            time.sleep(interval); continue
        d = r.json()
        st = d.get("status")
        log.info("status=%s progress=%s%%", st, d.get("progress"))
        if st == "complete":
            url = (d.get("download") or {}).get("url")
            if not url:
                raise RuntimeError(f"complete but no download.url: {d}")
            return url
        if st in ("failed", "canceled"):
            raise RuntimeError(f"job {st}: {d}")
        time.sleep(interval)
    raise RuntimeError(f"timed out after {max_wait}s")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--output")
    ap.add_argument("--scale", type=float, default=2.0)
    ap.add_argument("--model", default="prob-4",
                    help="Upscale model code (prob-4=Proteus v4 default; also rhea-1, iris-3, etc.)")
    ap.add_argument("--stop-after", choices=["create", "accept", "upload", "full"], default="full")
    args = ap.parse_args()

    inp = Path(args.input).expanduser()
    if not inp.exists():
        print(f"FAIL  input not found: {inp}", file=sys.stderr)
        return 2

    src = probe(inp)
    ow, oh = _even(int(src["width"] * args.scale)), _even(int(src["height"] * args.scale))
    log.info("source: %dx%d %.3ffps dur=%.2fs frames=%d size=%d -> output %dx%d (model=%s)",
             src["width"], src["height"], src["fps"], src["duration"], src["frame_count"],
             src["size"], ow, oh, args.model)

    created = create_request(src, args.scale, args.model)
    rid = created.get("requestId")
    est = created.get("estimates") or {}
    cost = est.get("cost") or []
    if cost:
        lo, hi = cost[0], cost[-1]
        print(f"PASS  create  requestId={rid}")
        print(f"      COST ESTIMATE: {lo}-{hi} credits  (~${lo*USD_PER_CREDIT:.2f}-${hi*USD_PER_CREDIT:.2f} at $0.12/credit Starter)")
        print(f"      TIME ESTIMATE: {est.get('time')} s")
    else:
        print(f"PASS  create  requestId={rid}  (no estimate returned: {created})")
    if args.stop_after == "create":
        print("      (create is FREE — no credits spent. Re-run without --stop-after to process.)")
        return 0

    upload_id, urls = accept(rid)
    print(f"PASS  accept  uploadId={upload_id}  parts={len(urls)}")
    if args.stop_after == "accept":
        return 0

    results = upload(inp, urls)
    complete_upload(rid, results)
    print(f"PASS  upload+complete  parts={len(results)}")
    if args.stop_after == "upload":
        return 0

    url = poll(rid)
    out = Path(args.output).expanduser() if args.output else inp.with_name(inp.stem + "_topaz.mp4")
    with requests.get(url, stream=True, timeout=600) as r:
        r.raise_for_status()
        with open(out, "wb") as f:
            for chunk in r.iter_content(64 * 1024):
                f.write(chunk)
    print(f"PASS  downloaded -> {out}  ({out.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
