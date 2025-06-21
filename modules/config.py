import os
from dotenv import load_dotenv

# Resolve .env path relative to this file
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=env_path)

ELEVENLABS_API_KEY = "sk_f044ce7ce71d37d46709036a9592c7f5eda7843569f087bd"
VOICE_ID = "IRHApOXLvnW57QJPQH2P"

if not ELEVENLABS_API_KEY or not VOICE_ID:
    raise EnvironmentError("Missing ELEVENLABS_API_KEY or VOICE_ID in .env or environment variables.")
