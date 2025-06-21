from modules.render_video import render_final_video
from pathlib import Path

# Define paths
background_file = Path("assets/backgrounds/test_video.webm")
audio_file = Path("temp/voice.wav")
subtitle_file = Path("temp/subtitles.ass")
output_file = Path("output/final_render.mp4")

# Log what's being used
print(f"🎞️ Using background video: {background_file}")
print(f"🎧 Using audio file: {audio_file}")
print(f"📝 Using subtitle file: {subtitle_file}")
print(f"📤 Output path: {output_file}")

# Call the function with positional arguments only
render_final_video(background_file, audio_file, subtitle_file, output_file)
