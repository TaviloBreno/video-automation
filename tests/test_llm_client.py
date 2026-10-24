"""Tests for retrying invalid model responses."""

import json
from unittest.mock import Mock

from scripts import llm_client
from scripts.config_loader import load_config


def test_parse_scene_retries_schema_invalid_model_response(monkeypatch):
    invalid_scene = json.dumps({"elements": [], "palette": "dark-neon"})
    valid_scene = json.dumps(
        {
            "elements": [
                {
                    "type": "title",
                    "content": "Dica",
                    "duration_seconds": 3,
                }
            ],
            "palette": "dark-neon",
            "suggested_duration_hint": 5,
            "narration_text": "Uma dica simples.",
        }
    )
    model_call = Mock(side_effect=[invalid_scene, valid_scene])
    monkeypatch.setattr(llm_client, "_load_prompt_template", lambda _: "{description}")
    monkeypatch.setattr(llm_client, "_call_ollama", model_call)
    monkeypatch.setattr(llm_client, "OLLAMA_ENABLED", True)
    monkeypatch.setattr(llm_client.time, "sleep", lambda _: None)

    scene = llm_client.parse_scene("Crie um título.", cfg=load_config())

    assert scene["elements"][0]["type"] == "title"
    assert scene["narration_text"] == "Uma dica simples."
    assert model_call.call_count == 2
    assert "A resposta anterior falhou na validação" in model_call.call_args_list[1].args[0][0]["content"]


def test_parse_scene_requires_valid_sources_for_factual_elements(monkeypatch):
    source = {
        "id": "S1",
        "title": "Estudo",
        "url": "https://example.org/study",
        "publisher": "example.org",
        "snippet": "Evidence",
    }
    response = {
        "elements": [
            {"type": "title", "content": "Fato", "duration_seconds": 3},
            {
                "type": "body",
                "content": "Uma afirmação com evidência.",
                "duration_seconds": 3,
                "source_ids": ["S1"],
            },
        ],
        "palette": "dark-neon",
        "suggested_duration_hint": 6,
        "narration_text": "Uma afirmação com evidência.",
    }
    monkeypatch.setattr(llm_client, "_load_prompt_template", lambda _: "{description}")
    monkeypatch.setattr(llm_client, "_call_ollama", lambda *_: json.dumps(response))
    monkeypatch.setattr(llm_client, "OLLAMA_ENABLED", True)

    scene = llm_client.parse_scene(
        "Explique um fato.",
        cfg=load_config(),
        research_sources=[source],
    )

    assert scene["elements"][1]["source_ids"] == ["S1"]
