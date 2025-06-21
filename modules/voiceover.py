import os
from pathlib import Path
import logging
import json
import requests
from dotenv import load_dotenv
import wave
import struct

load_dotenv()

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEMP_DIR = PROJECT_ROOT / "temp"
STATE_FILE = PROJECT_ROOT / "state.json"

# Ensure temp exists
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# Logging
logging.basicConfig(filename=PROJECT_ROOT / "logs/runtime.log", level=logging.INFO)

def get_test_mode():
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f).get("env", {}).get("test_mode", True)
    except Exception as e:
        logging.error(f"Could not read state.json: {e}")
        return True

def generate_dummy_audio(path):
    try:
        with wave.open(str(path), 'w') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(44100)
            duration_seconds = 2
            silence = [0] * int(44100 * duration_seconds)
            wf.writeframes(b''.join(struct.pack('<h', s) for s in silence))
        logging.info(f"Dummy audio generated at {path}")
    except Exception as e:
        logging.error(f"Failed to generate dummy audio: {e}")

def call_elevenlabs_api(text, output_path):
    api_key = os.getenv("ELEVENLABS_API_KEY")
    voice_id = os.getenv("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")  # Default voice ID

    if not api_key:
        logging.error("ELEVENLABS_API_KEY not found in .env")
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
            with open(output_path, "wb") as f:
                f.write(response.content)
            logging.info(f"Voiceover generated at {output_path}")
            return True
        else:
            logging.error(f"ElevenLabs API Error {response.status_code}: {response.text}")
            return False
    except Exception as e:
        logging.error(f"Exception during ElevenLabs call: {e}")
        return False

def generate_voiceover(script_text, output_path):
    test_mode = get_test_mode()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if test_mode:
        print("[INFO] Test mode active: generating dummy audio")
        generate_dummy_audio(output_path)
    else:
        print("[INFO] Calling ElevenLabs API...")
        success = call_elevenlabs_api(script_text, output_path)
        if not success:
            print("[ERROR] Failed to generate voiceover.")
