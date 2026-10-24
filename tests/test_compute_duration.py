"""Unit tests for scene duration calculation."""

import json
import sys

import pytest

from scripts import compute_duration
from scripts.compute_duration import compute_scene_duration


@pytest.mark.parametrize(
    "payload",
    [
        [{"end": 1.1}, {"end": 2.7}, {"end": 1.8}],
        {"words": [{"end": 1.1}, {"end": 2.7}, {"end": 1.8}]},
    ],
)
def test_calculates_max_end_plus_padding(tmp_path, payload):
    words_path = tmp_path / "words.json"
    words_path.write_text(json.dumps(payload), encoding="utf-8")
    assert compute_scene_duration(words_path, padding=0.25) == pytest.approx(2.95)


def test_uses_default_padding(tmp_path):
    words_path = tmp_path / "words.json"
    words_path.write_text(json.dumps([{"end": 3}]), encoding="utf-8")
    assert compute_scene_duration(words_path) == pytest.approx(3.3)


def test_reports_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="não encontrado"):
        compute_scene_duration(tmp_path / "missing.json")


def test_rejects_unrecognized_json_structure(tmp_path):
    words_path = tmp_path / "words.json"
    words_path.write_text(json.dumps({"items": []}), encoding="utf-8")
    with pytest.raises(ValueError, match="Estrutura não reconhecida"):
        compute_scene_duration(words_path)


def test_rejects_empty_words(tmp_path):
    words_path = tmp_path / "words.json"
    words_path.write_text(json.dumps({"words": []}), encoding="utf-8")
    with pytest.raises(ValueError, match="está vazio"):
        compute_scene_duration(words_path)


@pytest.mark.parametrize(
    ("words", "message"),
    [
        ([None], r"words\[0\] sem campo 'end'"),
        ([{"start": 0}], r"words\[0\] sem campo 'end'"),
        ([{"end": "2"}], r"words\[0\]\.end não numérico"),
    ],
)
def test_rejects_invalid_word_end_values(tmp_path, words, message):
    words_path = tmp_path / "words.json"
    words_path.write_text(json.dumps(words), encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        compute_scene_duration(words_path)


def test_cli_prints_duration_and_reports_errors(tmp_path, monkeypatch, capsys):
    words_path = tmp_path / "words.json"
    words_path.write_text(json.dumps([{"end": 2}]), encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        ["compute_duration.py", str(words_path), "--padding", "0.5"],
    )
    assert compute_duration.main() == 0
    assert capsys.readouterr().out.strip() == "2.500"

    monkeypatch.setattr(sys, "argv", ["compute_duration.py", str(tmp_path / "missing.json")])
    assert compute_duration.main() == 1
    assert "Erro:" in capsys.readouterr().out


def test_cli_rejects_malformed_json(tmp_path, monkeypatch, capsys):
    words_path = tmp_path / "words.json"
    words_path.write_text("{", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["compute_duration.py", str(words_path)])
    assert compute_duration.main() == 1
    assert "Erro:" in capsys.readouterr().out
