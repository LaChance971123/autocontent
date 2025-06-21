# AutoContent

This project provides a simple pipeline for generating voiceovers, subtitles and merging them with a background video.

## Setup

1. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and set your ElevenLabs credentials.
   - `ELEVENLABS_API_KEY` – API token for generating voiceovers
   - `ELEVENLABS_VOICE_ID` – desired voice ID from ElevenLabs
   - `TEST_MODE` – set to `true` to skip API calls and generate silent audio
   - `JOBS_DIR` – directory for temporary per-job files
   - `OUTPUT_DIR` – directory for rendered results

3. Run the pipeline:
```bash
python pipeline.py scripts/test_script.txt assets/backgrounds/test_video.webm output
```

### Running the API server

Launch the FastAPI server to process jobs in the background:
```bash
uvicorn server:app --reload
```
Submit a job by POSTing a script file and background path to `/jobs` then poll
`/jobs/{job_id}` for status. When completed, download from
`/jobs/{job_id}/result`.

## Testing

Run the test suite with:
```bash
pytest
```

## Docker

A simple Dockerfile is provided:
```bash
docker build -t autocontent .
docker run --env-file .env autocontent
```
