#!/usr/bin/env python3
"""
generate_voice.py — Gera MP3 + words.json a partir de texto via subreel tts.

Uso:
    from scripts.generate_voice import generate_voice
    mp3, words = generate_voice("texto...", "pt-BR-FranciscaNeural", "output")

CLI:
    python scripts/generate_voice.py --text "texto..." --voice pt-BR-FranciscaNeural
"""

from __future__ import annotations

import argparse
import logging
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.config_loader import load_config, ConfigError

logger = logging.getLogger("generate_voice")


# Mapeamento de vozes para garantir 100% Português do Brasil e compatibilidade
VOICE_ALIASES: dict[str, str] = {
    "pt-BR-NicolauNeural": "pt-BR-AntonioDoc",
    "pt-BR-FabioNeural": "pt-BR-AntonioDoc",
    "pt-BR-ThalitaNeural": "pt-BR-ThalitaMultilingualNeural",
    "pt-BR-BrendaNeural": "pt-BR-FranciscaNeural",
    "pt-PT-DuarteNeural": "pt-BR-AntonioDoc",
    "pt-PT-RaquelNeural": "pt-BR-FranciscaNeural",
}

DEFAULT_FALLBACK_VOICE = "pt-BR-AntonioNeural"


def _run_subreel_tts(text: str, voice: str, rate: str, pitch: str, mp3_path: Path, words_path: Path) -> subprocess.CompletedProcess:
    # Garante formatação com sinal (+ ou -) e unidade
    clean_rate = str(rate).strip()
    if not clean_rate.endswith("%"):
        clean_rate = f"{clean_rate}%"
    if not (clean_rate.startswith("+") or clean_rate.startswith("-")):
        clean_rate = f"+{clean_rate}"

    clean_pitch = str(pitch).strip()
    if not clean_pitch.endswith("Hz"):
        clean_pitch = f"{clean_pitch}Hz"
    if not (clean_pitch.startswith("+") or clean_pitch.startswith("-")):
        clean_pitch = f"+{clean_pitch}"

    # Usa --flag=valor para evitar que argparse trate taxas negativas como novos flags
    cmd = [
        "subreel", "tts",
        "--text-inline", text.strip(),
        f"--voice={voice}",
        f"--rate={clean_rate}",
        f"--pitch={clean_pitch}",
        "--out", str(mp3_path),
        "--timings", str(words_path),
    ]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )


def insert_breaths(text: str) -> str:
    """Insere respirações e pausas contemplativas naturais (...) no texto da narração para o TTS."""
    t = re.sub(r"\s+", " ", text).strip()
    # Adiciona pausas reflexivas (...) nos pontos finais e exclamações seguidos de nova oração
    t = re.sub(r"([.?!])\s+([A-ZÀ-Ú])", r"\1... \2", t)
    # Adiciona pausas respiratórias antes de conjunções reflexivas e de impacto
    t = re.sub(r"(\s+)(mas|porém|contudo|no entanto|todavia|ou seja|imagine|repare|observe)(\s+)", r" — \2\3", t, flags=re.IGNORECASE)
    # Substitui dois pontos por pausa reflexiva
    t = t.replace(":", "... ")
    # Normaliza pontuação
    t = re.sub(r"\.{4,}", "...", t)
    return t


