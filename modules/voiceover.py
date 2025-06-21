import os
from pathlib import Path
import json
import requests
from dotenv import load_dotenv
import wave
import struct
from io import BytesIO
from pydub import AudioSegment

from .utils import get_logger, get_test_mode, ErrorCode

load_dotenv()

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMP_DIR = PROJECT_ROOT / "temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

logger = get_logger(__name__)

def generate_dummy_audio(path):
    try:
        with wave.open(str(path), 'w') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(44100)
            duration_seconds = 2
            silence = [0] * int(44100 * duration_seconds)
            wf.writeframes(b''.join(struct.pack('<h', s) for s in silence))
        logger.info(f"Dummy audio generated at {path}")
    except Exception as e:
        logger.error(f"Failed to generate dummy audio: {e}")

def call_elevenlabs_api(text, output_path):
    api_key = os.getenv("ELEVENLABS_API_KEY")
    voice_id = os.getenv("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")  # Default voice ID

    if not api_key:
        logger.error(f"{ErrorCode.ELEVENLABS_FAIL.value}: API key missing")
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
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "audio/mpeg")
            audio_data = response.content
            if "mpeg" in content_type or output_path.suffix.lower() != ".wav":
                seg = AudioSegment.from_file(BytesIO(audio_data))
                seg = seg.set_frame_rate(44100).set_channels(1)
                seg.export(output_path, format="wav")
            else:
                with open(output_path, "wb") as f:
                    f.write(audio_data)
            logger.info(f"Voiceover generated at {output_path}")
            return True
        else:
            logger.error(f"{ErrorCode.ELEVENLABS_FAIL.value}: {response.status_code} {response.text}")
            return False
    except Exception as e:
        logger.error(f"{ErrorCode.ELEVENLABS_FAIL.value}: {e}")
        return False

def generate_voiceover(script_text, output_path, *, test_mode: bool | None = None):
    if test_mode is None:
        test_mode = get_test_mode()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if test_mode:
        logger.info("Test mode active: using dummy audio and skipping ElevenLabs")
        generate_dummy_audio(output_path)
    else:
        logger.info("Calling ElevenLabs API...")
        success = call_elevenlabs_api(script_text, output_path)
        if not success:
            logger.error(f"{ErrorCode.ELEVENLABS_FAIL.value}: generation failed")
            raise RuntimeError(ErrorCode.ELEVENLABS_FAIL.value)
