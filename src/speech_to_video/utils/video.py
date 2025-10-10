import os
import shutil
import tempfile
from typing import List, Optional

import requests


def stitch_videos(video_urls: List[str]) -> Optional[str]:
    """
    Stitch remote video URLs into a single local file using moviepy if available.
    Falls back to returning the first URL if stitching is unavailable or fails.
    """
    if not video_urls:
        return None

    try:
        from moviepy.editor import VideoFileClip, concatenate_videoclips
    except Exception:
        # moviepy/ffmpeg not available; return the first URL as a fallback
        return video_urls[0]

    temp_dir = tempfile.mkdtemp(prefix="video_stitch_")
    local_paths: List[str] = []
    try:
        # Download segments
        for idx, url in enumerate(video_urls):
            local_path = os.path.join(temp_dir, f"segment_{idx}.mp4")
            with requests.get(url, stream=True, timeout=120) as r:
                r.raise_for_status()
                with open(local_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            local_paths.append(local_path)

        # Load and concatenate
        clips = [VideoFileClip(p) for p in local_paths]
        final = concatenate_videoclips(clips, method="compose")
        output_path = os.path.join(temp_dir, "stitched.mp4")
        final.write_videofile(output_path, codec="libx264", audio_codec="aac")

        # Close clips to release file handles on Windows
        for c in clips:
            try:
                c.close()
            except Exception:
                pass

        # Move stitched file to project root for convenience
        destination = os.path.abspath("stitched_output.mp4")
        try:
            if os.path.exists(destination):
                os.remove(destination)
        except Exception:
            pass
        shutil.move(output_path, destination)
        return destination
    except Exception:
        return video_urls[0]
    finally:
        # Cleanup temp files
        for p in local_paths:
            try:
                if os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass


