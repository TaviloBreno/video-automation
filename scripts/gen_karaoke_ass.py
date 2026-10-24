#!/usr/bin/env python3
"""
gen_karaoke_ass.py — Gera ASS karaokê de alta precisão a partir de words.json,
sincronizado milimetricamente à velocidade da fala do narrador, com pausas respiratórias e frases naturais.
"""

from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _fmt_time(seconds: float) -> str:
    seconds = max(0.0, seconds)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def generate_karaoke_ass(
    words_path: str,
    output_path: str,
    font_size: int = 58,
    primary_color: str = "&H0000D7FF",    # Cor ativa durante a fala (Amarelo Dourado Vivo)
    highlight_color: str = "&H00FFFFFF",  # Cor inativa antes da fala (Branco Puro)
    play_res_x: int = 1920,
    play_res_y: int = 1080,
    margin_v: int = 80,
    font_name: str = "Arial",
) -> Path:
    words_file = Path(words_path)
    if not words_file.is_absolute():
        words_file = PROJECT_ROOT / words_file
    data = json.loads(words_file.read_text(encoding="utf-8"))
    raw_words = data["words"] if isinstance(data, dict) else data

    # Filtra palavras com duração válida
    words = [w for w in raw_words if w.get("text") and w.get("end", 0) >= w.get("start", 0)]
    if not words:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("", encoding="utf-8")
        return out

    # No padrão ASS Karaokê:
    # PrimaryColour: cor para a qual a palavra muda quando é falada (ativo)
    # SecondaryColour: cor original da palavra antes de ser dita (inativo)
    # Se highlight_color for passada como branco e primary_color como amarelo, garantimos a ordem correta:
    active_colour = primary_color if primary_color != "&H00FFFFFF" else "&H0000D7FF"
    inactive_colour = highlight_color if highlight_color != "&H0000D7FF" else "&H00FFFFFF"

    ass_lines = [
        "[Script Info]",
        "ScriptType: v4.00+",
        f"PlayResX: {play_res_x}",
        f"PlayResY: {play_res_y}",
        "ScaledBorderAndShadow: yes",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        f"Style: Default,{font_name},{font_size},{active_colour},{inactive_colour},&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,3.5,1.5,2,60,60,{margin_v},1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]

    # Agrupamento inteligente por pausas respiratórias e pontuação
    line_groups: list[list[dict]] = []
    current: list[dict] = []

    for i, w in enumerate(words):
        current.append(w)
        txt = w["text"].strip()

        next_w = words[i + 1] if i + 1 < len(words) else None
        next_gap = (next_w["start"] - w["end"]) if next_w else 0.0

        is_strong_punct = any(txt.endswith(p) for p in [".", "!", "?", ":", "..."])
        is_comma_split = txt.endswith(",") and len(current) >= 3
        is_breath_pause = next_gap >= 0.30
        is_max_words = len(current) >= 5

        if is_strong_punct or is_breath_pause or is_comma_split or is_max_words or next_w is None:
            line_groups.append(current)
            current = []

    if current:
        line_groups.append(current)

    # Gera cada linha com sincronização exata de tempo e gaps
    for idx, group in enumerate(line_groups):
        line_start = group[0]["start"]
        next_line_start = line_groups[idx + 1][0]["start"] if idx + 1 < len(line_groups) else group[-1]["end"] + 1.0

        # A linha permanece na tela por um breve respiro após o fim da fala, sem invadir a próxima
        line_end = min(group[-1]["end"] + 0.20, max(group[-1]["end"] + 0.05, next_line_start - 0.05))

        karaoke_parts = []
        for j, w in enumerate(group):
            dur_cs = max(1, int(round((w["end"] - w["start"]) * 100)))

            if j > 0:
                # Se houver silêncio ou pausa respiratória entre palavras da mesma linha
                gap = w["start"] - group[j - 1]["end"]
                if gap > 0.005:
                    gap_cs = max(1, int(round(gap * 100)))
                    karaoke_parts.append(f"{{\\k{gap_cs}}} ")
                else:
                    karaoke_parts.append(" ")

            # Preenchimento contínuo e suave na velocidade da fala do narrador
            karaoke_parts.append(f"{{\\kf{dur_cs}}}{w['text']}")

        dialogue_text = "".join(karaoke_parts).strip()
        ass_lines.append(
            f"Dialogue: 0,{_fmt_time(line_start)},{_fmt_time(line_end)},Default,,0,0,0,,{dialogue_text}"
        )

    out = Path(output_path)
    if not out.is_absolute():
        out = PROJECT_ROOT / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(ass_lines), encoding="utf-8")
    return out


if __name__ == "__main__":
    generate_karaoke_ass("output/voice.words.json", "output/subs/karaoke.ass")