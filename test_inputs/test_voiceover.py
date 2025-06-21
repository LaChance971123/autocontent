import sys
from pathlib import Path

# Add parent dir to sys.path to import voiceover
sys.path.append(str(Path(__file__).resolve().parent.parent / "modules"))

from modules.voiceover import generate_voiceover

# Dummy script text
script_text = """I found a tape recorder in my dead brother’s room.
The last recording wasn’t human. It whispered things I can’t forget.
"""

# Output path
output_path = Path(__file__).resolve().parent.parent / "temp" / "voice.wav"

# Run voiceover generation
generate_voiceover(script_text, output_path)

print(f"✅ Test complete. Check output at: {output_path}")
