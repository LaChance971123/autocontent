import argparse
import os
import json
from pathlib import Path
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Constants
PROJECT_ROOT = Path(__file__).parent
STATE_FILE = PROJECT_ROOT / "state.json"
REQUIRED_FOLDERS = [
    "modules",
    "assets/backgrounds/clipgoat",
    "assets/backgrounds/minecraft",
    "assets/backgrounds/gta",
    "assets/backgrounds/climber",
    "test_inputs",
    "output",
    "logs",
    "temp"
]

# Setup logging
log_path = PROJECT_ROOT / "logs" / "runtime.log"
logging.basicConfig(filename=log_path, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def create_folders():
    for folder in REQUIRED_FOLDERS:
        path = PROJECT_ROOT / folder
        path.mkdir(parents=True, exist_ok=True)
        logging.info(f"Verified folder: {folder}")

def load_state():
    if not STATE_FILE.exists():
        print("[ERROR] state.json not found.")
        return None
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def validate_env():
    eleven_key = os.getenv("ELEVENLABS_API_KEY")
    if not eleven_key:
        print("[ERROR] ELEVENLABS_API_KEY not found in .env")
        return False
    print("[OK] ElevenLabs key found (but not validated to save tokens).")
    return True

def run_cli():
    parser = argparse.ArgumentParser(description="AutoContent CLI")
    parser.add_argument("--init", action="store_true", help="Create necessary folders and check environment.")
    parser.add_argument("--dry-run", action="store_true", help="Run in test mode (no real API calls).")
    parser.add_argument("--debug", action="store_true", help="Enable debug output.")
    parser.add_argument("--validate-env", action="store_true", help="Check for .env and keys.")
    args = parser.parse_args()

    if args.debug:
        print("[DEBUG] Running in DEBUG mode")
        logging.getLogger().setLevel(logging.DEBUG)

    if args.init:
        print("[INFO] Initializing project...")
        create_folders()
        print("[OK] Folders ready.")

    if args.validate_env:
        validate_env()

    if args.dry_run:
        print("[INFO] Running in dry-run mode. No API calls will be made.")
        logging.info("Dry-run mode enabled.")

    logging.info("CLI execution completed.")

if __name__ == "__main__":
    run_cli()
