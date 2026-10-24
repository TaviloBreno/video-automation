"""Unit tests for scene and schema validation."""

import json
import sys

import pytest
from jsonschema import Draft202012Validator

from scripts import scene_validator
from scripts.scene_validator import SceneValidationError, validate_scene


def _valid_scene():
    return {
        "elements": [
            {"type": "title", "content": "LANÇAMENTO", "position": "center",
             "animation": "fade", "duration_seconds": 4},
            {"type": "subtitle", "content": "Conheça o novo produto",
             "position": "bottom", "animation": "slide-up", "duration_seconds": 3},
        ],
        "palette": "dark-neon",
        "suggested_duration_hint": 7,
        "narration_text": "Apresentamos o novo produto.",
    }


def test_valid_minimal():
    """Caso válido 1: cena mínima com 1 title."""
    scene = {
        "elements": [
            {"type": "title", "content": "X", "duration_seconds": 3},
        ],
        "palette": "clean-light",
        "suggested_duration_hint": 5,
        "narration_text": "Texto.",
    }
    assert validate_scene(scene) is scene


def test_valid_full():
    """Caso válido 2: cena completa com múltiplos elementos."""
    assert validate_scene(_valid_scene()) is not None


def test_validates_referenced_sources_and_factual_elements():
    scene = _valid_scene()
    scene["sources"] = [
        {
            "id": "S1",
            "title": "Evidência científica",
            "url": "https://example.org/study",
            "publisher": "example.org",
            "snippet": "Resumo da evidência.",
        }
    ]
    scene["elements"][1]["source_ids"] = ["S1"]

    assert validate_scene(scene) is scene


def test_rejects_factual_element_without_source_ids():
    scene = _valid_scene()
    scene["sources"] = [
        {
            "id": "S1",
            "title": "Evidência científica",
            "url": "https://example.org/study",
            "publisher": "example.org",
            "snippet": "Resumo da evidência.",
        }
    ]

    with pytest.raises(SceneValidationError, match="precisa de source_ids"):
        validate_scene(scene)


def test_rejects_unknown_source_id():
    scene = _valid_scene()
    scene["sources"] = [
        {
            "id": "S1",
            "title": "Evidência científica",
            "url": "https://example.org/study",
            "publisher": "example.org",
            "snippet": "Resumo da evidência.",
        }
    ]
    scene["elements"][1]["source_ids"] = ["S2"]

    with pytest.raises(SceneValidationError, match="IDs desconhecidos"):
        validate_scene(scene)


def test_rejects_non_http_source_url():
    scene = _valid_scene()
    scene["sources"] = [
        {
            "id": "S1",
            "title": "Evidência científica",
            "url": "javascript:alert(1)",
            "publisher": "example.org",
            "snippet": "Resumo da evidência.",
        }
    ]

    with pytest.raises(SceneValidationError, match="URL HTTP ou HTTPS"):
        validate_scene(scene)


def test_valid_no_optional_fields():
    """Caso válido 3: elementos sem position/animation (opcionais)."""
    scene = {
        "elements": [
            {"type": "title", "content": "X", "duration_seconds": 3},
        ],
        "palette": "tiktok-bold",
        "suggested_duration_hint": 5,
        "narration_text": "Texto.",
    }
    assert validate_scene(scene) is not None


def test_invalid_missing_animation():
    """Caso inválido 1: title sem duration_seconds (campo obrigatório)."""
    scene = _valid_scene()
    del scene["elements"][0]["duration_seconds"]
    with pytest.raises(SceneValidationError) as exc_info:
        validate_scene(scene)
    messages = "\n".join(exc_info.value.errors)
    assert "duration_seconds" in messages
    assert "[0]" in messages


def test_invalid_palette_and_content():
    """Caso inválido 2: palette inválida + body sem content."""
    scene = _valid_scene()
    scene["palette"] = "azul"
    scene["elements"].append({"type": "body", "duration_seconds": 3})
    with pytest.raises(SceneValidationError) as exc_info:
        validate_scene(scene)
    messages = "\n".join(exc_info.value.errors)
    assert "palette" in messages
    assert "content" in messages


@pytest.mark.parametrize("scene", [None, [], "scene", 42])
def test_rejects_non_object_scene(scene):
    with pytest.raises(SceneValidationError, match="esperado objeto"):
        validate_scene(scene)


def test_supports_custom_schema():
    value = {"title": "custom value"}
    assert validate_scene(value, {"type": "object", "required": ["title"]}) is value


@pytest.mark.parametrize(
    ("schema", "instance", "expected"),
    [
        ({"type": "object", "required": ["title"]}, {}, "campo obrigatório ausente"),
        ({"enum": ["ok"]}, "bad", "valor inválido"),
        ({"type": "string"}, 2, "tipo inválido"),
        ({"type": "array", "minItems": 1}, [], "pelo menos 1"),
        ({"type": "string", "minLength": 1}, "", "não pode ser vazio"),
        ({"type": "number", "exclusiveMinimum": 0}, 0, "deve ser maior que 0"),
        ({"type": "number", "minimum": 1}, 0, "maior ou igual a 1"),
        ({"type": "number", "maximum": 1}, 2, "menor ou igual a 1"),
        ({"type": "object", "additionalProperties": False}, {"extra": 1}, "Additional properties"),
    ],
)
def test_formats_schema_errors(schema, instance, expected):
    error = next(Draft202012Validator(schema).iter_errors(instance))
    message = scene_validator._build_specific_message(error)
    assert expected.lower() in message.lower()


def test_formats_nested_error_path():
    error = next(
        Draft202012Validator(
            {"type": "object", "properties": {"items": {"type": "array", "items": {"type": "string"}}}}
        ).iter_errors({"items": [1]})
    )
    assert scene_validator._format_error_path(error) == "items[0]"


def test_scene_validator_cli_reports_missing_invalid_and_valid_files(tmp_path, monkeypatch, capsys):
    scene_path = tmp_path / "scene.json"
    monkeypatch.setattr(sys, "argv", ["scene_validator.py", str(scene_path)])
    assert scene_validator.main() == 1
    assert "Arquivo não encontrado" in capsys.readouterr().out

    scene_path.write_text("{", encoding="utf-8")
    assert scene_validator.main() == 1
    assert "JSON inválido" in capsys.readouterr().out

    scene_path.write_text(json.dumps({"elements": []}), encoding="utf-8")
    assert scene_validator.main() == 1
    assert "Cena inválida" in capsys.readouterr().out

    scene_path.write_text(json.dumps(_valid_scene()), encoding="utf-8")
    assert scene_validator.main() == 0
    assert "Cena válida" in capsys.readouterr().out