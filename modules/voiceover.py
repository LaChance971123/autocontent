import os
from pathlib import Path
import subprocess
import logging
import json
import requests
from dotenv import load_dotenv

from modules.utils import get_logger, ErrorCode, get_test_mode

# Load environment variables from .env
load_dotenv()

# Logger setup
logger = get_logger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMP_DIR = PROJECT_ROOT / "temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Dummy audio generator

def generate_dummy_audio(path: Path) -> None:
    """
    Generate a 1-second silent WAV file for testing.
    """
    try:
        import wave, struct
        with wave.open(str(path), 'w') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(44100)
            duration_seconds = 1
            silence = [0] * int(44100 * duration_seconds)
            wf.writeframes(b''.join(struct.pack('<h', s) for s in silence))
        logger.info(f"Dummy audio generated at {path}")
    except Exception as e:
        logger.error(f"Failed to generate dummy audio: {e}")

# ElevenLabs API interaction

def call_elevenlabs_api(text: str, output_path: Path) -> bool:
    api_key = os.getenv("ELEVENLABS_API_KEY")
    voice_id = os.getenv("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")

    if not api_key:
        logger.error(f"{ErrorCode.ELEVENLABS_FAIL.value}: Missing API key")
        return False

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
    payload = {"text": text, "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}}

    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            logger.info(f"ElevenLabs API MP3 saved to {output_path}")
            return True
        else:
            logger.error(f"{ErrorCode.ELEVENLABS_FAIL.value}: API error {response.status_code} - {response.text}")
            return False
    except Exception as e:
        logger.error(f"{ErrorCode.ELEVENLABS_FAIL.value}: Exception during API call: {e}")
        return False

# Audio conversion

def convert_mp3_to_wav(mp3_path: Path, wav_path: Path) -> bool:
    """
    Convert an MP3 file to a 44.1kHz mono WAV using ffmpeg.
    """
    try:
        subprocess.run([
            "ffmpeg", "-y",
            "-i", str(mp3_path),
            "-ar", "44100",
            "-ac", "1",
            str(wav_path)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logger.info(f"Converted MP3 to WAV: {wav_path}")
        mp3_path.unlink(missing_ok=True)
        return True
    except Exception as e:
        logger.error(f"{ErrorCode.VIDEO_RENDER_FAIL.value}: FFmpeg conversion failed: {e}")
        return False

# Main generator

def generate_voiceover(script_text: str, output_path: Path, *, test_mode: bool | None = None) -> None:
    """
    Generate voiceover audio. In test mode, write dummy WAV; otherwise,
    fetch MP3 from ElevenLabs then convert to WAV.
    """
    if test_mode is None:
        test_mode = get_test_mode()

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if test_mode:
        logger.info("Test mode active: generating dummy audio")
        generate_dummy_audio(output_path)
        return

    # 1) fetch raw MP3 from ElevenLabs
    mp3_path = output_path.with_suffix(".mp3")
    logger.info("Calling ElevenLabs API for MP3...")
    if not call_elevenlabs_api(script_text, mp3_path):
        raise RuntimeError(ErrorCode.ELEVENLABS_FAIL.value)

    # 2) convert to WAV
    logger.info("Converting MP3 to WAV...")
    if not convert_mp3_to_wav(mp3_path, output_path):
        raise RuntimeError(ErrorCode.ELEVENLABS_FAIL.value)

    logger.info(f"Voiceover ready at {output_path}")
