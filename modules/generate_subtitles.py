import os
import whisperx
import torch
from modules.utils import save_ass_subtitles

def generate_subtitles(audio_path, subtitle_path):
    print("Transcribing with WhisperX + alignment for word-level timestamps...")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = whisperx.load_model("large-v3", device, compute_type="float32")

    result = model.transcribe(audio_path)
    model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
    result_aligned = whisperx.align(result["segments"], model_a, metadata, audio_path, device)

    print(f"Improved karaoke-style subtitles saved to {subtitle_path}")
    save_ass_subtitles(result_aligned["word_segments"], subtitle_path)

if __name__ == "__main__":
    generate_subtitles("temp/voice.wav", "temp/subtitles.ass")
