#!/usr/bin/env python3
"""
render_scene.py — Chama npx hyperframes render via Python com streaming de progresso,
limpeza de travas (locks) e encerramento limpo da árvore de processos.
"""

from __future__ import annotations

import json
import logging
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger("render_scene")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RENDER_DIR = PROJECT_ROOT / "render"


def _clean_stale_locks() -> None:
    """Remove diretórios ou arquivos de trava deixados por processos anteriores interrompidos."""
    hyperframes_dir = RENDER_DIR / ".hyperframes"
    if not hyperframes_dir.exists():
        return
    for lock in hyperframes_dir.glob("*lock"):
        try:
            if lock.is_dir():
                shutil.rmtree(lock, ignore_errors=True)
            else:
                lock.unlink(missing_ok=True)
            logger.info("Trava antiga removida: %s", lock.name)
        except Exception as exc:
            logger.warning("Falha ao remover trava %s: %s", lock.name, exc)


def _kill_process_tree(pid: int) -> None:
    """Mata a árvore de processos completa (npx -> node -> chrome workers) no Windows ou Unix."""
    try:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                capture_output=True,
                check=False,
            )
        else:
            import os
            import signal
            os.killpg(os.getpgid(pid), signal.SIGKILL)
    except Exception as exc:
        logger.debug("Erro ao finalizar processo %s: %s", pid, exc)


def render_scene(
    composition_path: str,
    out_mp4: str,
    timeout: int = 600,
    progress: Optional[Callable[[float, str], None]] = None,
    cancelled: Optional[Callable[[], bool]] = None,
) -> Path:
    """
    Renderiza a composição para MP4 via HyperFrames.
    Executa o comando de dentro da pasta 'render/' para que o HyperFrames
    encontre o projeto corretamente.
    """
    out_path = (
        (PROJECT_ROOT / out_mp4).resolve()
        if not Path(out_mp4).is_absolute()
        else Path(out_mp4)
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)

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

    cmd = [
        npx_path,
        "--yes",
        "hyperframes",
        "render",
        "--output",
        str(out_path),
    ]

    for attempt in range(1, 3):
        if cancelled and cancelled():
            from scripts.long_video import JobCancelled
            raise JobCancelled("Cancelado antes de iniciar render.")

        logger.info("Render tentativa %d/2 para %s...", attempt, out_path.name)
        print(f"Render tentativa {attempt}/2...", flush=True)
        _clean_stale_locks()

        proc = None
        try:
            proc = subprocess.Popen(
                cmd,
                cwd=str(RENDER_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )

            start_time = time.time()
            last_progress_time = start_time

            while True:
                if cancelled and cancelled():
                    logger.info("Cancelamento solicitado. Finalizando processo de render...")
                    if proc and proc.poll() is None:
                        _kill_process_tree(proc.pid)
                    _clean_stale_locks()
                    from scripts.long_video import JobCancelled
                    raise JobCancelled("Job cancelado pelo usuário durante o render.")

                line = proc.stdout.readline() if proc.stdout else ""
                if not line and proc.poll() is not None:
                    break

                if line:
                    line_clean = line.strip()
                    if line_clean.startswith("@hf-progress"):
                        try:
                            data = json.loads(line_clean.replace("@hf-progress", "").strip())
                            code = data.get("code", "")
                            pct = float(data.get("pct", 0))
                            done = data.get("done")
                            total = data.get("total")
                            msg = f"{code} {pct:.0f}%"
                            if done is not None and total is not None:
                                msg = f"{code} {done}/{total} ({pct:.0f}%)"
                            if progress:
                                progress(pct, msg)
                        except Exception:
                            pass
                    elif "%" in line_clean:
                        # Extrai mensagem de progresso do CLI (ex: "Capturing frame 120/1097")
                        m = re.search(r"(\d+%\s+.*)", line_clean)
                        if m and progress:
                            pct_m = re.search(r"(\d+)%", m.group(1))
                            pct_val = float(pct_m.group(1)) if pct_m else 0.0
                            progress(pct_val, m.group(1))

                    # Se a linha contiver informação relevante de status ou erro, logar
                    if any(k in line_clean for k in ("Error", "error", "Fail", "fail", "Render complete", "Compiling")):
                        logger.info("[HyperFrames] %s", line_clean)

                if time.time() - start_time > timeout:
                    logger.warning("Timeout de %ds atingido no render.", timeout)
                    if proc and proc.poll() is None:
                        _kill_process_tree(proc.pid)
                    _clean_stale_locks()
                    break

            proc.wait()

            if proc.returncode == 0 and out_path.exists():
                logger.info("Render concluído com sucesso: %s", out_path)
                print(f"Render concluído: {out_path}", flush=True)
                _clean_stale_locks()
                return out_path
            else:
                logger.warning("Tentativa %d falhou com código %d", attempt, proc.returncode)
        except Exception as exc:
            if "JobCancelled" in type(exc).__name__:
                raise
            logger.warning("Erro na tentativa %d de render: %s", attempt, exc)
            if proc and proc.poll() is None:
                _kill_process_tree(proc.pid)
            _clean_stale_locks()

        if attempt < 2:
            time.sleep(5)

    _clean_stale_locks()
    raise RuntimeError(f"Render falhou após 2 tentativas: {out_path}")


if __name__ == "__main__":
    render_scene("render/src/composition.html", "output/final.mp4")
