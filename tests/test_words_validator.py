"""Unit tests for word-timing validation."""

import json
import sys
from unittest.mock import Mock

import pytest

from scripts import words_validator
from scripts.words_validator import validate_words


def _write_words(tmp_path, data):
    path = tmp_path / "words.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_accepts_list_and_wrapped_words_and_word_alias(tmp_path, monkeypatch):
    monkeypatch.setattr(words_validator, "_get_mp3_duration", lambda _: 2.0)
    mp3_path = tmp_path / "voice.mp3"
    mp3_path.touch()

    direct = _write_words(tmp_path, [{"text": "Olá", "start": 0, "end": 1.5}])
    wrapped = _write_words(
        tmp_path,
        {"words": [{"word": "mundo", "start": 1, "end": 1.8}]},
    )
    assert validate_words(direct, mp3_path) == []
    assert validate_words(wrapped, mp3_path) == []


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({}, "Estrutura não reconhecida"),
        ({"words": []}, "está vazio"),
        ({"words": ["Olá"]}, "não é objeto"),
        ([{"start": 0, "end": 1}], "sem campo de texto"),
        ([{"text": "oi", "end": 1}], "sem 'start' ou 'end'"),
        ([{"text": "oi", "start": "0", "end": 1}], "não numéricos"),
        ([{"text": "oi", "start": 1, "end": 1}], r"end \(1\) <= start"),
    ],
)
def test_rejects_structurally_invalid_word_data(tmp_path, payload, message):
    path = _write_words(tmp_path, payload)
    with pytest.raises(ValueError, match=message):
        validate_words(path, tmp_path / "unused.mp3")


def test_rejects_non_monotonic_start_times(tmp_path):
    path = _write_words(
        tmp_path,
        [
            {"text": "primeira", "start": 1, "end": 1.5},
            {"text": "segunda", "start": 0.5, "end": 1.8},
        ],
    )
    with pytest.raises(ValueError, match="não monotônicos"):
        validate_words(path, tmp_path / "unused.mp3")


@pytest.mark.parametrize(
    ("duration", "last_end", "warning"),
    [
        (5.0, 1.0, "Possível truncamento"),
        (1.0, 5.0, "excede a duração"),
        (2.0, 1.0, None),
    ],
)
def test_duration_mismatch_warnings(tmp_path, monkeypatch, duration, last_end, warning):
    monkeypatch.setattr(words_validator, "_get_mp3_duration", lambda _: duration)
    words_path = _write_words(
        tmp_path,
        [{"text": "palavra", "start": 0, "end": last_end}],
    )
    mp3_path = tmp_path / "voice.mp3"
    mp3_path.touch()
    messages = validate_words(words_path, mp3_path, tolerance=1.5)
    if warning:
        assert len(messages) == 1
        assert warning in messages[0]
    else:
        assert messages == []


def test_get_mp3_duration_reports_ffprobe_failure(monkeypatch, tmp_path):
    class Result:
        returncode = 1
        stderr = "invalid audio"

    run = Mock(return_value=Result())
    monkeypatch.setattr(words_validator.subprocess, "run", run)
    with pytest.raises(RuntimeError, match="ffprobe falhou: invalid audio"):
        words_validator._get_mp3_duration(tmp_path / "voice.mp3")
    run.assert_called_once()


def test_get_mp3_duration_parses_ffprobe_output(monkeypatch, tmp_path):
    class Result:
        returncode = 0
        stdout = "12.375\n"

    run = Mock(return_value=Result())
    monkeypatch.setattr(words_validator.subprocess, "run", run)
    assert words_validator._get_mp3_duration(tmp_path / "voice.mp3") == 12.375
    run.assert_called_once()


def test_cli_reports_missing_files_and_warnings(tmp_path, monkeypatch, capsys):
    words_path = tmp_path / "words.json"
    mp3_path = tmp_path / "voice.mp3"
    monkeypatch.setattr(sys, "argv", ["words_validator.py", str(words_path), str(mp3_path)])
    assert words_validator.main() == 1
    assert "Não encontrado" in capsys.readouterr().out

    words_path.write_text(json.dumps([{"text": "oi", "start": 0, "end": 1}]), encoding="utf-8")
    mp3_path.touch()
    monkeypatch.setattr(words_validator, "_get_mp3_duration", lambda _: 4.0)
    assert words_validator.main() == 0
    assert "Warnings" in capsys.readouterr().out

    monkeypatch.setattr(words_validator, "_get_mp3_duration", lambda _: 1.0)
    assert words_validator.main() == 0
    assert "válido e consistente" in capsys.readouterr().out


def test_cli_rejects_wrong_arguments(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["words_validator.py"])
    assert words_validator.main() == 2
    assert "Uso:" in capsys.readouterr().out


def test_cli_reports_invalid_json(tmp_path, monkeypatch, capsys):
    words_path = tmp_path / "words.json"
    mp3_path = tmp_path / "voice.mp3"
    words_path.write_text("{", encoding="utf-8")
    mp3_path.touch()
    monkeypatch.setattr(sys, "argv", ["words_validator.py", str(words_path), str(mp3_path)])
    assert words_validator.main() == 1
    assert "Erro estrutural" in capsys.readouterr().out
