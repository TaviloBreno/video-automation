#!/usr/bin/env python3
"""
build_composition.py — Gera render/src/composition.html a partir de scene.json.
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.compute_duration import compute_scene_duration
from scripts.config_loader import load_config, get_palette


def build_composition(scene_path: str, words_path: str, template_path: str, output_path: str):
    scene = json.loads(Path(scene_path).read_text(encoding="utf-8"))
    cfg = load_config()
    palette = get_palette(scene["palette"], cfg)
    scene_duration = compute_scene_duration(words_path, padding=0.3)

    template = Path(template_path).read_text(encoding="utf-8")

    # Gera os clips HTML
    clips_html = []
    cursor = 0.0
    for el in scene["elements"]:
        dur = el.get("duration_seconds", 3)
        anim = el.get("animation", "fade-in")
        content = el.get("content", "")
        pos = el.get("position", "center")

        # Mapeia posição para CSS
        top = {"top": "10%", "center": "50%", "bottom": "85%"}.get(pos, "50%")

        clips_html.append(f'''
    <div id="el-{len(clips_html)}" class="clip" 
         data-start="{cursor}" data-duration="{dur}" 
         data-animation="{anim}"
         style="position:absolute; top:{top}; left:50%; transform:translate(-50%,-50%); 
                color:var(--paletteText); font-size:64px; text-align:center; width:90%;">
      {content}
    </div>''')
        cursor += dur

    # Substitui placeholders no template
    html = template.replace("{{CLIPS}}", "\n".join(clips_html))
    html = html.replace("{{SCENE_DURATION}}", str(scene_duration))
    html = html.replace("{{PALETTE_PRIMARY}}", palette.primary)
    html = html.replace("{{PALETTE_ACCENT}}", palette.accent)
    html = html.replace("{{PALETTE_TEXT}}", palette.text)
    html = html.replace("{{PALETTE_BACKGROUND}}", palette.background)

    Path(output_path).write_text(html, encoding="utf-8")
    print(f"✅ Composição gerada: {output_path} (duração: {scene_duration:.2f}s)")
    return scene_duration


if __name__ == "__main__":
    build_composition(
        scene_path="output/scene.json",
        words_path="output/voice.words.json",
        template_path="render/src/template.html",
        output_path="render/index.html",  
    )