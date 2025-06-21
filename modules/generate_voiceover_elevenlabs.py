import os
from elevenlabs import generate, save

ELEVENLABS_API_KEY = "sk_f044ce7ce71d37d46709036a9592c7f5eda7843569f087bd"
VOICE_ID = "IRHApOXLvnW57QJPQH2P"

if not ELEVENLABS_API_KEY or not VOICE_ID:
    raise EnvironmentError("Missing ELEVENLABS_API_KEY or VOICE_ID in .env or environment variables.")

def generate_voiceover(script_path: str, output_path: str):
    with open(script_path, "r", encoding="utf-8") as f:
        script = f.read()

    audio = generate(
        text=script,
        voice=VOICE_ID,
        model="eleven_monolingual_v1",
        api_key=ELEVENLABS_API_KEY
    )

    save(audio, output_path)