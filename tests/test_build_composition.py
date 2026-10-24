import json

from scripts import build_composition
from scripts.config_loader import load_config


def test_build_composition_renders_escaped_citations_and_original_explainer_style(
    tmp_path, monkeypatch
):
    scene_path = tmp_path / "scene.json"
    words_path = tmp_path / "words.json"
    template_path = tmp_path / "template.html"
    output_path = tmp_path / "composition.html"
    scene_path.write_text(
        json.dumps(
            {
                "palette": "dark-neon",
                "elements": [
                    {
                        "type": "title",
                        "content": "O que explica isso?",
                        "duration_seconds": 3,
                    },
                    {
                        "type": "body",
                        "content": "<script>alert(1)</script>",
                        "duration_seconds": 3,
                        "source_ids": ["S1"],
                    },
                ],
                "sources": [
                    {
                        "id": "S1",
                        "title": "Estudo <seguro>",
                        "url": "https://example.org/study",
                        "publisher": "example.org",
                        "snippet": "Evidence",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    template_path.write_text(
        "{{CLIPS}}|{{SCENE_DURATION}}|{{PALETTE_PRIMARY}}|{{PALETTE_ACCENT}}|"
        "{{PALETTE_TEXT}}|{{PALETTE_BACKGROUND}}",
        encoding="utf-8",
    )
    monkeypatch.setattr(build_composition, "load_config", load_config)
    monkeypatch.setattr(build_composition, "compute_scene_duration", lambda *_args, **_kwargs: 6)

    build_composition.build_composition(
        str(scene_path), str(words_path), str(template_path), str(output_path)
    )

    rendered = output_path.read_text(encoding="utf-8")
    assert 'clip-copy">&lt;script&gt;alert(1)&lt;/script&gt;</div>' in rendered
    assert "FONTES  /" in rendered
    assert "Estudo &lt;seguro&gt;" in rendered
    assert "explainer-clip" in rendered
    assert "{{" not in rendered
