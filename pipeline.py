import argparse
import json
import os
import shutil
import subprocess
import time
import logging
import wave
from pathlib import Path

from modules.voiceover import generate_voiceover
from modules.generate_subtitles import generate_subtitles
from modules.render_video import render_final_video
from modules.utils import (
    get_logger,
    sanitize_name,
    extract_title_and_stats,
    init_job_log,
    save_job_log,
    ErrorCode,
    is_api_mode,
)

logger = get_logger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(description="Run the AutoContent pipeline")
    parser.add_argument("--script", required=True, help="Path to script text file")
    parser.add_argument("--background", required=True, help="Background video file")
    parser.add_argument("--output-dir", help="Directory for final outputs")
    parser.add_argument("--dry-run", action="store_true", help="Run pipeline without rendering final video")
    parser.add_argument("--test-mode", action="store_true", help="Use dummy audio and subtitles")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    parser.add_argument("--keep-temp", action="store_true", help="Retain temp folder after execution")
    parser.add_argument("--thumbnail", action="store_true", help="Export a thumbnail from the final video")
    parser.add_argument("--model-size", default="large-v3", help="WhisperX model size")
    parser.add_argument("--compress", action="store_true", help="Compress final video")
    parser.add_argument("--cleanup-old", type=int, default=0, help="Delete N oldest output folders before running")
    parser.add_argument("--json", action="store_true", help="Print JSON summary to stdout")
    parser.add_argument("--strict", action="store_true", help="Stop pipeline on first error")
    parser.add_argument("--max-length", type=int, default=0, help="Trim script if duration exceeds this many seconds")
    return parser.parse_args()


def validate_paths(script_path: Path, background_path: Path):
    if not script_path.is_file():
        raise FileNotFoundError(ErrorCode.SCRIPT_NOT_FOUND.value)
    if not background_path.is_file():
        raise FileNotFoundError(ErrorCode.BACKGROUND_NOT_FOUND.value)


def export_thumbnail(video: Path, thumb: Path, title: str):
    try:
        subprocess.run([
            "ffmpeg", "-y", "-i", str(video), "-ss", "00:00:01",
            "-vframes", "1",
            "-vf", f"drawtext=text='{title}':fontcolor=white:fontsize=32:box=1:boxcolor=black@0.5:boxborderw=5:x=(w-text_w)/2:y=(h-text_h)/2",
            str(thumb)
        ], check=True)
        logger.info(f"Thumbnail exported to {thumb}")
    except subprocess.CalledProcessError as e:
        logger.error(f"{ErrorCode.THUMBNAIL_FAIL.value}: {e}")
        raise RuntimeError(ErrorCode.THUMBNAIL_FAIL.value) from e


def compress_video(src: Path, dest: Path):
    try:
        subprocess.run([
            "ffmpeg",
            "-y",
            "-i",
            str(src),
            "-b:v",
            "1M",
            "-bufsize",
            "1M",
            str(dest),
        ], check=True)
        logger.info(f"Compressed video saved to {dest}")
    except subprocess.CalledProcessError as e:
        logger.error(f"{ErrorCode.COMPRESS_FAIL.value}: {e}")
        raise RuntimeError(ErrorCode.COMPRESS_FAIL.value) from e


def cleanup_old_jobs(count: int, base: Path = Path("output")):
    if count <= 0 or not base.exists():
        return
    dirs = [d for d in base.iterdir() if d.is_dir()]
    dirs.sort(key=lambda p: p.stat().st_mtime)
    for d in dirs[:count]:
        shutil.rmtree(d, ignore_errors=True)
        logger.info(f"Removed old output folder: {d}")


