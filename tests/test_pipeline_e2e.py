"""Opt-in end-to-end test for the local Ollama-to-MP4 pipeline."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest
import requests

from scripts import pipeline, render_scene
from scripts.config_loader import load_config
from scripts.export_all import export_all as run_export_all
from scripts.settings import default_preferences


pytestmark = pytest.mark.slow


def _missing_prerequisites() -> list[str]:
    missing = [
        tool
        for tool in ("ollama", "ffmpeg", "ffprobe", "node", "npx", "subreel")
        if shutil.which(tool) is None
    ]
    if missing:
        return missing

    config = load_config()
    try:
        response = requests.get(f"{config.llm.base_url.rstrip('/')}/api/tags", timeout=3)
        response.raise_for_status()
        models = response.json().get("models", [])
    except (requests.RequestException, ValueError) as exc:
        return [f"Ollama indisponível em {config.llm.base_url}: {exc}"]

    model_name = config.llm.model.split(":")[0]
    if not any(model.get("name", "").split(":")[0] == model_name for model in models):
        return [f"modelo Ollama '{config.llm.model}' não baixado (ollama pull {config.llm.model})"]
    return []


def _copy_render_project(source: Path, destination: Path) -> None:
    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns(".hyperframes", ".thumbnails", "test.mp4"),
    )


def _probe_export(path: Path) -> dict:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries",
            "stream=codec_type,codec_name,width,height,pix_fmt",
            "-of", "json", str(path),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, f"ffprobe falhou para {path}: {result.stderr}"
    return json.loads(result.stdout)


def test_e2e_prerequisite_check_reports_missing_ffmpeg(monkeypatch):
    monkeypatch.setattr(
        shutil,
        "which",
        lambda command: None if command == "ffmpeg" else command,
    )
    missing = _missing_prerequisites()
    assert "ffmpeg" in missing


def test_pipeline_creates_youtube_and_vertical_exports(tmp_path, monkeypatch):
    missing = _missing_prerequisites()
    if missing:
        pytest.skip("Pré-requisitos do teste E2E ausentes: " + "; ".join(missing))

    render_dir = tmp_path / "render"
    _copy_render_project(Path(render_scene.RENDER_DIR), render_dir)
    monkeypatch.setattr(render_scene, "RENDER_DIR", render_dir)
    monkeypatch.setattr(
        pipeline,
        "_resolve_path",
        lambda value: Path(value).resolve()
        if Path(value).is_absolute()
        else (tmp_path / value).resolve(),
    )
    monkeypatch.setattr(
        pipeline,
        "_resolve_path",
        lambda value: Path(value).resolve()
        if Path(value).is_absolute()
        else (tmp_path / value).resolve(),
    )
    monkeypatch.setattr(pipeline, "load_preferences", default_preferences)

    def export_to_temp(input_path, audio_path, formats):
        run_export_all(
            input_path=input_path,
            audio_path=audio_path,
            youtube_output=str(tmp_path / "output-youtube.mp4"),
            vertical_output=str(tmp_path / "output-vertical.mp4"),
            formats=formats,
        )

    monkeypatch.setattr(pipeline, "export_all", export_to_temp)
    outputs = pipeline.run(
        "Sono e sua importância para o aprendizado.",
        palette="dark-neon",
        formats=("youtube", "vertical"),
    )

    youtube_path = outputs["youtube"]
    vertical_path = outputs["vertical"]
    assert youtube_path.is_file() and youtube_path.stat().st_size > 0
    assert vertical_path.is_file() and vertical_path.stat().st_size > 0

    youtube_video = next(
        stream for stream in _probe_export(youtube_path)["streams"]
        if stream["codec_type"] == "video"
    )
    vertical_video = next(
        stream for stream in _probe_export(vertical_path)["streams"]
        if stream["codec_type"] == "video"
    )
    assert (youtube_video["codec_name"], youtube_video["width"], youtube_video["height"]) == (
        "h264", 1920, 1080
    )
    assert (vertical_video["codec_name"], vertical_video["width"], vertical_video["height"]) == (
        "h264", 1080, 1920
    )
    assert youtube_video["pix_fmt"] == vertical_video["pix_fmt"] == "yuv420p"
    assert any(stream["codec_name"] == "aac" for stream in _probe_export(youtube_path)["streams"])
    assert any(stream["codec_name"] == "aac" for stream in _probe_export(vertical_path)["streams"])
