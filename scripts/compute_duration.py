#!/usr/bin/env python3
"""
compute_duration.py — Calcula a duração real da cena a partir de words.json.

Uso:
    from scripts.compute_duration import compute_scene_duration
    duration = compute_scene_duration("output/voice.words.json", padding=0.3)

CLI:
    python scripts/compute_duration.py output/voice.words.json --padding 0.3
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def _normalize_words(data: Any) -> List[Dict[str, Any]]:
    """Aceita lista direta ou dict com chave 'words' (formato subreel/loudkit)."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "words" in data:
        return data["words"]
    raise ValueError(f"Estrutura não reconhecida: {type(data).__name__}")


def compute_scene_duration(words_json_path: str | Path, padding: float = 0.3) -> float:
    """
    Lê words.json e retorna último_end + padding.
    Lança ValueError se o arquivo estiver vazio ou malformado.
    """
    path = Path(words_json_path)
    if not path.exists():
        raise FileNotFoundError(f"words.json não encontrado: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))
    words = _normalize_words(data)

    if not words:
        raise ValueError("words.json está vazio")

    # Extrai o maior 'end' (robusto a ordenação)
    ends = []
    for idx, w in enumerate(words):
        if not isinstance(w, dict) or "end" not in w:
            raise ValueError(f"words[{idx}] sem campo 'end'")
        if not isinstance(w["end"], (int, float)):
            raise ValueError(f"words[{idx}].end não numérico: {w['end']!r}")
        ends.append(w["end"])

    last_end = max(ends)
    return float(last_end + padding)


def main() -> int:
    parser = argparse.ArgumentParser(description="Calcula duração da cena a partir de words.json.")
    parser.add_argument("words_json", help="Caminho para voice.words.json")
    parser.add_argument("--padding", "-p", type=float, default=0.3, help="Padding em segundos (padrão: 0.3)")
    args = parser.parse_args()

    try:
        duration = compute_scene_duration(args.words_json, padding=args.padding)
    except Exception as exc:
        print(f"❌ Erro: {exc}")
        return 1

    print(f"{duration:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())