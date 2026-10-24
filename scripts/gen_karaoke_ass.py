#!/usr/bin/env python3
"""
gen_karaoke_ass.py — Gera ASS karaokê a partir de words.json.
"""

from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _fmt_time(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def generate_karaoke_ass(
    words_path: str,
    output_path: str,
    font_size: int = 64,
    primary_color: str = "&H00FFFFFF",
    highlight_color: str = "&H0000FFFF",
    play_res_x: int = 1080,
    play_res_y: int = 1920,
    margin_v: int = 150,
) -> Path:
    words_file = Path(words_path)
    if not words_file.is_absolute():
        words_file = PROJECT_ROOT / words_file
    data = json.loads(words_file.read_text(encoding="utf-8"))
    words = data["words"] if isinstance(data, dict) else data

    ass_lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        f"PlayResX: {play_res_x}",
        f"PlayResY: {play_res_y}",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Default,Arial,{font_size},{primary_color},{highlight_color},&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,3,1,2,50,50,{margin_v},1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]

    # Agrupa em linhas de até 5 palavras
    line_groups = []
    current = []
    for w in words:
        current.append(w)
        if len(current) >= 5:
            line_groups.append(current)
            current = []
    if current:
        line_groups.append(current)

    for group in line_groups:
        start = group[0]["start"]
        end = group[-1]["end"]

        karaoke_text = ""
        for w in group:
            dur_cs = max(1, int((w["end"] - w["start"]) * 100))
            karaoke_text += f"{{\\kf{dur_cs}}}{w['text']} "

        ass_lines.append(
            f"Dialogue: 0,{_fmt_time(start)},{_fmt_time(end)},Default,,0,0,0,,{karaoke_text.strip()}"
        )

    out = Path(output_path)
    if not out.is_absolute():
        out = PROJECT_ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(ass_lines), encoding="utf-8")
    print(f"ASS karaokê gerado: {out}")
    return out


if __name__ == "__main__":
    generate_karaoke_ass("output/voice.words.json", "output/subs/karaoke.ass")