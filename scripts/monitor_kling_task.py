"""Monitor a Kling Motion Control task until terminal state, download on success.

Push-style alternative to inline polling inside a chain script. Designed to be
launched as `bash run_in_background` from Claude Code — the harness notifies the
assistant when this script exits, so the conversation only re-enters when there's
something to act on (no inline 600s polls eating conversation context).

Exit codes:
    0 = Kling task SUCCEED; video downloaded to --out-path
    1 = Kling task FAILED (Kling-side error or download error)
    2 = HUNG (updated_at hasn't advanced for >--hang-threshold seconds)
    3 = TIMEOUT (>--max-wait seconds without terminal state)

Per Memory/reference_kling_task_hang_detection.md, hung tasks aren't charged
by Kling, so a hang-detected exit (code 2) is safe to retry by re-submitting.

Usage:
    .venv/bin/python scripts/monitor_kling_task.py \\
        --task-id 888806253990903823 \\
        --out-path ~/Downloads/seteadora_chain.mp4
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env", override=True)
sys.path.insert(0, str(ROOT / "src"))

import requests  # noqa: E402

from speech_to_video.clients.kling_motion_client import KlingMotionClient  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task-id", required=True)
    ap.add_argument(
        "--out-path", required=True, help="MP4 destination on success."
    )
    ap.add_argument(
        "--poll-interval", type=int, default=30,
        help="Seconds between status polls (default: 30).",
    )
    ap.add_argument(
        "--max-wait", type=int, default=1800,
        help="Hard wallclock cap in seconds (default: 1800 = 30 min).",
    )
    ap.add_argument(
        "--hang-threshold", type=int, default=300,
        help="If updated_at doesn't advance for this many seconds, treat as hung (default: 300).",
    )
    args = ap.parse_args()

    out_path = Path(args.out_path).expanduser()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    client = KlingMotionClient()
    t_start = time.time()
    last_updated_at: int | None = None
    last_change_t = t_start

    print(
        f"MONITOR  task_id={args.task_id}  poll={args.poll_interval}s  "
        f"max_wait={args.max_wait}s  hang_threshold={args.hang_threshold}s",
        flush=True,
    )

    while True:
        elapsed = time.time() - t_start
        if elapsed > args.max_wait:
            print(
                f"TIMEOUT  task_id={args.task_id}  elapsed={elapsed:.0f}s",
                flush=True,
            )
            return 3

        r = client.poll(args.task_id)
        data = r.get("data") or {}
        status = str(data.get("task_status", "")).lower()
        updated_at = data.get("updated_at")

        print(
            f"  poll  status={status}  updated_at={updated_at}  elapsed={elapsed:.0f}s",
            flush=True,
        )

        if status == "succeed":
            task_result = data.get("task_result") or {}
            videos = task_result.get("videos") or []
            if not videos:
                print(
                    f"FAIL  task_id={args.task_id}  succeed but no videos in task_result",
                    flush=True,
                )
                return 1
            video = videos[0]
            video_url = video.get("url")
            if not video_url:
                print(
                    f"FAIL  task_id={args.task_id}  video entry missing url",
                    flush=True,
                )
                return 1
            print(f"DOWNLOAD  {video_url} -> {out_path}", flush=True)
            try:
                with requests.get(video_url, stream=True, timeout=60) as resp:
                    resp.raise_for_status()
                    with open(out_path, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=64 * 1024):
                            f.write(chunk)
            except requests.RequestException as e:
                print(
                    f"FAIL  task_id={args.task_id}  download error: {e}",
                    flush=True,
                )
                return 1
            print(
                f"PASS  task_id={args.task_id}  video_url={video_url}  "
                f"path={out_path}  duration={video.get('duration')}s  "
                f"elapsed={elapsed:.0f}s",
                flush=True,
            )
            return 0

        if status == "failed":
            msg = data.get("task_status_msg") or r
            print(
                f"FAIL  task_id={args.task_id}  error={msg}  elapsed={elapsed:.0f}s",
                flush=True,
            )
            return 1

        # Hang detection — updated_at should advance as Kling makes progress
        if last_updated_at is None:
            last_updated_at = updated_at
            last_change_t = time.time()
        elif updated_at != last_updated_at:
            last_updated_at = updated_at
            last_change_t = time.time()
        else:
            stuck_for = time.time() - last_change_t
            if stuck_for > args.hang_threshold:
                print(
                    f"HANG  task_id={args.task_id}  "
                    f"updated_at stuck at {updated_at} for {stuck_for:.0f}s",
                    flush=True,
                )
                return 2

        time.sleep(args.poll_interval)


if __name__ == "__main__":
    raise SystemExit(main())
