"""Subtitle generation using WhisperX."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from .utils import get_test_mode, save_ass_subtitles

logger = logging.getLogger(__name__)


def generate_subtitles(
    audio_path: Path, subtitle_path: Path, *, test_mode: Optional[bool] = None
) -> None:
    """Generate subtitles for ``audio_path`` and write to ``subtitle_path``.

    When ``test_mode`` is True, an empty subtitle file is created instead of
    running WhisperX.
    """
    if test_mode is None:
        test_mode = get_test_mode()

    subtitle_path = Path(subtitle_path)
    subtitle_path.parent.mkdir(parents=True, exist_ok=True)

    if test_mode:
        subtitle_path.write_text("", encoding="utf-8")
        logger.info("Dummy subtitles written to %s", subtitle_path)
        return

    try:
        import torch
        import whisperx

        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = whisperx.load_model("large-v3", device, compute_type="float32")

        result = model.transcribe(str(audio_path))
        model_a, metadata = whisperx.load_align_model(
            language_code=result["language"], device=device
        )
        result_aligned = whisperx.align(
            result["segments"], model_a, metadata, str(audio_path), device
        )
        save_ass_subtitles(result_aligned["word_segments"], subtitle_path)
        logger.info("Subtitles saved to %s", subtitle_path)
    except Exception as exc:
        logger.error("Failed to generate subtitles: %s", exc)
        raise

