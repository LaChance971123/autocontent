
import subprocess
from pathlib import Path

def render_final_video(background_video, audio_file, subtitle_file, output_path):
    print(f"[INFO] Using background video: {background_video}")
    print(f"[INFO] Using audio file: {audio_file}")
    print(f"[INFO] Using subtitle file: {subtitle_file}")
    print(f"[INFO] Output path: {output_path}")

    background_video = Path(background_video).resolve()
    audio_file = Path(audio_file).resolve()
    subtitle_file = Path(subtitle_file).resolve()
    output_path = Path(output_path).resolve()

    if not background_video.exists():
        print(f"[ERROR] Background video not found: {background_video}")
        return
    if not audio_file.exists():
        print(f"[ERROR] Audio file not found: {audio_file}")
        return
    if not subtitle_file.exists():
        print(f"[ERROR] Subtitle file not found: {subtitle_file}")
        return

    subtitle_path_escaped = str(subtitle_file).replace('\\', '/').replace(':', '\\:')

    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-i", str(background_video),
        "-i", str(audio_file),
        "-filter_complex",
        f"[0:v]scale=1080:1920,setsar=1,subtitles='{subtitle_path_escaped}'[v]",
        "-map", "[v]",
        "-map", "1:a",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-shortest",
        str(output_path)
    ]

    try:
        subprocess.run(ffmpeg_cmd, check=True)
        print(f"[OK] Final video rendered: {output_path}")
    except subprocess.CalledProcessError as e:
        print("[ERROR] FFmpeg rendering failed.")
        print(e)

