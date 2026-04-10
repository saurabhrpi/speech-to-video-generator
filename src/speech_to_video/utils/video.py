import os
import shutil
import subprocess
import tempfile
import time
from typing import List, Optional, Dict, Any, Union

import requests


def _unique_stitched_path() -> str:
    """Return a unique path like clips/stitched/stitched-{timestamp}.mp4"""
    stitched_dir = os.path.join(os.path.abspath(os.getcwd()), "clips", "stitched")
    os.makedirs(stitched_dir, exist_ok=True)
    filename = f"stitched-{int(time.time())}.mp4"
    return os.path.join(stitched_dir, filename)


def stitch_videos(video_urls: List[str]) -> Optional[str]:
    """
    Stitch remote video URLs into a single local file using moviepy if available.
    Falls back to returning the first URL if stitching is unavailable or fails.
    """
    if not video_urls:
        return None

    try:
        from moviepy import VideoFileClip, concatenate_videoclips
    except Exception:
        # moviepy/ffmpeg not available; return None so caller can surface error
        return None

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

        # Load and concatenate with gentle crossfade for continuity
        clips = [VideoFileClip(p) for p in local_paths]
        if len(clips) >= 2:
            try:
                fade = 0.5
                mod: List = []
                for i, c in enumerate(clips):
                    d = max(0.1, min(fade, (c.duration or 0.6) * 0.25))
                    if i > 0:
                        try:
                            c = c.crossfadein(d)
                        except Exception:
                            pass
                        try:
                            c = c.audio_fadein(d)
                        except Exception:
                            pass
                    if i < len(clips) - 1:
                        try:
                            c = c.audio_fadeout(d)
                        except Exception:
                            pass
                    mod.append(c)
                final = concatenate_videoclips(mod, method="compose", padding=-d)
            except Exception:
                final = concatenate_videoclips(clips, method="compose")
        else:
            final = concatenate_videoclips(clips, method="compose")
        output_path = os.path.join(temp_dir, "stitched.mp4")
        final.write_videofile(output_path, codec="libx264", audio_codec="aac")

        # Close clips to release file handles on Windows
        try:
            final.close()
        except Exception:
            pass
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
        return None
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


def stitch_videos_detailed(video_urls: List[str]) -> Dict[str, Any]:
    """
    Detailed variant that returns success flag and error info instead of silently
    falling back. Downloads each URL, concatenates, and returns the output path.
    """
    result: Dict[str, Any] = {"success": False, "output_path": None, "segments": [], "attempted_urls": list(video_urls), "error": None}
    if not video_urls:
        result["error"] = "No video URLs provided"
        return result

    try:
        from moviepy import VideoFileClip, concatenate_videoclips
    except Exception as e:
        result["error"] = f"moviepy/ffmpeg unavailable: {e}"
        return result

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

        result["segments"] = list(local_paths)

        # Load and concatenate with gentle crossfade for continuity
        clips = [VideoFileClip(p) for p in local_paths]
        if len(clips) >= 2:
            try:
                fade = 0.5
                mod: List = []
                for i, c in enumerate(clips):
                    d = max(0.1, min(fade, (c.duration or 0.6) * 0.25))
                    if i > 0:
                        try:
                            c = c.crossfadein(d)
                        except Exception:
                            pass
                        try:
                            c = c.audio_fadein(d)
                        except Exception:
                            pass
                    if i < len(clips) - 1:
                        try:
                            c = c.audio_fadeout(d)
                        except Exception:
                            pass
                    mod.append(c)
                final = concatenate_videoclips(mod, method="compose", padding=-d)
            except Exception:
                final = concatenate_videoclips(clips, method="compose")
        else:
            final = concatenate_videoclips(clips, method="compose")
        output_path = os.path.join(temp_dir, "stitched.mp4")
        final.write_videofile(output_path, codec="libx264", audio_codec="aac")

        # Close
        try:
            final.close()
        except Exception:
            pass
        for c in clips:
            try:
                c.close()
            except Exception:
                pass

        destination = _unique_stitched_path()
        shutil.move(output_path, destination)
        result["success"] = True
        result["output_path"] = destination
        result["filename"] = os.path.basename(destination)
        return result
    except Exception as e:
        result["error"] = str(e)
        return result
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


