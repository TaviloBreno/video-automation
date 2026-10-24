#!/usr/bin/env python3
"""Testes unitários do scene_validator (T1.3)."""

import pytest
from scripts.scene_validator import validate_scene, SceneValidationError


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