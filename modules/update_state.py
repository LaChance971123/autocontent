import json
import argparse
from pathlib import Path

STATE_FILE = Path(__file__).resolve().parent.parent / "state.json"

def update_state(module, status):
    if not STATE_FILE.exists():
        print("[ERROR] state.json not found.")
        return

    with open(STATE_FILE, "r") as f:
        state = json.load(f)

    if module in state.get("modules", {}):
        state["modules"][module] = status
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
        print(f"[OK] Updated module '{module}' to status: '{status}'")
    else:
        print(f"[ERROR] Module '{module}' not found in state.json.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update module status in state.json")
    parser.add_argument("--module", type=str, required=True, help="Module name to update")
    parser.add_argument("--status", type=str, required=True, help="New status (e.g., completed, pending)")
    args = parser.parse_args()

    update_state(args.module, args.status)
