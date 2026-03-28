"""Video frame extraction via ffmpeg.

Extracts a single representative JPEG from a video file, seeking to 10 % of
the total duration to avoid black leader frames at the start.
"""

import json
import subprocess


def extract_frame(video_path: str, output_path: str) -> None:
    """Extract a representative frame from *video_path* and write it to *output_path*.

    Raises:
        RuntimeError: if ffmpeg exits with a non-zero return code.
    """
    seek_time = _probe_seek_time(video_path)
    result = subprocess.run(
        [
            "ffmpeg", "-y",
            "-ss", str(seek_time),
            "-i", video_path,
            "-vframes", "1",
            "-q:v", "2",
            output_path,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg frame extraction failed:\n{result.stderr}")


def _probe_seek_time(video_path: str) -> float:
    """Return a seek time 10 % into the video, or 0.0 if probing fails."""
    try:
        probe = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                video_path,
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        info = json.loads(probe.stdout)
        duration = float(info["format"]["duration"])
        return duration * 0.1
    except Exception:
        return 0.0
