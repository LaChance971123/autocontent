import os
import re
import json
import logging
import sys
from pathlib import Path
from datetime import datetime
from enum import Enum

LOG_COLORS = {
    logging.INFO: "\033[36m",    # Cyan
    logging.WARNING: "\033[33m", # Yellow
    logging.ERROR: "\033[31m",   # Red
}


class ErrorCode(str, Enum):
    SCRIPT_NOT_FOUND = "SCRIPT_NOT_FOUND"
    BACKGROUND_NOT_FOUND = "BACKGROUND_NOT_FOUND"
    ELEVENLABS_FAIL = "ELEVENLABS_FAIL"
    WHISPERX_FAIL = "WHISPERX_FAIL"
    RENDER_FAIL = "RENDER_FAIL"
    THUMBNAIL_FAIL = "THUMBNAIL_FAIL"
    COMPRESS_FAIL = "COMPRESS_FAIL"

class _ColorFormatter(logging.Formatter):
    def format(self, record):
        color = LOG_COLORS.get(record.levelno, "")
        reset = "\033[0m"
        record.levelname = f"{color}{record.levelname}{reset}"
        return super().format(record)

def get_logger(name: str) -> logging.Logger:
    """Return a configured logger with optional colored output."""
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(level)
        handler = logging.StreamHandler(sys.stdout)
        formatter = _ColorFormatter(
            "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
            datefmt="%H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


def is_api_mode(args=None) -> bool:
    """Return True if running in API mode based on env or CLI."""
    if args and getattr(args, "json", False):
        return True
    return os.getenv("API_MODE") == "1"

def get_test_mode() -> bool:
    """Return True if running in test mode based on state.json or env."""
    if os.getenv("TEST_MODE"):
        return os.getenv("TEST_MODE") == "1"
    try:
        with open("state.json", "r", encoding="utf-8") as f:
            state = json.load(f)
        return state.get("env", {}).get("test_mode", False)
    except Exception:
        return False

def save_ass_subtitles(segments, path):
    header = """[Script Info]
ScriptType: v4.00+
Collisions: Normal
PlayResX: 608
PlayResY: 1080
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Bangers,110,&H00FFFFFF,&H000000FF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,3,0,5,10,10,540,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    def to_ass_timestamp(seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centis = int((seconds - int(seconds)) * 100)
        return f"{hours:d}:{minutes:02d}:{secs:02d}.{centis:02d}"

    def remove_punctuation(text):
        return re.sub(r'[^\w\s]', '', text)

    body = ""
    for segment in segments:
        start = to_ass_timestamp(segment["start"])
        end = to_ass_timestamp(segment["end"])
        clean_word = remove_punctuation(segment["word"])
        text = clean_word.replace('\\', '\\\\').replace('{', '\{').replace('}', '\}')
        body += f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\\N\n"

    with open(path, "w", encoding="utf-8") as f:
        f.write(header + body)


def sanitize_name(name: str) -> str:
    """Return a filesystem-safe folder name"""
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", name.strip().lower())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned or "job"


def extract_title_and_stats(text: str):
    """Extract title and simple stats from text."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    title = lines[0] if lines else "untitled"
    words = text.split()
    word_count = len(words)
    char_count = len(text)
    try:
        from langdetect import detect

        language = detect(text)
    except Exception:
        language = "unknown"
    est_read_time = round(word_count / 180 * 60, 1)  # seconds
    return title, {
        "word_count": word_count,
        "char_count": char_count,
        "est_read_time": est_read_time,
        "language": language,
    }


def init_job_log(job_id: str, test_mode: bool):
    return {
        "job_id": job_id,
        "timestamp": datetime.utcnow().isoformat(),
        "test_mode": test_mode,
        "events": [],
        "errors": [],
        "output_files": {},
        "duration_sec": None,
    }


def save_job_log(log: dict, output_dir: Path):
    with open(Path(output_dir) / "log.json", "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2)
