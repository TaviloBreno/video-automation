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
