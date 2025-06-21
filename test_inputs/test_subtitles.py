import sys
from pathlib import Path

# Add modules to sys path
sys.path.append(str(Path(__file__).resolve().parent.parent / "modules"))

from modules.generate_subtitles import generate_subtitles

# Define input/output
audio_path = Path(__file__).resolve().parent.parent / "temp" / "voice.wav"
subtitle_path = Path(__file__).resolve().parent.parent / "temp" / "subtitles.ass"

# Run subtitle generator
generate_subtitles(audio_path, subtitle_path)

print(f"✅ Subtitle test complete. Output saved to: {subtitle_path}")
