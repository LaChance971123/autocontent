"""FastAPI server exposing pipeline generation jobs."""

from __future__ import annotations

import os
from pathlib import Path
from uuid import uuid4
from typing import Dict

from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import logging

from pipeline import run_pipeline

JOBS_DIR = Path(os.getenv("JOBS_DIR", "jobs"))
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "output"))
JOBS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)

app = FastAPI(title="AutoContent API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job registry
jobs: Dict[str, Dict] = {}


def _run_job(job_id: str, script_path: Path, background: Path, output_dir: Path) -> None:
    """Background task to execute the pipeline."""
    try:
        video = run_pipeline(script_path, background, output_dir, job_id=job_id)
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["result"] = str(video)
    except Exception as exc:
        logger.exception("Job %s failed", job_id)
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(exc)


@app.post("/jobs")
async def start_job(
    background: str = Form(...),
    script: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
):
    """Create a new pipeline job."""

    job_id = uuid4().hex
    work_dir = JOBS_DIR / job_id
    work_dir.mkdir(parents=True, exist_ok=True)
    script_path = work_dir / "script.txt"

    content = await script.read()
    script_path.write_bytes(content)

    jobs[job_id] = {"status": "running"}
    background_tasks.add_task(_run_job, job_id, script_path, Path(background), OUTPUT_DIR)
    return {"job_id": job_id}


@app.get("/jobs/{job_id}")
def job_status(job_id: str):
    """Return status information for *job_id*."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]


@app.get("/jobs/{job_id}/result")
def job_result(job_id: str):
    """Return the rendered video file for *job_id* if completed."""
    job = jobs.get(job_id)
    if not job or job.get("status") != "completed":
        raise HTTPException(status_code=404, detail="Result not available")
    return FileResponse(job["result"], filename=f"{job_id}.mp4")


