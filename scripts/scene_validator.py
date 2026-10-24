#!/usr/bin/env python3
"""
scene_validator.py — Validação formal do JSON de cena usando jsonschema.

Uso:
    from scripts.scene_validator import validate_scene, SCENE_SCHEMA
    validate_scene(scene_dict)  # lança SceneValidationError se inválido
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator, ValidationError

# Paletas conhecidas (mantém em sincronia com config/palettes.json)
KNOWN_PALETTES = [
    "dark-neon", "clean-light", "corporate-blue", "warm-sunset",
    "tiktok-bold", "forest-green", "purple-haze", "mono-contrast",
]

# Schema formal da cena
SCENE_SCHEMA: Dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["elements", "palette", "suggested_duration_hint", "narration_text"],
    "additionalProperties": False,
    "properties": {
        "elements": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["type", "duration_seconds"],
                "additionalProperties": False,
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["title", "subtitle", "body", "image", "shape"],
                    },
                    "content": {"type": "string", "minLength": 1},
                    "position": {
                        "type": "string",
                        "enum": ["top", "center", "bottom"],
                    },
                    "animation": {
                        "type": "string",
                        "enum": ["fade", "slide-up", "slide-left", "zoom", "none"],
                    },
                    "duration_seconds": {"type": "number", "exclusiveMinimum": 0},
                    "source_ids": {
                        "type": "array",
                        "items": {"type": "string", "minLength": 1},
                        "uniqueItems": True,
                    },
                },
                # Regra condicional: elementos de texto exigem content
                "allOf": [
                    {
                        "if": {
                            "properties": {"type": {"enum": ["title", "subtitle", "body"]}},
                            "required": ["type"],
                        },
                        "then": {"required": ["content"]},
                    }
                ],
            },
        },
        "palette": {
            "type": "string",
            "enum": KNOWN_PALETTES,
        },
        "suggested_duration_hint": {"type": "number", "minimum": 5, "maximum": 120},
        "narration_text": {"type": "string", "minLength": 1},
        "sources": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "title", "url", "publisher", "snippet"],
                "additionalProperties": False,
                "properties": {
                    "id": {"type": "string", "minLength": 1},
                    "title": {"type": "string", "minLength": 1},
                    "url": {"type": "string", "format": "uri"},
                    "publisher": {"type": "string", "minLength": 1},
                    "snippet": {"type": "string"},
                },
            },
        },
    },
}


class SceneValidationError(ValueError):
    """Erro de validação com mensagens específicas por caminho."""

    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__("\n".join(errors))


def _format_error_path(error: ValidationError) -> str:
    """Converte o caminho do erro do jsonschema para notação legível."""
    path = list(error.absolute_path)
    if not path:
        return "root"

    parts = []
    for p in path:
        if isinstance(p, int):
            parts.append(f"[{p}]")
        else:
            if parts:
                parts.append(".")
            parts.append(str(p))
    return "".join(parts)


def _build_specific_message(error: ValidationError) -> str:
    """Gera mensagem específica a partir do ValidationError."""
    path = _format_error_path(error)
    validator = error.validator
    value = error.validator_value

    if validator == "required":
        # error.message: "'animation' is a required property"
        missing = error.message.split("'")[1] if "'" in error.message else "campo"
        return f"{path}: campo obrigatório ausente '{missing}'"

    if validator == "enum":
        allowed = ", ".join(str(v) for v in value)
        return f"{path}: valor inválido {error.instance!r}. Permitidos: {allowed}"

    if validator == "type":
        return f"{path}: tipo inválido (esperado {value}, recebido {type(error.instance).__name__})"

    if validator == "minItems":
        return f"{path}: deve ter pelo menos {value} item(ns)"

    if validator == "minLength":
        return f"{path}: não pode ser vazio"

    if validator == "exclusiveMinimum":
        return f"{path}: deve ser maior que {value}"

    if validator == "minimum":
        return f"{path}: deve ser maior ou igual a {value}"

    if validator == "maximum":
        return f"{path}: deve ser menor ou igual a {value}"

    # Fallback: usa a mensagem padrão do jsonschema
    return f"{path}: {error.message}"


def validate_scene(scene: Any, schema: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    Valida o dict de cena contra o schema formal.
    Lança SceneValidationError com todas as mensagens específicas se inválido.
    Retorna o próprio dict se válido.
    """
    if not isinstance(scene, dict):
        raise SceneValidationError([f"root: esperado objeto, recebido {type(scene).__name__}"])

    validator = Draft202012Validator(schema or SCENE_SCHEMA)
    errors = sorted(validator.iter_errors(scene), key=lambda e: list(e.absolute_path))

    if errors:
        messages = [_build_specific_message(e) for e in errors]
        raise SceneValidationError(messages)

    sources = scene.get("sources")
    if (
        (schema is None or schema == SCENE_SCHEMA)
        and "sources" in scene
        and "elements" in scene
    ):
        known_ids = {source["id"] for source in sources}
        if len(known_ids) != len(sources):
            raise SceneValidationError(["sources contém IDs duplicados"])
        source_errors = []
        for index, source in enumerate(sources):
            try:
                url = source.get("url")
                if not isinstance(url, str):
                    raise ValueError("URL deve ser string")
                parsed_url = urlsplit(url)
            except ValueError:
                parsed_url = None
            if (
                parsed_url is None
                or parsed_url.scheme not in {"http", "https"}
                or not parsed_url.hostname
            ):
                source_errors.append(
                    f"sources[{index}].url deve ser uma URL HTTP ou HTTPS válida"
                )
        for index, element in enumerate(scene["elements"]):
            source_ids = element.get("source_ids", [])
            unknown_ids = set(source_ids) - known_ids
            if unknown_ids:
                source_errors.append(
                    f"elements[{index}].source_ids contém IDs desconhecidos: "
                    f"{sorted(unknown_ids)}"
                )
            if element["type"] in {"body", "subtitle"} and not source_ids:
                source_errors.append(
                    f"elements[{index}] é uma afirmação textual e precisa de source_ids"
                )
        if source_errors:
            raise SceneValidationError(source_errors)

    return scene


# ---------------------------------------------------------------------------
# CLI para testar um JSON manualmente
# ---------------------------------------------------------------------------

def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Valida um JSON de cena contra o schema.")
    parser.add_argument("json_file", help="Caminho para o arquivo JSON")
    args = parser.parse_args()

    path = Path(args.json_file)
    if not path.exists():
        print(f"❌ Arquivo não encontrado: {path}")
        return 1

    try:
        scene = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"❌ JSON inválido: {exc}")
        return 1

    try:
        validate_scene(scene)
    except SceneValidationError as exc:
        print("❌ Cena inválida:")
        for msg in exc.errors:
            print(f"   - {msg}")
        return 1

    print("✅ Cena válida.")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())