from dataclasses import replace
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import pipeline, settings
from scripts.add_subtitles import add_subtitles


def test_normalize_formats_accepts_csv_and_rejects_unknown():
    assert pipeline._normalize_formats("youtube, vertical,youtube") == (
        "youtube",
        "vertical",
    )
    with pytest.raises(ValueError, match="formats"):
        pipeline._normalize_formats("tiktok")


def test_export_all_runs_only_requested_format(monkeypatch):
    from scripts import export_all as exports_module

    commands = []
    monkeypatch.setattr(
        exports_module.subprocess,
        "run",
        lambda command, **kwargs: commands.append(command) or SimpleNamespace(
            returncode=0, stderr="", stdout=""
        ),
    )

    exports_module.export_all(formats=("youtube",))

    assert len(commands) == 1
    assert commands[0][1].endswith("export_youtube.py")


def test_run_executes_stages_in_order_and_passes_selected_options(tmp_path, monkeypatch):
    from scripts.config_loader import load_config

    config = load_config()
    config = replace(config, paths=replace(config.paths, output_dir=str(tmp_path / "output")))
    monkeypatch.setattr(pipeline, "load_config", lambda: config)
    monkeypatch.setattr(
        pipeline,
        "load_preferences",
        lambda: {"palette": "dark-neon", "voice": "default-voice", "legend_style": "clean"},
    )
    calls = []
    scene = {
        "palette": "clean-light",
        "suggested_duration_hint": 5,
        "narration_text": "Narration",
        "elements": [
            {"type": "title", "content": "Teste", "duration_seconds": 5}
        ],
    }

    def parse(text, cfg, research_sources=None):
        calls.append(("parse", text))
        return scene.copy()

    monkeypatch.setattr(
        pipeline,
        "search_sources",
        lambda text: {
            "status": "completed",
            "query": text,
            "searched_at": "2026-01-01T00:00:00+00:00",
            "provider": "Bing",
            "sources": [],
        },
    )
    monkeypatch.setattr(pipeline, "parse_scene", parse)
    monkeypatch.setattr(
        pipeline,
        "generate_voice",
        lambda *args, **kwargs: calls.append(("voice", args[1])),
    )
    monkeypatch.setattr(
        pipeline,
        "compute_scene_duration",
        lambda path: calls.append(("duration", path)) or 9.5,
    )
    monkeypatch.setattr(
        pipeline,
        "build_composition",
        lambda *args: calls.append(("composition", args[0])),
    )
    monkeypatch.setattr(
        pipeline,
        "render_scene",
        lambda *args: calls.append(("render", args[1])),
    )
    monkeypatch.setattr(
        pipeline,
        "add_subtitles",
        lambda *args: calls.append(("subtitles", args[4], args[5])),
    )
    monkeypatch.setattr(
        pipeline,
        "export_all",
        lambda **kwargs: calls.append(("export", kwargs["formats"])),
    )
    outputs = pipeline.run(
        "product launch",
        palette="warm-sunset",
        voice="pt-BR-BrendaNeural",
        legend_style="bold",
        formats="vertical",
    )

    assert [call[0] for call in calls] == [
        "parse",
        "voice",
        "duration",
        "composition",
        "render",
        "subtitles",
        "export",
    ]
    written_scene = json.loads((tmp_path / "output" / "scene.json").read_text(encoding="utf-8"))
    assert written_scene["palette"] == "warm-sunset"
    assert calls[1] == ("voice", "pt-BR-BrendaNeural")
    assert calls[5][1:] == ("bold", str(tmp_path / "output" / "voice.mp3"))
    assert calls[6] == ("export", ("vertical",))
    assert set(outputs) == {"vertical"}
    assert (tmp_path / "output" / "scene.json").is_file()
    research = json.loads(
        (tmp_path / "output" / "research.json").read_text(encoding="utf-8")
    )
    assert research["status"] == "completed"


def test_pipeline_fails_fast_when_scene_parsing_fails(monkeypatch):
    from scripts.config_loader import load_config

    monkeypatch.setattr(pipeline, "load_config", load_config)
    monkeypatch.setattr(
        pipeline,
        "load_preferences",
        lambda: {"palette": "dark-neon", "voice": "voice", "legend_style": "karaoke"},
    )
    monkeypatch.setattr(
        pipeline,
        "search_sources",
        lambda text: {
            "status": "completed",
            "query": text,
            "searched_at": "2026-01-01T00:00:00+00:00",
            "provider": "Bing",
            "sources": [],
        },
    )
    monkeypatch.setattr(
        pipeline,
        "parse_scene",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("parse failed")),
    )
    monkeypatch.setattr(
        pipeline,
        "generate_voice",
        lambda *args, **kwargs: pytest.fail("TTS must not run after parse failure"),
    )

    with pytest.raises(RuntimeError, match="parse failed"):
        pipeline.run("valid description")


def test_preferences_round_trip_and_validate_palette(tmp_path):
    preference_file = tmp_path / "user_prefs.yaml"
    saved = settings.save_preferences({"palette": "warm-sunset"}, preference_file)
    assert saved["palette"] == "warm-sunset"
    assert settings.load_preferences(preference_file)["palette"] == "warm-sunset"
    with pytest.raises(ValueError, match="Estilo"):
        settings.save_preferences({"legend_style": "unknown"}, preference_file)


def test_add_subtitles_passes_selected_style_and_audio(monkeypatch):
    from scripts import add_subtitles as subtitle_module

    generated = []
    burned = []
    monkeypatch.setattr(
        subtitle_module,
        "generate_karaoke_ass",
        lambda *args, **kwargs: generated.append((args, kwargs)),
    )
    monkeypatch.setattr(
        subtitle_module,
        "burn_ass",
        lambda *args, **kwargs: burned.append((args, kwargs)) or Path("done.mp4"),
    )

    result = add_subtitles(legend_style="bold", audio_path="output/voice.mp3")
    assert result == Path("done.mp4")
    assert generated[0][1]["font_size"] == 72
    assert burned[0][1]["audio_path"] == "output/voice.mp3"
