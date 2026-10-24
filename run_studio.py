#!/usr/bin/env python3
"""
run_studio.py — Inicia a Interface Web do Studio AI para automação de vídeos e Shorts virais.
"""

import sys
import webbrowser
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from web.server import start_server

if __name__ == "__main__":
    # Abre o navegador automaticamente após 1 segundo
    def _open_browser():
        import time
        time.sleep(1.2)
        webbrowser.open("http://localhost:5000")

    import threading
    threading.Thread(target=_open_browser, daemon=True).start()

    start_server(host="127.0.0.1", port=5000)
