import json
import os
import shutil
import logging
from pathlib import Path
from argparse import Namespace
import pytest

import pipeline

SCRIPT = Path('scripts/test_script.txt')
BACKGROUND = Path('assets/backgrounds/test_video.webm')


def test_missing_file_errors(tmp_path):
    args = Namespace(script='missing.txt', background=str(BACKGROUND), output_dir=str(tmp_path), dry_run=True, test_mode=True, verbose=False, keep_temp=False, thumbnail=False, model_size='tiny', compress=False, cleanup_old=0, json=False, strict=False, max_length=0)
    try:
        pipeline.run_pipeline(args)
    except FileNotFoundError:
        pass
    else:
        assert False, 'Expected FileNotFoundError'


def test_verbose_log_level(monkeypatch, tmp_path):
    args = Namespace(script=str(SCRIPT), background=str(BACKGROUND), output_dir=str(tmp_path), dry_run=True, test_mode=True, verbose=True, keep_temp=False, thumbnail=False, model_size='tiny', compress=False, cleanup_old=0, json=False, strict=False, max_length=0)
    pipeline.run_pipeline(args)
    assert pipeline.logger.level == logging.DEBUG


def test_keep_temp_retains_files(tmp_path):
    temp_dir = Path('temp')
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    args = Namespace(script=str(SCRIPT), background=str(BACKGROUND), output_dir=str(tmp_path), dry_run=True, test_mode=True, verbose=False, keep_temp=True, thumbnail=False, model_size='tiny', compress=False, cleanup_old=0, json=False, strict=False, max_length=0)
    pipeline.run_pipeline(args)
    assert (temp_dir / 'voice.wav').exists()
    shutil.rmtree(temp_dir)


def test_model_override(tmp_path):
    args = Namespace(script=str(SCRIPT), background=str(BACKGROUND), output_dir=str(tmp_path), dry_run=True, test_mode=True, verbose=False, keep_temp=False, thumbnail=False, model_size='small', compress=False, cleanup_old=0, json=False, strict=False, max_length=0)
    pipeline.run_pipeline(args)
    meta = json.loads((Path(tmp_path) / 'metadata.json').read_text())
    assert meta['model_size'] == 'small'


def test_metadata_file(tmp_path):
    args = Namespace(script=str(SCRIPT), background=str(BACKGROUND), output_dir=str(tmp_path), dry_run=True, test_mode=True, verbose=False, keep_temp=False, thumbnail=False, model_size='tiny', compress=False, cleanup_old=0, json=False, strict=False, max_length=0)
    pipeline.run_pipeline(args)
    meta_path = Path(tmp_path) / 'metadata.json'
    assert meta_path.exists()
    data = json.loads(meta_path.read_text())
    assert 'title' in data and 'word_count' in data


def test_sanitized_folder_name(tmp_path):
    custom_script = tmp_path / 'Weird Title!!.txt'
    custom_script.write_text('Hello world')
    args = Namespace(script=str(custom_script), background=str(BACKGROUND), output_dir=None, dry_run=True, test_mode=True, verbose=False, keep_temp=False, thumbnail=False, model_size='tiny', compress=False, cleanup_old=0, json=False, strict=False, max_length=0)
    pipeline.run_pipeline(args)
    expected_dir = Path('output') / 'hello_world'
    assert expected_dir.exists()
    shutil.rmtree(expected_dir)


def test_log_file_created(tmp_path):
    args = Namespace(script=str(SCRIPT), background=str(BACKGROUND), output_dir=str(tmp_path), dry_run=True, test_mode=True, verbose=False, keep_temp=False, thumbnail=False, model_size='tiny', compress=False, cleanup_old=0, json=False, strict=False, max_length=0)
    pipeline.run_pipeline(args)
    assert (Path(tmp_path) / 'log.json').exists()


def test_compress_reduces_size(tmp_path):
    if shutil.which('ffmpeg') is None:
        pytest.skip('ffmpeg not available')
    args = Namespace(script=str(SCRIPT), background=str(BACKGROUND), output_dir=str(tmp_path), dry_run=False, test_mode=True, verbose=False, keep_temp=False, thumbnail=False, model_size='tiny', compress=True, cleanup_old=0, json=False, strict=False, max_length=0)
    pipeline.run_pipeline(args)
    orig = Path(tmp_path) / 'final.mp4'
    comp = Path(tmp_path) / 'final_compressed.mp4'
    assert comp.exists()
    assert comp.stat().st_size < orig.stat().st_size


def test_cleanup_old(tmp_path):
    base = Path('output')
    old1 = base / 'old1'
    old2 = base / 'old2'
    old1.mkdir(parents=True, exist_ok=True)
    old2.mkdir(parents=True, exist_ok=True)
    (old1 / 'dummy.txt').write_text('x')
    (old2 / 'dummy.txt').write_text('x')
    os.utime(old1, (1, 1))
    os.utime(old2, (2, 2))
    args = Namespace(script=str(SCRIPT), background=str(BACKGROUND), output_dir=str(tmp_path), dry_run=True, test_mode=True, verbose=False, keep_temp=False, thumbnail=False, model_size='tiny', compress=False, cleanup_old=1, json=False, strict=False, max_length=0)
    pipeline.run_pipeline(args)
    # old1 should be removed as the oldest
    assert not old1.exists() and old2.exists()
    shutil.rmtree(old2)


def test_json_output(tmp_path, capsys):
    args = Namespace(script=str(SCRIPT), background=str(BACKGROUND), output_dir=str(tmp_path), dry_run=True, test_mode=True, verbose=False, keep_temp=False, thumbnail=False, model_size='tiny', compress=False, cleanup_old=0, json=True, strict=False, max_length=0)
    pipeline.run_pipeline(args)
    captured = capsys.readouterr().out
    data = json.loads(captured.strip())
    assert data['output_path'] == str(tmp_path)


def test_strict_halts(tmp_path, monkeypatch):
    def fail_render(*a, **k):
        raise RuntimeError('FAIL')

    monkeypatch.setattr(pipeline, 'render_final_video', fail_render)
    args = Namespace(script=str(SCRIPT), background=str(BACKGROUND), output_dir=str(tmp_path), dry_run=False, test_mode=True, verbose=False, keep_temp=False, thumbnail=False, model_size='tiny', compress=False, cleanup_old=0, json=False, strict=True, max_length=0)
    with pytest.raises(RuntimeError):
        pipeline.run_pipeline(args)
