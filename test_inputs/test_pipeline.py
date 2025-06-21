import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from modules.generate_voiceover_elevenlabs import generate_voiceover
from modules.generate_subtitles import generate_subtitles
from modules.generate_card import generate_card
from modules.render_final_video import render_final_video as generate_final_video

def main():
    script_path = "scripts/test_script.txt"
    audio_path = "temp/voice.wav"
    subtitle_path = "temp/subtitles.ass"
    card_path = "temp/reddit_card.png"
    output_path = "output/final_render.mp4"

    generate_voiceover(script_path, audio_path)
    generate_subtitles(audio_path, subtitle_path)
    generate_card("testsub", "This is a test title", card_path)
    generate_final_video(audio_path, subtitle_path, output_path)

if __name__ == "__main__":
    main()
