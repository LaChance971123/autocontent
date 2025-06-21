import os
from pathlib import Path
import logging
import tempfile
import whisper
from dotenv import load_dotenv
import subprocess

# Setup
load_dotenv()
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMP_DIR = PROJECT_ROOT / "temp"
LOG_PATH = PROJECT_ROOT / "logs/runtime.log"
TEMP_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(filename=LOG_PATH, level=logging.INFO)

# Subtitle style constants
SUBTITLE_FONT = "Bangers"
SUBTITLE_POSITION = "center"
SUBTITLE_SIZE = "48"

def transcribe_audio_to_srt(audio_path):
    try:
        model = whisper.load_model("base")
        result = model.transcribe(str(audio_path))
        segments = result['segments']
        return segments
    except Exception as e:
        logging.error(f"Whisper transcription failed: {e}")
        return []

def generate_ass_file(segments, output_path):
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("[Script Info]\n")
            f.write("ScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n\n")
            f.write("[V4+ Styles]\n")
            f.write("Format: Name, Fontname, Fontsize, PrimaryColour, BackColour, Bold, Italic, "
                    "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, "
                    "Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n")
            f.write(f"Style: Default,{SUBTITLE_FONT},{SUBTITLE_SIZE},&H00FFFFFF,&H00000000,0,0,0,0,100,100,"
                    f"0,0,1,3,1,2,30,30,100,1\n\n")

            f.write("[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")

            for segment in segments:
                start = format_time(segment['start'])
                end = format_time(segment['end'])
                text = segment['text'].replace("\n", " ").strip()
                f.write(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\n")
        logging.info(f"ASS subtitle file created at {output_path}")
    except Exception as e:
        logging.error(f"Failed to write ASS file: {e}")

def format_time(seconds):
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 100)
    return f"{hrs:01d}:{mins:02d}:{secs:02d}.{ms:02d}"

def generate_subtitles(audio_path, output_path):
    try:
        segments = transcribe_audio_to_srt(audio_path)
        if not segments:
            print("[ERROR] No segments returned from Whisper.")
            return
        generate_ass_file(segments, output_path)
    except Exception as e:
        logging.error(f"Subtitle generation failed: {e}")
