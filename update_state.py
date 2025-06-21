import json
import os

def update_state(module, status):
    path = "state.json"
    state = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            state = json.load(f)
    state[module] = status
    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
