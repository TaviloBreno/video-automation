#!/usr/bin/env python3
"""
render_scene.py — Chama npx hyperframes render via Python.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RENDER_DIR = PROJECT_ROOT / "render"


def render_scene(composition_path: str, out_mp4: str, timeout: int = 600) -> Path:
    """
    Renderiza a composição para MP4 via HyperFrames.
    Executa o comando de dentro da pasta 'render/' para que o HyperFrames
    encontre o projeto corretamente.
    """
    # O caminho de saída é relativo à raiz do projeto (output/final.mp4)
    out_path = (
        (PROJECT_ROOT / out_mp4).resolve()
        if not Path(out_mp4).is_absolute()
        else Path(out_mp4)
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Verifica se a composição (HTML) existe, apenas para validação
    composition_file = (
        (PROJECT_ROOT / composition_path).resolve()
        if not Path(composition_path).is_absolute()
        else Path(composition_path)
    )
    if not composition_file.exists():
        raise FileNotFoundError(f"Composição não encontrada: {composition_file}")

    npx_path = shutil.which("npx")
    if not npx_path:
        raise RuntimeError(
            "npx não encontrado no PATH. Instale o Node.js e reinicie o terminal."
        )

    # O comando agora é simples, pois o cwd será a pasta 'render/'
    # O HyperFrames usará o index.html (ou composition.html se você renomear)
    # Se você quiser apontar para um arquivo específico, use --composition (se suportado)
    cmd = [
        npx_path,
        "hyperframes",
        "render",
        "--output",
        str(out_path),
    ]

    for attempt in range(1, 3):
        print(f"Render tentativa {attempt}/2...")
        try:
            result = subprocess.run(
                cmd,
                cwd=str(RENDER_DIR),
                capture_output=True,
                text=True,
                encoding="utf-8",  # <-- Adicione
                errors="replace",  # <-- Adicione
                timeout=timeout,
                check=False,
            )
            if result.returncode == 0 and out_path.exists():
                print(f"✅ Render concluído: {out_path}")
                return out_path
            else:
                stderr_tail = (result.stderr or "")[-800:]
                print(f"⚠️ Falha (exit {result.returncode}): {stderr_tail}")
        except subprocess.TimeoutExpired:
            print(f"⚠️ Timeout de {timeout}s")

        if attempt < 2:
            time.sleep(5)

    raise RuntimeError(f"Render falhou após 2 tentativas: {out_path}")


if __name__ == "__main__":
    render_scene("render/src/composition.html", "output/final.mp4")
