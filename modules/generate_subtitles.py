from .utils import save_ass_subtitles, get_logger, get_test_mode, ErrorCode

logger = get_logger(__name__)

def _generate_dummy_subtitles(path: str):
    dummy = [
        {"start": 0.0, "end": 1.0, "word": "test"},
        {"start": 1.0, "end": 2.0, "word": "mode"},
    ]
    save_ass_subtitles(dummy, path)

def generate_subtitles(audio_path, subtitle_path, *, model_size: str = "large-v3", test_mode: bool | None = None):
    if test_mode is None:
        test_mode = get_test_mode()

    if test_mode:
        logger.info("Test mode active: using dummy subtitles and skipping WhisperX")
        _generate_dummy_subtitles(subtitle_path)
        return

    logger.info("Transcribing with WhisperX")
    import whisperx
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    try:
        model = whisperx.load_model(model_size, device, compute_type="float32")
        result = model.transcribe(audio_path)
        model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
        result_aligned = whisperx.align(result["segments"], model_a, metadata, audio_path, device)
        save_ass_subtitles(result_aligned["word_segments"], subtitle_path)
        logger.info(f"Subtitles saved to {subtitle_path}")
    except Exception as e:
        logger.error(f"{ErrorCode.WHISPERX_FAIL.value}: {e}")
        raise RuntimeError(ErrorCode.WHISPERX_FAIL.value) from e

if __name__ == "__main__":
    generate_subtitles("temp/voice.wav", "temp/subtitles.ass")
