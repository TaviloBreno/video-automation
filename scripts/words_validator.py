#!/usr/bin/env python3
"""
words_validator.py — Valida voice.words.json contra o MP3 correspondente.

Uso:
    python scripts/words_validator.py output/voice.words.json output/voice.mp3
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List


def _get_mp3_duration(mp3_path: Path) -> float:
    """Retorna a duração do MP3 em segundos via ffprobe."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(mp3_path)],
        capture_output=True, text=True, timeout=30, check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe falhou: {result.stderr}")
    return float(result.stdout.strip())


def _normalize_words(data: Any) -> List[Dict[str, Any]]:
    """Aceita lista direta ou dict com chave 'words' (formato do subreel)."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "words" in data:
        return data["words"]
    raise ValueError(f"Estrutura não reconhecida: {type(data).__name__}")


def validate_words(words_path: Path, mp3_path: Path, tolerance: float = 1.5) -> List[str]:
    """
    Valida words.json contra o MP3.
    Retorna lista de warnings (vazia = tudo OK).
    Lança ValueError para erros estruturais graves.
    """
    warnings: List[str] = []
    data = json.loads(words_path.read_text(encoding="utf-8"))
    words = _normalize_words(data)

    if not words:
        raise ValueError("words.json está vazio")

    for idx, w in enumerate(words):
        if not isinstance(w, dict):
            raise ValueError(f"words[{idx}] não é objeto")

        # subreel usa 'text'; aceitamos 'word' por compatibilidade
        text_field = w.get("text") or w.get("word")
        if not isinstance(text_field, str) or not text_field.strip():
            raise ValueError(f"words[{idx}] sem campo de texto ('text' ou 'word')")

        if "start" not in w or "end" not in w:
            raise ValueError(f"words[{idx}] sem 'start' ou 'end'")
        if not isinstance(w["start"], (int, float)) or not isinstance(w["end"], (int, float)):
            raise ValueError(f"words[{idx}] start/end não numéricos")
        if w["end"] <= w["start"]:
            raise ValueError(f"words[{idx}] end ({w['end']}) <= start ({w['start']})")

    for idx in range(1, len(words)):
        if words[idx]["start"] < words[idx - 1]["start"]:
            raise ValueError(
                f"Timestamps não monotônicos: words[{idx}].start ({words[idx]['start']}) "
                f"< words[{idx-1}].start ({words[idx-1]['start']})"
            )

    mp3_duration = _get_mp3_duration(mp3_path)
    last_end = words[-1]["end"]
    diff = mp3_duration - last_end

    if diff > tolerance:
        warnings.append(
            f"Último end ({last_end:.2f}s) está {diff:.2f}s antes da duração do MP3 "
            f"({mp3_duration:.2f}s). Possível truncamento."
        )
    elif last_end > mp3_duration + tolerance:
        warnings.append(
            f"Último end ({last_end:.2f}s) excede a duração do MP3 "
            f"({mp3_duration:.2f}s) em {last_end - mp3_duration:.2f}s."
        )

    return warnings


def main() -> int:
    if len(sys.argv) != 3:
        print("Uso: python scripts/words_validator.py <words.json> <mp3>")
        return 2

    words_path, mp3_path = Path(sys.argv[1]), Path(sys.argv[2])
    if not words_path.exists():
        print(f"❌ Não encontrado: {words_path}")
        return 1
    if not mp3_path.exists():
        print(f"❌ Não encontrado: {mp3_path}")
        return 1

    try:
        warnings = validate_words(words_path, mp3_path)
    except Exception as exc:
        print(f"❌ Erro estrutural: {exc}")
        return 1

    if warnings:
        print("⚠️  Warnings:")
        for w in warnings:
            print(f"   - {w}")
        return 0

    print("✅ words.json válido e consistente com o MP3.")
    return 0


if __name__ == "__main__":
    sys.exit(main())