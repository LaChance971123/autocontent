import os
from pathlib import Path
from pipeline import run_pipeline


def test_run_pipeline(tmp_path):
    os.environ["TEST_MODE"] = "true"
    script = Path("scripts/test_script.txt")
    background = Path("assets/backgrounds/test_video.webm")
    result = run_pipeline(script, background, tmp_path, test_mode=True)
    assert result.exists()
