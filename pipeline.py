"""High level pipeline orchestration for AutoContent."""

from pathlib import Path
import logging
import uuid
import argparse

from modules.voiceover import generate_voiceover
from modules.generate_subtitles import generate_subtitles
from modules.render_video import render_final_video
from modules.utils import get_test_mode

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_pipeline(
    script_path: Path,
    background_video: Path,
    output_dir: Path,
    *,
    job_id: str | None = None,
    test_mode: bool | None = None,
) -> Path:
    """Run the full pipeline and return the rendered video path.

    Parameters
    ----------
    script_path : Path
        Path to the text script input.
    background_video : Path
        Path to the background video file.
    output_dir : Path
        Directory where job results will be written.
    job_id : str, optional
        Identifier for this run. A UUID will be generated if omitted.
    test_mode : bool, optional
        When True, heavy operations are skipped and dummy files created.
    """

    if test_mode is None:
        test_mode = get_test_mode()

    job_id = job_id or uuid.uuid4().hex
    temp_dir = Path("temp") / job_id
    final_dir = output_dir / job_id

    temp_dir.mkdir(parents=True, exist_ok=True)
    final_dir.mkdir(parents=True, exist_ok=True)

    audio_file = temp_dir / "voice.wav"
    subtitles_file = temp_dir / "subtitles.ass"
    final_video = final_dir / "final_render.mp4"

    logger.info("[%s] Generating voiceover", job_id)
    script_text = Path(script_path).read_text(encoding="utf-8")
    generate_voiceover(script_text, audio_file, test_mode=test_mode)

    logger.info("[%s] Generating subtitles", job_id)
    generate_subtitles(audio_file, subtitles_file, test_mode=test_mode)

    logger.info("[%s] Rendering final video", job_id)
    render_final_video(
        background_video, audio_file, subtitles_file, final_video, test_mode=test_mode
    )

    logger.info("[%s] Pipeline complete -> %s", job_id, final_video)
    return final_video


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the AutoContent pipeline")
    parser.add_argument("script", type=Path)
    parser.add_argument("background", type=Path)
    parser.add_argument("output", type=Path, nargs="?", default=Path("output"))
    parser.add_argument("--job-id", dest="job_id")
    args = parser.parse_args()

    run_pipeline(args.script, args.background, args.output, job_id=args.job_id)


if __name__ == "__main__":
    main()

