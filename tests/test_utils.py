from modules.utils import save_ass_subtitles
from pathlib import Path


def test_save_ass_subtitles(tmp_path):
    segments = [
        {"start": 0.0, "end": 1.0, "word": "hello"},
        {"start": 1.0, "end": 2.0, "word": "world"},
    ]
    output = tmp_path / "subs.ass"
    save_ass_subtitles(segments, output)
    assert output.exists()
