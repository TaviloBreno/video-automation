#!/usr/bin/env python3
"""
llm_client.py — Cliente LLM com suporte a Ollama local e fallback para Groq.

Uso:
    from scripts.llm_client import parse_scene
    scene = parse_scene("cena de lançamento de produto, fundo escuro, texto aparecendo gradualmente")
    print(scene["narration_text"])
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict

import requests
from dotenv import load_dotenv

# Garante que a raiz do projeto esteja no sys.path para importar config_loader
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.config_loader import load_config, AppConfig
from scripts.research_web import format_research_context

ALLOWED_TYPES = {"title", "subtitle", "body", "image", "shape"}
ALLOWED_POSITIONS = {"top", "center", "bottom"}
ALLOWED_ANIMATIONS = {"fade", "slide-up", "slide-left", "zoom", "none"}
TEXT_TYPES = {"title", "subtitle", "body"}

load_dotenv(PROJECT_ROOT / ".env")

OLLAMA_ENABLED = os.getenv("OLLAMA_ENABLED", "true").lower() == "true"
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

MAX_RETRIES = 4
RETRY_DELAY_SECONDS = 2


# ---------------------------------------------------------------------------
# Carregamento do prompt
# ---------------------------------------------------------------------------

def _load_prompt_template(cfg: AppConfig) -> str:
    """Lê prompts/scene_parser.txt e retorna o conteúdo."""
    prompt_path = PROJECT_ROOT / cfg.paths.prompts_dir / "scene_parser.txt"
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt não encontrado: {prompt_path}")
    return prompt_path.read_text(encoding="utf-8")


def _build_messages(
    template: str,
    description: str,
    research_sources: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    """Substitui {description} e monta a lista de mensagens no formato chat."""
    system_content = template.replace("{description}", description)
    if research_sources is not None:
        system_content += format_research_context({"sources": research_sources})
    return [
        {"role": "user", "content": system_content},
    ]


# ---------------------------------------------------------------------------
# Validação mínima do JSON de saída
# ---------------------------------------------------------------------------

def _validate_scene(
    scene: Any,
    known_palettes: set[str] | None = None,
    known_source_ids: set[str] | None = None,
) -> Dict[str, Any]:
    """Valida o schema mínimo e a consistência do JSON retornado."""
    if not isinstance(scene, dict):
        raise ValueError(f"Esperado dict, recebido {type(scene).__name__}")

    required = {"elements", "palette", "suggested_duration_hint", "narration_text"}
    missing = required - scene.keys()
    if missing:
        raise ValueError(f"Campos ausentes: {sorted(missing)}")

    if not isinstance(scene["elements"], list) or len(scene["elements"]) == 0:
        raise ValueError("'elements' deve ser uma lista com pelo menos 1 item")

    if not isinstance(scene["narration_text"], str) or not scene["narration_text"].strip():
        raise ValueError("'narration_text' deve ser string não vazia")

    if not isinstance(scene["suggested_duration_hint"], (int, float)):
        raise ValueError("'suggested_duration_hint' deve ser número")

    if not isinstance(scene["palette"], str) or not scene["palette"].strip():
        raise ValueError("'palette' deve ser string não vazia")

    if known_palettes is not None and scene["palette"] not in known_palettes:
        raise ValueError(
            f"'palette' inválida: {scene['palette']!r}. "
            f"Disponíveis: {sorted(known_palettes)}"
        )

    has_title = False
    for idx, el in enumerate(scene["elements"]):
        if not isinstance(el, dict):
            raise ValueError(f"elements[{idx}] deve ser objeto")

        el_type = el.get("type")
        if el_type not in ALLOWED_TYPES:
            raise ValueError(
                f"elements[{idx}].type inválido: {el_type!r}. "
                f"Permitidos: {sorted(ALLOWED_TYPES)}"
            )
        if el_type == "title":
            has_title = True

        # Todo elemento precisa de duration_seconds > 0
        dur = el.get("duration_seconds")
        if not isinstance(dur, (int, float)) or dur <= 0:
            raise ValueError(f"elements[{idx}].duration_seconds inválido: {dur!r}")

        # Elementos de texto precisam de content não vazio
        if el_type in TEXT_TYPES:
            content = el.get("content")
            if not isinstance(content, str) or not content.strip():
                raise ValueError(f"elements[{idx}].content vazio para tipo '{el_type}'")

        # Campos opcionais, mas se presentes precisam ser válidos
        if "position" in el and el["position"] not in ALLOWED_POSITIONS:
            raise ValueError(
                f"elements[{idx}].position inválida: {el['position']!r}. "
                f"Permitidos: {sorted(ALLOWED_POSITIONS)}"
            )
        if "animation" in el and el["animation"] not in ALLOWED_ANIMATIONS:
            raise ValueError(
                f"elements[{idx}].animation inválida: {el['animation']!r}. "
                f"Permitidos: {sorted(ALLOWED_ANIMATIONS)}"
            )
        source_ids = el.get("source_ids", [])
        if not isinstance(source_ids, list) or any(
            not isinstance(source_id, str) for source_id in source_ids
        ):
            raise ValueError(f"elements[{idx}].source_ids deve ser uma lista de IDs de fonte")
        if len(source_ids) != len(set(source_ids)):
            raise ValueError(f"elements[{idx}].source_ids contém IDs duplicados")
        if known_source_ids is not None:
            unknown_ids = set(source_ids) - known_source_ids
            if unknown_ids:
                raise ValueError(
                    f"elements[{idx}] cita fontes desconhecidas: {sorted(unknown_ids)}"
                )
            if el_type in {"body", "subtitle"} and not source_ids:
                raise ValueError(
                    f"elements[{idx}] é uma afirmação textual e precisa de source_ids"
                )

    if not has_title:
        raise ValueError("'elements' deve conter pelo menos 1 elemento do tipo 'title'")

    return scene

def _parse_json_response(raw: str) -> Dict[str, Any]:
    """Extrai JSON de uma resposta de texto (tolerante a markdown fences)."""
    text = raw.strip()
    # Remove cercas de markdown se existirem
    if text.startswith("```"):
        lines = text.splitlines()
        # Remove primeira e última linha se forem fences
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return json.loads(text)


# ---------------------------------------------------------------------------
# Backend Ollama
# ---------------------------------------------------------------------------

def _call_ollama(messages: list[dict], cfg: AppConfig) -> str:
    """Chama Ollama /api/chat com format=json. Retorna o conteúdo bruto da resposta."""
    url = f"{cfg.llm.base_url.rstrip('/')}/api/chat"
    payload = {
        "model": cfg.llm.model,
        "messages": messages,
        "stream": False,
        "format": "json",  # força saída JSON [citation:1][citation:6]
        "options": {
            "temperature": cfg.llm.temperature,
            "num_predict": cfg.llm.max_tokens,
        },
    }
    response = requests.post(url, json=payload, timeout=cfg.llm.timeout_seconds)
    response.raise_for_status()
    data = response.json()
    return data["message"]["content"]


# ---------------------------------------------------------------------------
# Backend Groq (fallback)
# ---------------------------------------------------------------------------

def _call_groq(messages: list[dict], cfg: AppConfig) -> str:
    """Chama Groq como fallback. Requer GROQ_API_KEY."""
    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY não configurada. Defina no .env ou desative o fallback."
        )
    try:
        from groq import Groq
    except ImportError as exc:
        raise RuntimeError("Pacote 'groq' não instalado. Rode: pip install groq") from exc

    client = Groq(api_key=GROQ_API_KEY)
    completion = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=cfg.llm.temperature,
        max_tokens=cfg.llm.max_tokens,
        response_format={"type": "json_object"},  # JSON mode do Groq
    )
    return completion.choices[0].message.content


# ---------------------------------------------------------------------------
# Função pública
# ---------------------------------------------------------------------------

def parse_scene(
    description: str,
    cfg: AppConfig | None = None,
    research_sources: list[dict[str, str]] | None = None,
) -> Dict[str, Any]:
    """
    Converte uma descrição em linguagem natural para um dict JSON estruturado.

    - Usa Ollama local se OLLAMA_ENABLED=true.
    - Faz fallback para Groq se OLLAMA_ENABLED=false.
    - Retry 2x em timeouts, erros de conexão, JSON inválido e cena fora do schema.
    - Valida o schema mínimo antes de retornar.

    Lança RuntimeError se todas as tentativas falharem.
    """
    if not description or not description.strip():
        raise ValueError("'description' não pode ser vazia")

    cfg = cfg or load_config()
    template = _load_prompt_template(cfg)
    messages = _build_messages(template, description.strip(), research_sources)
    known_source_ids = (
        {source["id"] for source in research_sources}
        if research_sources is not None
        else None
    )

    last_error: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            if OLLAMA_ENABLED:
                raw = _call_ollama(messages, cfg)
            else:
                raw = _call_groq(messages, cfg)

            scene = _parse_json_response(raw)
            return _validate_scene(
                scene,
                known_palettes=set(cfg.palettes.keys()),
                known_source_ids=known_source_ids,
            )

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
            last_error = exc
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS * attempt)
                continue
            break
        except json.JSONDecodeError as exc:
            last_error = exc
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS * attempt)
                continue
            break
        except ValueError as exc:
            last_error = exc
            if attempt < MAX_RETRIES:
                messages = [
                    *messages[:-1],
                    {
                        **messages[-1],
                        "content": (
                            messages[-1]["content"]
                            + "\n\nA resposta anterior falhou na validação: "
                            + str(exc)
                            + ". Corrija o JSON e inclua obrigatoriamente pelo menos "
                            "um elemento do tipo title. Quando a pesquisa estiver ativa, "
                            "inclua source_ids existentes em cada afirmação factual "
                            "de body/subtitle; use apenas fontes que sustentem o texto."
                        ),
                    },
                ]
                time.sleep(RETRY_DELAY_SECONDS * attempt)
                continue
            break
        except Exception as exc:
            # Erros não recuperáveis (ex.: prompt ausente, API key) sobem direto
            raise RuntimeError(f"Falha ao parsear cena: {exc}") from exc

    raise RuntimeError(
        f"parse_scene falhou após {MAX_RETRIES} tentativas. Último erro: {last_error}"
    )


# ---------------------------------------------------------------------------
# CLI para teste rápido
# ---------------------------------------------------------------------------

def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Testa parse_scene com uma descrição.")
    parser.add_argument(
        "description",
        nargs="?",
        default="cena de lançamento de produto, fundo escuro, texto aparecendo gradualmente",
        help="Descrição da cena",
    )
    args = parser.parse_args()

    print(f"Descrição: {args.description}\n")
    try:
        scene = parse_scene(args.description)
    except Exception as exc:
        print(f"❌ Erro: {exc}")
        return 1

    print("✅ JSON válido retornado:")
    print(json.dumps(scene, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())