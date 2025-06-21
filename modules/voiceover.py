"""Voiceover generation using the ElevenLabs API."""

from __future__ import annotations

import os
from pathlib import Path
import logging
import requests
from dotenv import load_dotenv
import wave
import struct

load_dotenv()

logger = logging.getLogger(__name__)

from .utils import get_test_mode


def generate_dummy_audio(path: Path) -> None:
    """Generate a short silent WAV file at *path*."""
    try:
        with wave.open(str(path), "w") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(44100)
            duration_seconds = 2
            silence = [0] * int(44100 * duration_seconds)
            wf.writeframes(b"".join(struct.pack("<h", s) for s in silence))
        logger.info("Dummy audio generated at %s", path)
    except Exception as exc:
        logger.error("Failed to generate dummy audio: %s", exc)

def call_elevenlabs_api(text: str, output_path: Path) -> bool:
    """Call the ElevenLabs API and write the resulting audio to *output_path*.

    Returns True on success.
    """
    api_key = os.getenv("ELEVENLABS_API_KEY")
    voice_id = os.getenv("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")  # Default voice ID

    if not api_key:
        logger.error("ELEVENLABS_API_KEY not found in environment")
        return False

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            logger.info("Voiceover generated at %s", output_path)
            return True
        logger.error("ElevenLabs API Error %s: %s", response.status_code, response.text)
        return False
    except Exception as exc:
        logger.error("Exception during ElevenLabs call: %s", exc)
        return False

def generate_voiceover(script_text: str, output_path: Path, test_mode: bool | None = None) -> None:
    """Generate voiceover audio for *script_text* and write it to *output_path*.

    If *test_mode* is True, a silent audio file is generated instead of calling
    the ElevenLabs API. When *test_mode* is None, the value is determined from
    the ``TEST_MODE`` environment variable.
    """
    if test_mode is None:
        test_mode = get_test_mode()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if test_mode:
        logger.info("Test mode active: generating dummy audio")
        generate_dummy_audio(output_path)
    else:
        logger.info("Calling ElevenLabs API")
        success = call_elevenlabs_api(script_text, output_path)
        if not success:
            logger.error("Failed to generate voiceover")


