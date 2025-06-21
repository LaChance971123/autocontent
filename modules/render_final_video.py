
import os
import subprocess
import sys
import threading
import time

def render_final_video(audio_path, subtitle_path, output_path):
    # Normalize paths for ffmpeg (use forward slashes)
    subs = subtitle_path.replace('\\', '/')
    background = os.path.join('assets', 'backgrounds', 'test_video.webm').replace('\\', '/')
    watermark = os.path.join('assets', 'watermark.png').replace('\\', '/')

    # Burn in ASS subtitles (so karaoke tags work), then overlay watermark
    filter_complex = (
        f"[0:v]ass={subs}[subt];"
        "[2:v]scale=325:-1,format=rgba,colorchannelmixer=aa=0.15[wm];"
        "[subt][wm]overlay=5:5:format=auto[vout]"
    )

    cmd = [
        'ffmpeg',
        '-y',  # overwrite output
        '-i', background,       # input 0: background video
        '-i', audio_path,       # input 1: voiceover audio
        '-i', watermark,        # input 2: watermark image
        '-filter_complex', filter_complex,
        '-map', '[vout]',       # use the filtered video
        '-map', '1:a',          # use the voiceover audio
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-c:a', 'aac',
        '-shortest',
        output_path
    ]

    # Simple spinner for feedback
    done = False
    def spinner():
        for c in ['|', '/', '-', '\\']:
            while not done:
                sys.stdout.write(f"\rRendering final video... {c}")
                sys.stdout.flush()
                time.sleep(0.1)

    t = threading.Thread(target=spinner)
    t.start()
    try:
        subprocess.run(cmd, check=True)
    finally:
        done = True
        t.join()
        sys.stdout.write(f"\r[OK] Final video rendered successfully: {output_path}\n")


if __name__ == '__main__':
    render_final_video('temp/voice.wav', 'temp/subtitles.ass', 'output/final_render.mp4')
