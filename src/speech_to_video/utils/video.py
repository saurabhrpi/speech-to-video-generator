import os
import shutil
import tempfile
from typing import List, Optional, Dict, Any

import requests


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

        destination = os.path.abspath("stitched_output.mp4")
        try:
            if os.path.exists(destination):
                os.remove(destination)
        except Exception:
            pass
        shutil.move(output_path, destination)
        result["success"] = True
        result["output_path"] = destination
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

        destination = os.path.abspath("stitched_output.mp4")
        try:
            if os.path.exists(destination):
                os.remove(destination)
        except Exception:
            pass
        shutil.move(output_path, destination)

        result["success"] = True
        result["output_path"] = destination
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

