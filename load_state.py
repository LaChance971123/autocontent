import json
import os

def load_state():
    path = "state.json"
    if not os.path.exists(path):
        print("❌ state.json not found.")
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
