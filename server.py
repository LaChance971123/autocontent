from fastapi import FastAPI, UploadFile, File, Form, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from pathlib import Path
import shutil
import uuid
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict
import argparse
import os
import threading

import pipeline
from modules.utils import get_logger, OUTPUT_DIR

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    thread = threading.Thread(target=_cleanup_loop, daemon=True)
    thread.start()
    yield


app = FastAPI(lifespan=lifespan)

executor = ThreadPoolExecutor(max_workers=3)

JOBS: Dict[str, dict] = {}
RATE_LIMITS: Dict[str, list] = {}

logger = get_logger(__name__)

TEMP_UPLOAD = Path("temp/uploads")
TEMP_UPLOAD.mkdir(parents=True, exist_ok=True)

CLEANUP_INTERVAL = 600  # seconds
CLEANUP_AGE = 60 * 60  # seconds


def cleanup_output_dir(age_seconds: int = CLEANUP_AGE):
    base = Path(OUTPUT_DIR)
    if not base.exists():
        return
    cutoff = time.time() - age_seconds
    for folder in base.iterdir():
        if not folder.is_dir():
            continue
        if folder.name in JOBS and JOBS[folder.name]["status"] in ("queued", "running"):
            continue
        if folder.stat().st_mtime < cutoff:
            shutil.rmtree(folder, ignore_errors=True)
            logger.info(f"Removed old job folder: {folder}")


def _cleanup_loop():
    while True:
        cleanup_output_dir()
        time.sleep(CLEANUP_INTERVAL)




def run_job(job_id: str, script_path: Path, background_path: Path, params: dict):
    JOBS[job_id]["status"] = "processing"
    start_ts = time.time()
    JOBS[job_id]["started_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(start_ts))
    args = argparse.Namespace(
        script=str(script_path),
        background=str(background_path),
        output_dir=str(Path(OUTPUT_DIR) / job_id),
        dry_run=params.get("dry_run", False),
        test_mode=params.get("test_mode", False),
        verbose=params.get("verbose", False),
        keep_temp=params.get("keep_temp", False),
        thumbnail=params.get("thumbnail", False),
        model_size=params.get("model_size", "large-v3"),
        compress=False,
        cleanup_old=0,
        json=params.get("json", False),
        strict=params.get("strict", False),
        max_length=params.get("max_length", 0),
    )
    try:
        out_dir = pipeline.run_pipeline(args, job_id=job_id, started_at=JOBS[job_id]["started_at"])
        JOBS[job_id]["status"] = "complete"
        JOBS[job_id]["output_dir"] = str(out_dir)
        JOBS[job_id]["completed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        JOBS[job_id]["duration_seconds"] = int(time.time() - start_ts)
        (Path(out_dir) / "log.txt").write_text("Job log placeholder")
    except Exception as e:
        JOBS[job_id]["status"] = "failed"
        JOBS[job_id]["error"] = str(e)
        JOBS[job_id]["completed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


@app.post("/generate")
async def generate(
    request: Request,
    script_file: UploadFile = File(...),
    background_file: UploadFile = File(...),
    dry_run: bool = Form(False),
    test_mode: bool = Form(False),
    verbose: bool = Form(False),
    strict: bool = Form(False),
    json_flag: bool = Form(False),
    max_length: int = Form(0),
):
    ip = request.client.host
    rl = RATE_LIMITS.get(ip, [time.time(), 0])
    if time.time() - rl[0] > 60:
        rl = [time.time(), 0]
    if rl[1] >= 5:
        return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded. Try again later."})
    rl[1] += 1
    RATE_LIMITS[ip] = rl
    job_id = str(uuid.uuid4())
    script_path = TEMP_UPLOAD / f"{job_id}_script.txt"
    background_path = TEMP_UPLOAD / f"{job_id}_{background_file.filename}"
    TEMP_UPLOAD.mkdir(parents=True, exist_ok=True)
    with open(script_path, "wb") as f:
        f.write(await script_file.read())
    with open(background_path, "wb") as f:
        f.write(await background_file.read())
    JOBS[job_id] = {"status": "queued"}
    params = {
        "dry_run": dry_run,
        "test_mode": test_mode,
        "verbose": verbose,
        "strict": strict,
        "json": json_flag,
        "max_length": max_length,
    }
    loop = asyncio.get_event_loop()
    if not loop.is_closed():
        loop.run_in_executor(
            executor,
            run_job,
            job_id,
            script_path,
            background_path,
            params,
        )
    return {"job_id": job_id, "status": "queued"}


@app.get("/status/{job_id}")
async def status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        return JSONResponse(status_code=404, content={"error": "job not found"})
    payload = {
        "job_id": job_id,
        "status": job.get("status"),
        "started_at": job.get("started_at"),
        "completed_at": job.get("completed_at"),
        "duration_seconds": job.get("duration_seconds"),
        "video_url": f"/download/{job_id}",
        "log_url": f"/logs/{job_id}" if (Path(job.get("output_dir", "")) / "log.txt").exists() else None,
    }
    return payload


@app.get("/download/{job_id}")
async def download_video(job_id: str):
    file_path = OUTPUT_DIR / job_id / "final.mp4"
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Video not found")
    return FileResponse(path=str(file_path), media_type="video/mp4", filename=f"{job_id}.mp4")


@app.get("/logs/{job_id}")
async def get_logs(job_id: str):
    file_path = OUTPUT_DIR / job_id / "log.txt"
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Log not found")
    return FileResponse(path=str(file_path), media_type="text/plain", filename="log.txt")
