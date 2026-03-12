"""Utilitários para carregamento de prompts versionados em arquivo."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path


PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"


@lru_cache(maxsize=64)
def load_prompt(prompt_filename: str) -> str:
    """Carrega o conteúdo de um prompt da pasta `prompts/`."""

    prompt_path = PROMPTS_DIR / prompt_filename
    return prompt_path.read_text(encoding="utf-8")
