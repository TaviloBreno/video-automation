#!/usr/bin/env python3
"""
check_env.py — Verifica dependências do sistema para o pipeline de automação de vídeo.
Uso: python scripts/check_env.py
"""

import platform
import subprocess
import sys
from typing import Tuple

MIN_PYTHON = (3, 11)


def run_version(cmd: list[str]) -> Tuple[bool, str]:
    """Executa cmd e retorna (ok, primeira_linha_da_saida)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if result.returncode != 0:
            return False, (result.stderr or result.stdout).strip().splitlines()[0] if (result.stderr or result.stdout).strip() else "erro desconhecido"
        output = (result.stdout or result.stderr).strip()
        first_line = output.splitlines()[0] if output else "sem saída"
        return True, first_line
    except FileNotFoundError:
        return False, "não encontrado no PATH"
    except subprocess.TimeoutExpired:
        return False, "timeout ao executar"


def instructions(system: str, dep: str) -> str:
    """Retorna instrução de instalação conforme SO e dependência."""
    system = system.lower()

    if dep == "ffmpeg":
        if "windows" in system:
            return "  winget install --id Gyan.FFmpeg --source winget\n  (ou baixe em https://gyan.dev/ffmpeg/builds/ e adicione C:\\ffmpeg\\bin ao PATH)"
        if "darwin" in system:
            return "  brew install ffmpeg"
        return "  sudo apt update && sudo apt install ffmpeg   # Debian/Ubuntu\n  sudo dnf install ffmpeg                       # Fedora"

    if dep == "ollama":
        if "windows" in system:
            return "  Baixe e execute OllamaSetup.exe em https://ollama.com/download"
        if "darwin" in system:
            return "  Baixe o app em https://ollama.com/download ou: brew install ollama"
        return "  curl -fsSL https://ollama.com/install.sh | sh"

    if dep == "node":
        if "windows" in system:
            return "  winget install OpenJS.NodeJS.LTS\n  (ou baixe o .msi LTS em https://nodejs.org/download)"
        if "darwin" in system:
            return "  brew install node"
        return "  sudo apt install nodejs npm   # ou use nvm"

    if dep == "python":
        if "windows" in system:
            return "  Baixe o instalador em https://python.org/downloads e marque 'Add python.exe to PATH'"
        if "darwin" in system:
            return "  brew install python@3.12"
        return "  sudo apt install python3 python3-pip"

    return "  Consulte a documentação oficial."


def check_python() -> Tuple[bool, str]:
    ok = sys.version_info >= MIN_PYTHON
    ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    return ok, f"Python {ver}"


def main() -> int:
    system = platform.system()
    print(f"Sistema detectado: {platform.platform()}\n")

    checks = []

    # Python (não depende de PATH externo)
    py_ok, py_ver = check_python()
    checks.append(("Python", py_ok, py_ver, instructions(system, "python")))

    # FFmpeg
    ff_ok, ff_ver = run_version(["ffmpeg", "-version"])
    checks.append(("FFmpeg", ff_ok, ff_ver, instructions(system, "ffmpeg")))

    # Ollama
    ol_ok, ol_ver = run_version(["ollama", "--version"])
    checks.append(("Ollama", ol_ok, ol_ver, instructions(system, "ollama")))

    # Node
    nd_ok, nd_ver = run_version(["node", "--version"])
    checks.append(("Node.js", nd_ok, nd_ver, instructions(system, "node")))

    # npm (bônus, útil para T0.1)
    npm_ok, npm_ver = run_version(["npm", "--version"])
    if not npm_ok and platform.system().lower() == "windows":
        # No Windows o Python pode não resolver "npm" sem extensão;
        # tentamos o shim .cmd explicitamente.
        npm_ok, npm_ver = run_version(["npm.cmd", "--version"])
    checks.append(("npm", npm_ok, npm_ver, "  Instale Node.js LTS (inclui npm)"))

    # Impressão do relatório
    all_ok = True
    print("=" * 55)
    print("RELATÓRIO DE DEPENDÊNCIAS")
    print("=" * 55)

    for name, ok, version, help_text in checks:
        if ok:
            print(f"[OK]    {name:8} {version}")
        else:
            all_ok = False
            print(f"[ERRO]  {name:8} {version}")
            print(f"   Instalação:\n{help_text}\n")

    print("=" * 55)
    if all_ok:
        print("[OK] Todas as dependências estão instaladas.")
        return 0
    else:
        print("[ERRO] Uma ou mais dependências precisam de atenção.")
        return 1


if __name__ == "__main__":
    sys.exit(main())