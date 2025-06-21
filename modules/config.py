import os
from dotenv import load_dotenv

"""Configuration helpers for environment variables."""

# Resolve .env path relative to project root
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=env_path)

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")

if not ELEVENLABS_API_KEY or not VOICE_ID:
    raise EnvironmentError("Missing ELEVENLABS_API_KEY or VOICE_ID in .env or environment variables.")
