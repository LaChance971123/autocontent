
import subprocess
from pathlib import Path

from .utils import get_logger, ErrorCode

logger = get_logger(__name__)

def render_final_video(background_video, audio_file, subtitle_file, output_path):
    logger.info(f"Using background video: {background_video}")
    logger.info(f"Using audio file: {audio_file}")
    logger.info(f"Using subtitle file: {subtitle_file}")
    logger.info(f"Output path: {output_path}")

    background_video = Path(background_video).resolve()
    audio_file = Path(audio_file).resolve()
    subtitle_file = Path(subtitle_file).resolve()
    output_path = Path(output_path).resolve()

    if not background_video.exists():
        logger.error(f"{ErrorCode.BACKGROUND_NOT_FOUND.value}: {background_video}")
        raise FileNotFoundError(ErrorCode.BACKGROUND_NOT_FOUND.value)
    if not audio_file.exists():
        logger.error(f"{ErrorCode.ELEVENLABS_FAIL.value}: audio missing {audio_file}")
        raise FileNotFoundError(ErrorCode.ELEVENLABS_FAIL.value)
    if not subtitle_file.exists():
        logger.error(f"{ErrorCode.WHISPERX_FAIL.value}: subtitle missing {subtitle_file}")
        raise FileNotFoundError(ErrorCode.WHISPERX_FAIL.value)

    subtitle_path_escaped = str(subtitle_file).replace('\\', '/').replace(':', '\\:')

    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-i", str(background_video),
        "-i", str(audio_file),
        "-filter_complex",
        f"[0:v]scale=1080:1920,setsar=1,subtitles='{subtitle_path_escaped}'[v]",
        "-map", "[v]",
        "-map", "1:a",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-shortest",
        str(output_path)
    ]

    try:
        subprocess.run(ffmpeg_cmd, check=True)
        logger.info(f"Final video rendered: {output_path}")
    except subprocess.CalledProcessError as e:
        logger.error(f"{ErrorCode.RENDER_FAIL.value}: {e}")
        raise RuntimeError(ErrorCode.RENDER_FAIL.value) from e

