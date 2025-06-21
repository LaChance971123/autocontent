"""Video rendering helpers using FFmpeg."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Optional

from .utils import get_test_mode

logger = logging.getLogger(__name__)


def render_final_video(
    background_video: Path,
    audio_file: Path,
    subtitle_file: Path,
    output_path: Path,
    *,
    test_mode: Optional[bool] = None,
) -> None:
    """Render the final video using FFmpeg."""

    if test_mode is None:
        test_mode = get_test_mode()

    background_video = Path(background_video).resolve()
    audio_file = Path(audio_file).resolve()
    subtitle_file = Path(subtitle_file).resolve()
    output_path = Path(output_path).resolve()

    if not background_video.exists():
        logger.error("Background video not found: %s", background_video)
        return
    if not audio_file.exists():
        logger.error("Audio file not found: %s", audio_file)
        return
    if not subtitle_file.exists():
        logger.error("Subtitle file not found: %s", subtitle_file)
        return

    subtitle_path_escaped = str(subtitle_file).replace("\\", "/").replace(":", "\\:")

    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(background_video),
        "-i",
        str(audio_file),
        "-filter_complex",
        f"[0:v]scale=1080:1920,setsar=1,subtitles='{subtitle_path_escaped}'[v]",
        "-map",
        "[v]",
        "-map",
        "1:a",
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-shortest",
        str(output_path),
    ]

    if test_mode:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("", encoding="utf-8")
        logger.info("Dummy video created at %s", output_path)
        return

    try:
        subprocess.run(ffmpeg_cmd, check=True)
        logger.info("Final video rendered: %s", output_path)
    except subprocess.CalledProcessError as exc:
        logger.error("FFmpeg rendering failed: %s", exc)

