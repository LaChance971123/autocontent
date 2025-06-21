# AutoContent CLI

Run the automated video generation pipeline.

## Usage

```bash
python pipeline.py --script PATH --background PATH [options]
```

### Options
- `--output-dir DIR` – custom output folder
- `--dry-run` – skip final video rendering
- `--test-mode` – use dummy audio and subtitles
- `--verbose` – debug logging
- `--keep-temp` – keep temporary files
- `--thumbnail` – export thumbnail image with title overlay
- `--compress` – compress final video to ~1 Mbps
- `--model-size SIZE` – WhisperX model size (e.g., `large-v2`)
- `--cleanup-old N` – remove the oldest N folders in `output/`
- `--json` – print a JSON summary
- `--strict` – stop on first failure
- `--max-length SECS` – trim scripts longer than this length (approx. 3 words/sec)

Environment variable `API_MODE=1` suppresses info logs when not running with `--verbose`.

### Example

```bash
python pipeline.py --script scripts/example.txt --background assets/bg.mp4 --thumbnail --compress --json
```

## FastAPI Server

Run the API server to queue jobs via HTTP:

```bash
uvicorn server:app --reload
```

POST `/generate` with form fields `script_file` and `background_file` plus optional parameters `test_mode`, `verbose`, `strict`, `json`, `max_length`. The response contains a `job_id`.

GET `/status/{job_id}` returns the current job status and the output folder when complete.