def generate_voice(
    text: str,
    voice: str,
    out_dir: str,
    rate: str = "+0%",
    pitch: str = "+0Hz",
) -> Tuple[Path, Path]:
    """
    Gera voice.mp3 e voice.words.json usando `subreel tts`.
    Inclui inserção de pausas respiratórias, afinação de barítono maduro e fallback automático.

    Retorna (mp3_path, words_json_path).
    """
    if not text or not text.strip():
        raise ValueError("'text' não pode ser vazio")

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    mp3_path = out_path / "voice.mp3"
    words_path = out_path / "voice.words.json"

    # Perfil especial de documentarista maduro / homem mais velho ou voz personalizada
    target_pitch = pitch
    target_rate = rate
    if voice.startswith("custom_"):
        from scripts.voice_cloner import get_custom_voice
        prof = get_custom_voice(voice)
        if prof:
            target_voice = prof.get("base_model", "pt-BR-AntonioNeural")
            if pitch == "+0Hz" or not pitch:
                target_pitch = prof.get("calibrated_pitch", "-2Hz")
            if rate == "+0%" or not rate:
                target_rate = prof.get("calibrated_rate", "-10%")
            logger.info("Usando voz personalizada '%s' (%s) com base '%s' (pitch %s, rate %s)", prof.get("name"), voice, target_voice, target_pitch, target_rate)
        else:
            target_voice = "pt-BR-AntonioNeural"
    elif voice == "pt-BR-AntonioSenior":
        target_voice = "pt-BR-AntonioNeural"
        if pitch == "+0Hz" or not pitch:
            target_pitch = "-9Hz"
        if rate == "+0%" or not rate:
            target_rate = "-20%"
    elif voice == "pt-BR-AntonioDoc":
        target_voice = "pt-BR-AntonioNeural"
        if pitch == "+0Hz" or not pitch:
            target_pitch = "-5Hz"
        if rate == "+0%" or not rate:
            target_rate = "-20%"
    else:
        target_voice = VOICE_ALIASES.get(voice, voice)
        if target_voice != voice:
            logger.info("Voz '%s' foi descontinuada pela Microsoft; mapeada para '%s'", voice, target_voice)

    # Formata texto com pausas respiratórias naturais
    spoken_text = insert_breaths(text)

    # Retry resiliente com backoff exponencial para lidar com timeouts e oscilações do WebSocket da Microsoft
    max_attempts = 4
    last_result = None

    for attempt in range(1, max_attempts + 1):
        logger.info(
            "Executando subreel tts com voz '%s' (pitch: %s, rate: %s, tentativa %d/%d)...",
            target_voice, target_pitch, target_rate, attempt, max_attempts
        )
        result = _run_subreel_tts(spoken_text, target_voice, target_rate, target_pitch, mp3_path, words_path)
        last_result = result

        # Sucesso: arquivos gerados e com tamanho válido
        if (
            result.returncode == 0
            and mp3_path.exists()
            and mp3_path.stat().st_size > 500
            and words_path.exists()
            and words_path.stat().st_size > 10
        ):
            break

        err_output = f"{result.stderr or ''}\n{result.stdout or ''}"
        is_conn_error = any(
            err in err_output
            for err in (
                "ConnectionTimeoutError",
                "ClientConnectorError",
                "ServerDisconnectedError",
                "timeout",
                "timed out",
                "Connection reset",
                "Cannot connect to host",
            )
        )

        # Se for erro transitório de conexão e ainda tiver tentativas, espera e tenta novamente
        if is_conn_error and attempt < max_attempts:
            wait_sec = 2.0 * attempt
            logger.warning(
                "Falha transitória de conexão com speech.platform.bing.com na tentativa %d (%s). Aguardando %.1fs para retentar...",
                attempt, err_output.strip().splitlines()[-1] if err_output.strip() else "Timeout", wait_sec
            )
            # Remove arquivos parciais corrompidos
            if mp3_path.exists():
                try: mp3_path.unlink()
                except Exception: pass
            if words_path.exists():
                try: words_path.unlink()
                except Exception: pass
            time.sleep(wait_sec)
            continue

        # Se falhou por voz descontinuada ou NoAudioReceived, tenta fallback
        if "NoAudioReceived" in err_output or "retired" in err_output or (attempt == max_attempts and target_voice != DEFAULT_FALLBACK_VOICE):
            fallback_voice = "pt-BR-FranciscaNeural" if "Femin" in target_voice else "pt-BR-AntonioNeural"
            logger.warning(
                "subreel tts falhou com a voz '%s'. Tentando voz de contingência '%s'...",
                target_voice, fallback_voice
            )
            result = _run_subreel_tts(spoken_text, fallback_voice, target_rate, target_pitch, mp3_path, words_path)
            last_result = result
            if (
                result.returncode == 0
                and mp3_path.exists()
                and mp3_path.stat().st_size > 500
                and words_path.exists()
            ):
                break

        # Se for a penúltima tentativa, tenta síntese direta em Python via subreel.tts.synthesize
        if attempt == max_attempts - 1 and (not mp3_path.exists() or mp3_path.stat().st_size == 0):
            try:
                logger.info("Tentando síntese direta via subreel.tts.synthesize...")
                from subreel.tts import synthesize
                clean_rate = str(target_rate).strip()
                if not clean_rate.endswith("%"): clean_rate = f"{clean_rate}%"
                if not (clean_rate.startswith("+") or clean_rate.startswith("-")): clean_rate = f"+{clean_rate}"
                clean_pitch = str(target_pitch).strip()
                if not clean_pitch.endswith("Hz"): clean_pitch = f"{clean_pitch}Hz"
                if not (clean_pitch.startswith("+") or clean_pitch.startswith("-")): clean_pitch = f"+{clean_pitch}"
                synthesize(
                    spoken_text,
                    voice=target_voice,
                    out=str(mp3_path),
                    rate=clean_rate,
                    pitch=clean_pitch,
                    timings=str(words_path),
                )
                if mp3_path.exists() and mp3_path.stat().st_size > 500 and words_path.exists():
                    break
            except Exception as exc:
                logger.warning("Síntese direta via subreel.tts falhou: %s", exc)

    if not mp3_path.exists() or mp3_path.stat().st_size == 0:
        err_detail = f"\nstdout: {last_result.stdout}\nstderr: {last_result.stderr}" if last_result else ""
        raise RuntimeError(
            f"subreel tts falhou após {max_attempts} tentativas:{err_detail}\n"
            f"Dica: Verifique a conexão com a internet ou tente novamente em instantes."
        )

    if not words_path.exists() or words_path.stat().st_size == 0:
        raise RuntimeError(f"words.json não gerado ou vazio: {words_path}")

    logger.info("MP3 gerado com sucesso: %s (%d bytes)", mp3_path, mp3_path.stat().st_size)
    logger.info("Words gerado com sucesso: %s (%d bytes)", words_path, words_path.stat().st_size)

    return mp3_path, words_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera voice.mp3 + voice.words.json via subreel.")
    parser.add_argument("--text", "-t", default=None, help="Texto a narrar")
    parser.add_argument("--input", "-i", default=None, help="Arquivo de texto (utf-8-sig)")
    parser.add_argument("--voice", "-v", default=None, help="Voz (padrão: cfg.tts.voice)")
    parser.add_argument("--out-dir", "-o", default="output", help="Diretório de saída")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    if args.input:
        text = Path(args.input).read_text(encoding="utf-8-sig").strip()
    elif args.text:
        text = args.text
    else:
        logger.error("Forneça --text ou --input")
        return 1

    if args.voice:
        voice = args.voice
    else:
        try:
            cfg = load_config()
            voice = cfg.tts.voice
        except ConfigError as exc:
            logger.error("Config inválida: %s", exc)
            return 1

    try:
        mp3, words = generate_voice(text, voice, args.out_dir)
    except Exception as exc:
        logger.error("Falha: %s", exc)
        return 1

    print(f"[OK] MP3: {mp3}")
    print(f"[OK] Words: {words}")
    return 0


if __name__ == "__main__":
    sys.exit(main())