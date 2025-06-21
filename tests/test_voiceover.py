import os
from pathlib import Path
from modules.voiceover import generate_voiceover


def test_generate_voiceover(tmp_path):
    os.environ["TEST_MODE"] = "true"
    output = tmp_path / "voice.wav"
    generate_voiceover("Hello world", output, test_mode=True)
    assert output.exists()