def stitch_videos_seamless(video_urls: List[str]) -> Dict[str, Any]:
    """
    Seamless stitching for continuous videos - NO visual crossfade, only subtle audio fades.
    This creates an invisible transition, making the result appear as one continuous clip.
    """
    result: Dict[str, Any] = {
        "success": False,
        "output_path": None,
        "segments": [],
        "attempted_urls": list(video_urls),
        "error": None,
    }
    if not video_urls:
        result["error"] = "No video URLs provided"
        return result

    try:
        from moviepy import VideoFileClip, concatenate_videoclips
    except Exception as e:
        result["error"] = f"moviepy/ffmpeg unavailable: {e}"
        return result

    temp_dir = tempfile.mkdtemp(prefix="video_seamless_")
    local_paths: List[str] = []
    clips = []

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

        result["segments"] = list(local_paths)

        # Load clips
        clips = [VideoFileClip(p) for p in local_paths]

        # Apply ONLY subtle audio fades at boundaries (no visual crossfade)
        # This prevents audio pops/clicks without any visible transition
        if len(clips) >= 2:
            mod: List = []
            audio_fade = 0.15  # Very short audio fade (150ms) - just enough to prevent clicks
            for i, c in enumerate(clips):
                # Only apply audio fades, NO visual effects
                if c.audio is not None:
                    try:
                        if i > 0:
                            # Fade in audio at the start of clips after the first
                            c = c.audio_fadein(audio_fade)
                        if i < len(clips) - 1:
                            # Fade out audio at the end of clips before the last
                            c = c.audio_fadeout(audio_fade)
                    except Exception:
                        pass
                mod.append(c)
            # Concatenate with NO padding (hard cut) - the clips should flow seamlessly
            final = concatenate_videoclips(mod, method="compose")
        else:
            final = concatenate_videoclips(clips, method="compose")

        output_path = os.path.join(temp_dir, "stitched.mp4")
        final.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            fps=30,  # Consistent framerate
            preset="ultrafast",  # Fast encoding for Replit/cloud
            bitrate="4000k",  # Good quality, faster encoding
        )

        # Close handles
        try:
            final.close()
        except Exception:
            pass
        for c in clips:
            try:
                c.close()
            except Exception:
                pass

        destination = _unique_stitched_path()
        shutil.move(output_path, destination)

        result["success"] = True
        result["output_path"] = destination
        result["filename"] = os.path.basename(destination)
        return result

    except Exception as e:
        result["error"] = str(e)
        return result

    finally:
        # Close any remaining clips
        for c in clips:
            try:
                c.close()
            except Exception:
                pass
        # Cleanup temp files (stitch_videos_seamless)
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


def stitch_timelapse_clips(
    video_sources: List[str],
    speed: float = 1.5,
    dissolve: bool = False,
    dissolve_duration: float = 0.3,
    hold_first_frame: float = 0.0,
) -> Dict[str, Any]:
    """
    Stitch timelapse transition clips with speed adjustment via a single ffmpeg call.
    Accepts URLs or local file paths.
    hold_first_frame: seconds to hold the first frame as a still before the transitions.

    `dissolve` and `dissolve_duration` are kept for signature compatibility but are
    currently no-ops; both production call sites pass dissolve=False.

    Why ffmpeg instead of moviepy: moviepy issues many small random reads on the
    source clip files. On filesystems backed by a network block device (e.g. Replit
    /tmp), every cache miss pays a network round-trip, which made stitching take
    ~25 minutes. ffmpeg's filter graph reads each input mostly sequentially, so
    kernel readahead amortizes the round-trips and we no longer need to land temp
    files on /dev/shm.
    """
    result: Dict[str, Any] = {
        "success": False,
        "output_path": None,
        "segments": [],
        "speed": speed,
        "error": None,
    }
    if not video_sources:
        result["error"] = "No video sources provided"
        return result

    try:
        from imageio_ffmpeg import get_ffmpeg_exe
        ffmpeg_bin = get_ffmpeg_exe()
    except Exception as e:
        result["error"] = f"ffmpeg unavailable: {e}"
        return result

    temp_dir = tempfile.mkdtemp(prefix="timelapse_stitch_")
    local_paths: List[str] = []

    try:
        # Download (or copy) each source to temp_dir. Sequential writes are
        # cheap on every filesystem including NBD-backed /tmp.
        for idx, src in enumerate(video_sources):
            local_path = os.path.join(temp_dir, f"segment_{idx}.mp4")
            if src.startswith("http"):
                with requests.get(src, stream=True, timeout=120) as r:
                    r.raise_for_status()
                    with open(local_path, "wb") as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
            elif os.path.isfile(src):
                shutil.copy2(src, local_path)
            else:
                result["error"] = f"Invalid video source: {src}"
                return result
            local_paths.append(local_path)

        result["segments"] = list(local_paths)

        # Build filter_complex: per-input setpts (speed) + tpad on first clip
        # (hold_first_frame), then concat all video streams. tpad runs AFTER
        # setpts so the held duration is in output time, matching the prior
        # moviepy behavior (a literal `hold_first_frame` seconds in the output).
        n = len(local_paths)
        filter_parts: List[str] = []
        for i in range(n):
            stages: List[str] = []
            if speed != 1.0:
                stages.append(f"setpts=PTS/{speed}")
            if i == 0 and hold_first_frame > 0:
                stages.append(
                    f"tpad=start_duration={hold_first_frame}:start_mode=clone"
                )
            chain = ",".join(stages) if stages else "null"
            filter_parts.append(f"[{i}:v]{chain}[v{i}]")

        concat_inputs = "".join(f"[v{i}]" for i in range(n))
        filter_parts.append(f"{concat_inputs}concat=n={n}:v=1:a=0[outv]")
        filter_complex = ";".join(filter_parts)

        output_path = os.path.join(temp_dir, "timelapse.mp4")
        cmd: List[str] = [ffmpeg_bin, "-y"]
        for p in local_paths:
            cmd.extend(["-i", p])
        cmd.extend([
            "-filter_complex", filter_complex,
            "-map", "[outv]",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-b:v", "4000k",
            "-pix_fmt", "yuv420p",
            "-r", "30",
            "-an",
            output_path,
        ])

        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if proc.returncode != 0:
            stderr = proc.stderr.decode("utf-8", errors="replace")
            tail = stderr.strip().splitlines()[-20:]
            result["error"] = "ffmpeg failed:\n" + "\n".join(tail)
            return result

        destination = _unique_stitched_path()
        shutil.move(output_path, destination)

        result["success"] = True
        result["output_path"] = destination
        result["filename"] = os.path.basename(destination)
        return result

    except Exception as e:
        result["error"] = str(e)
        return result

    finally:
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