def fmt_time(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


def run_pipeline(args, job_id: str | None = None, started_at: str | None = None):
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    elif is_api_mode(args):
        logger.setLevel(logging.WARNING)

    script_path = Path(args.script)
    background_path = Path(args.background)
    validate_paths(script_path, background_path)

    if args.cleanup_old:
        cleanup_old_jobs(args.cleanup_old)

    with open(script_path, "r", encoding="utf-8") as f:
        script_text = f.read()

    if args.max_length:
        max_words = args.max_length * 3
        words = script_text.split()
        if len(words) > max_words:
            script_text = " ".join(words[:max_words])
            logger.info(f"Script trimmed to {args.max_length}s / {max_words} words")

    title, stats = extract_title_and_stats(script_text)

    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = Path("output") / sanitize_name(title)

    output_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = Path("temp")
    temp_dir.mkdir(parents=True, exist_ok=True)

    job_log = init_job_log(output_dir.name, args.test_mode)

    voice_path = temp_dir / "voice.wav"
    subs_path = temp_dir / "subtitles.ass"
    video_path = output_dir / "final.mp4"

    start = time.time()

    try:
        generate_voiceover(script_text, voice_path, test_mode=args.test_mode)
        job_log["output_files"]["audio"] = str(voice_path)
    except Exception as e:
        job_log["errors"].append(e.args[0] if e.args else str(e))
        if args.strict:
            raise

    with wave.open(str(voice_path)) as wf:
        audio_duration = wf.getnframes() / wf.getframerate()

    try:
        generate_subtitles(voice_path, subs_path, model_size=args.model_size, test_mode=args.test_mode)
        job_log["output_files"]["subtitles"] = str(subs_path)
    except Exception as e:
        job_log["errors"].append(e.args[0] if e.args else str(e))
        if args.strict:
            raise

    if not args.dry_run:
        try:
            render_final_video(background_path, voice_path, subs_path, video_path)
            job_log["output_files"]["video"] = str(video_path)
        except Exception as e:
            job_log["errors"].append(e.args[0] if e.args else str(e))
            if args.strict:
                raise
        if args.thumbnail and not job_log["errors"]:
            try:
                thumb = output_dir / "thumbnail.png"
                export_thumbnail(video_path, thumb, title)
                job_log["output_files"]["thumbnail"] = str(thumb)
            except Exception as e:
                job_log["errors"].append(e.args[0] if e.args else str(e))
                if args.strict:
                    raise
        if args.compress and not job_log["errors"]:
            try:
                compressed = output_dir / "final_compressed.mp4"
                compress_video(video_path, compressed)
                job_log["output_files"]["compressed"] = str(compressed)
            except Exception as e:
                job_log["errors"].append(e.args[0] if e.args else str(e))
                if args.strict:
                    raise
    else:
        logger.info("Dry run enabled - skipping video rendering")

    end_time = time.time()
    duration = end_time - start

    metadata = {
        "job_id": job_id or output_dir.name,
        "title": title,
        **stats,
        "script": script_path.name,
        "started_at": started_at or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(start)),
        "completed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(end_time)),
        "duration_seconds": int(duration),
        "model_size": args.model_size,
        "voice_id": os.getenv("ELEVENLABS_VOICE_ID", "default"),
        "audio_duration": round(audio_duration, 2),
        "total_runtime": round(duration, 2),
        "flags": {
            "dry_run": args.dry_run,
            "test_mode": args.test_mode,
            "thumbnail": args.thumbnail,
            "keep_temp": args.keep_temp,
            "model_size": args.model_size,
            "compress": args.compress,
        },
    }

    with open(output_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    job_log["duration_sec"] = round(duration, 2)
    save_job_log(job_log, output_dir)

    if not args.keep_temp:
        shutil.rmtree(temp_dir, ignore_errors=True)
    else:
        logger.info(f"Temp files retained at {temp_dir}")

    summary_text = (
        f"\n✅ Job complete\n"
        f"📝 Title: \"{title}\"\n"
        f"🕓 Voice Length: {fmt_time(audio_duration)}\n"
        f"⏱ Total Runtime: {duration:.1f}s\n"
        f"📁 Output: {output_dir}/"
    )
    logger.info(summary_text)

    if args.json:
        summary = {
            "job_id": output_dir.name,
            "title": title,
            "duration": round(audio_duration, 2),
            "output_path": str(output_dir),
            "errors": job_log["errors"],
        }
        print(json.dumps(summary))

    return output_dir


def main():
    args = parse_args()
    run_pipeline(args)


if __name__ == "__main__":
    main()
