import time
import os
from pathlib import Path
from fastapi.testclient import TestClient

import server

SCRIPT = Path('scripts/test_script.txt')
BACKGROUND = Path('assets/backgrounds/test_video.webm')

client = TestClient(server.app)

def setup_function(func):
    server.RATE_LIMITS.clear()

def submit_job():
    with SCRIPT.open('rb') as sf, BACKGROUND.open('rb') as bf:
        resp = client.post(
            '/generate',
            files={
                'script_file': ('script.txt', sf.read(), 'text/plain'),
                'background_file': ('bg.webm', bf.read(), 'video/webm')
            },
            data={'test_mode': '1', 'dry_run': '0'}
        )
        assert resp.status_code == 200
        return resp.json()['job_id']

def wait_for_completion(job_id):
    for _ in range(40):
        r = client.get(f'/status/{job_id}')
        assert r.status_code == 200
        data = r.json()
        if data['status'] in ('complete', 'failed'):
            return data
        time.sleep(0.1)
    return data

def test_generate_download_and_status(tmp_path):
    job_id = submit_job()
    status = wait_for_completion(job_id)
    assert status['status'] == 'complete'
    assert status['video_url']
    # download endpoint
    r = client.get(status['video_url'])
    assert r.status_code == 200
    assert r.headers['content-type'] == 'video/mp4'
    # log endpoint
    log_resp = client.get(f'/logs/{job_id}')
    assert log_resp.status_code == 200


def test_rate_limiting(tmp_path):
    for _ in range(3):
        submit_job()
    extra = client.post(
        '/generate',
        files={'script_file': ('a.txt', b'x', 'text/plain'),
               'background_file': ('b.webm', b'x', 'video/webm')},
        data={'test_mode': '1', 'dry_run': '0'}
    )
    assert extra.status_code == 429


def test_cleanup_function(tmp_path):
    old_folder = Path('output/oldjob')
    old_folder.mkdir(parents=True, exist_ok=True)
    (old_folder / 'dummy').write_text('x')
    # set mtime to past
    past = time.time() - (server.CLEANUP_AGE + 10)
    os.utime(old_folder, (past, past))
    server.cleanup_output_dir(age_seconds=0)
    assert not old_folder.exists()
