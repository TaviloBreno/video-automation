#!/usr/bin/env python3
"""
build_composition.py — Gera render/src/composition.html a partir de scene.json.
"""

import json
import html
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.compute_duration import compute_scene_duration
from scripts.config_loader import load_config, get_palette


def build_composition(
    scene_path: str,
    words_path: str,
    template_path: str,
    output_path: str,
    padding: float = 0.3,
):
    scene = json.loads(Path(scene_path).read_text(encoding="utf-8"))
    cfg = load_config()
    palette = get_palette(scene["palette"], cfg)
    scene_duration = compute_scene_duration(words_path, padding=padding)

    template = Path(template_path).read_text(encoding="utf-8")
    sources = {source["id"]: source for source in scene.get("sources", [])}

    clips_html = []
    cursor = 0.0
    role_labels = {
        "title": "A PERGUNTA",
        "subtitle": "IDEIA-CHAVE",
        "body": "MECANISMO",
        "image": "OBSERVAÇÃO",
        "shape": "MODELO",
    }
    animation_names = {"fade": "fade-in", "zoom": "scale-in"}
    for index, el in enumerate(scene["elements"], start=1):
        dur = el.get("duration_seconds", 3)
        anim = animation_names.get(el.get("animation", "fade"), el.get("animation", "fade"))
        if anim == "none":
            anim = ""
        content = html.escape(str(el.get("content", "")))
        pos = el.get("position", "center")
        source_ids = el.get("source_ids", [])
        cited_sources = [
            sources[source_id]
            for source_id in source_ids
            if source_id in sources
        ]
        source_line = ""
        if cited_sources:
            citations = "  ·  ".join(
                (
                    f'<span class="citation" title="{html.escape(source["url"], quote=True)}">'
                    f'<b>[{html.escape(source["id"])}]</b> '
                    f'{html.escape(source["title"])}'
                    f'<i> — {html.escape(source["publisher"])}</i></span>'
                )
                for source in cited_sources
            )
            source_line = (
                f'<div class="clip-sources">FONTES  /  {citations}</div>'
            )

        top = {"top": "27%", "center": "51%", "bottom": "75%"}.get(pos, "51%")
        role = html.escape(role_labels.get(el.get("type"), "EVIDÊNCIA"))

        clips_html.append(f'''
    <div id="el-{index}" class="clip explainer-clip"
         data-start="{cursor}" data-duration="{dur}"
         data-animation="{anim}"
         style="--clip-top:{top}; --clip-index:'{index}'">
      <div class="clip-heading">
        <span class="clip-index">{index:02d}</span>
        <span class="clip-role">{role}</span>
      </div>
      <div class="clip-copy">{content}</div>
      {source_line}
    </div>''')
        cursor += dur

    rendered_html = template.replace("{{CLIPS}}", "\n".join(clips_html))
    rendered_html = rendered_html.replace("{{SCENE_DURATION}}", str(scene_duration))
    rendered_html = rendered_html.replace("{{PALETTE_PRIMARY}}", palette.primary)
    rendered_html = rendered_html.replace("{{PALETTE_ACCENT}}", palette.accent)
    rendered_html = rendered_html.replace("{{PALETTE_TEXT}}", palette.text)
    rendered_html = rendered_html.replace("{{PALETTE_BACKGROUND}}", palette.background)

    Path(output_path).write_text(rendered_html, encoding="utf-8")
    print(f"Composição gerada: {output_path} (duração: {scene_duration:.2f}s)")
    return scene_duration


if __name__ == "__main__":
    build_composition(
        scene_path="output/scene.json",
        words_path="output/voice.words.json",
        template_path="render/src/template.html",
        output_path="render/index.html",  
    )